"""
Insights Router - handles AI-generated insights for change management projects.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
import json

from ..database import get_connection, dict_from_row
from ..agents.insights import InsightsAgent

router = APIRouter(prefix="/api", tags=["insights"])

# Initialize insights agent
insights_agent = InsightsAgent()


# --- Enums ---

class InsightType(str, Enum):
    trend = "trend"
    opportunity = "opportunity"
    warning = "warning"
    success = "success"
    pattern = "pattern"


class InsightPriority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class TriggerType(str, Enum):
    manual = "manual"
    impulse_completed = "impulse_completed"
    recommendation_completed = "recommendation_completed"


# --- Pydantic Models ---

class InsightModel(BaseModel):
    id: str
    project_id: str
    title: str
    content: str
    insight_type: InsightType
    priority: InsightPriority
    trigger_type: TriggerType
    trigger_entity_id: Optional[str]
    related_groups: List[str]
    related_recommendations: List[str]
    action_suggestions: List[str]
    is_dismissed: bool
    created_at: str


class GenerateInsightRequest(BaseModel):
    focus: Optional[str] = None


class GeneratedInsightResponse(BaseModel):
    insight: dict  # Contains title, content, insight_type, priority, etc.


# --- Helper Functions ---

def row_to_insight(row) -> InsightModel:
    """Convert a database row to an InsightModel."""
    data = dict_from_row(row)
    # Parse JSON fields
    related_groups = json.loads(data.get("related_groups") or "[]")
    related_recommendations = json.loads(data.get("related_recommendations") or "[]")
    action_suggestions = json.loads(data.get("action_suggestions") or "[]")

    return InsightModel(
        id=data["id"],
        project_id=data["project_id"],
        title=data["title"],
        content=data["content"],
        insight_type=data["insight_type"],
        priority=data["priority"],
        trigger_type=data["trigger_type"],
        trigger_entity_id=data.get("trigger_entity_id"),
        related_groups=related_groups,
        related_recommendations=related_recommendations,
        action_suggestions=action_suggestions,
        is_dismissed=bool(data.get("is_dismissed", False)),
        created_at=data["created_at"]
    )


async def save_generated_insight(
    project_id: str,
    generated_insight,
    trigger_type: str,
    trigger_entity_id: Optional[str] = None
) -> InsightModel:
    """Save a generated insight to the database."""
    with get_connection() as conn:
        cursor = conn.cursor()

        insight_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO insights (
                id, project_id, title, content, insight_type,
                priority, trigger_type, trigger_entity_id,
                related_groups, related_recommendations, action_suggestions,
                is_dismissed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                insight_id,
                project_id,
                generated_insight.title,
                generated_insight.content,
                generated_insight.insight_type,
                generated_insight.priority,
                trigger_type,
                trigger_entity_id,
                json.dumps(generated_insight.related_groups),
                json.dumps(generated_insight.related_recommendations),
                json.dumps(generated_insight.action_suggestions),
                False,
                now
            )
        )

        cursor.execute("SELECT * FROM insights WHERE id = ?", (insight_id,))
        return row_to_insight(cursor.fetchone())


# --- Endpoints ---

@router.get("/projects/{project_id}/insights", response_model=List[InsightModel])
async def list_insights(project_id: str, include_dismissed: bool = False):
    """List all insights for a project, optionally including dismissed ones."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        if include_dismissed:
            cursor.execute(
                """
                SELECT * FROM insights
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM insights
                WHERE project_id = ?
                AND is_dismissed = FALSE
                ORDER BY created_at DESC
                """,
                (project_id,)
            )

        rows = cursor.fetchall()
        return [row_to_insight(row) for row in rows]


@router.post("/projects/{project_id}/insights/generate", response_model=GeneratedInsightResponse)
async def generate_insight(project_id: str, request: GenerateInsightRequest):
    """Generate an insight using AI based on project context."""
    # Verify project exists
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Generate insight using the agent
        generated = await insights_agent.generate_insight(
            project_id=project_id,
            trigger_type="manual",
            trigger_context={"focus": request.focus} if request.focus else None
        )

        # Save the insight to the database
        saved_insight = await save_generated_insight(
            project_id=project_id,
            generated_insight=generated,
            trigger_type="manual"
        )

        return GeneratedInsightResponse(
            insight={
                "id": saved_insight.id,
                "title": generated.title,
                "content": generated.content,
                "insight_type": generated.insight_type,
                "priority": generated.priority,
                "related_groups": generated.related_groups,
                "related_recommendations": generated.related_recommendations,
                "action_suggestions": generated.action_suggestions,
                "created_at": saved_insight.created_at
            }
        )
    except Exception as e:
        print(f"Error generating insight: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate insight: {str(e)}")


@router.get("/insights/{insight_id}", response_model=InsightModel)
async def get_insight(insight_id: str):
    """Get a single insight by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM insights WHERE id = ?", (insight_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Insight not found")

        return row_to_insight(row)


@router.patch("/insights/{insight_id}/dismiss", response_model=InsightModel)
async def dismiss_insight(insight_id: str):
    """Dismiss an insight (mark as acknowledged)."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM insights WHERE id = ?", (insight_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Insight not found")

        cursor.execute("UPDATE insights SET is_dismissed = TRUE WHERE id = ?", (insight_id,))

        cursor.execute("SELECT * FROM insights WHERE id = ?", (insight_id,))
        return row_to_insight(cursor.fetchone())


@router.delete("/insights/{insight_id}")
async def delete_insight(insight_id: str):
    """Delete an insight."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM insights WHERE id = ?", (insight_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Insight not found")

        cursor.execute("DELETE FROM insights WHERE id = ?", (insight_id,))

        return {"message": "Insight deleted"}


# --- Helper function for automatic triggers (used by other routers) ---

async def generate_and_save_insight(
    project_id: str,
    trigger_type: str,
    trigger_context: Optional[dict] = None,
    trigger_entity_id: Optional[str] = None
) -> Optional[InsightModel]:
    """
    Generate and save an insight. Called from other routers as a background task.
    Returns the saved insight or None if generation fails.
    """
    try:
        generated = await insights_agent.generate_insight(
            project_id=project_id,
            trigger_type=trigger_type,
            trigger_context=trigger_context
        )

        saved_insight = await save_generated_insight(
            project_id=project_id,
            generated_insight=generated,
            trigger_type=trigger_type,
            trigger_entity_id=trigger_entity_id
        )

        return saved_insight
    except Exception as e:
        print(f"Error generating insight (trigger={trigger_type}): {e}")
        return None
