"""
Recommendations Router - handles AI-generated action recommendations.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
import json

from ..database import get_connection, dict_from_row
from ..agents.recommendations import RecommendationAgent

router = APIRouter(prefix="/api", tags=["recommendations"])

# Initialize recommendation agent
recommendation_agent = RecommendationAgent()


# --- Enums ---

class RecommendationType(str, Enum):
    habit = "habit"
    communication = "communication"
    workshop = "workshop"
    process = "process"
    campaign = "campaign"


class RecommendationPriority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class RecommendationStatus(str, Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    started = "started"
    completed = "completed"


# --- Pydantic Models ---

class RecommendationModel(BaseModel):
    id: str
    project_id: str
    title: str
    description: Optional[str]
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    status: RecommendationStatus
    affected_groups: List[str]
    steps: List[str]
    rejection_reason: Optional[str]
    parent_id: Optional[str]
    created_at: str
    approved_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]


class CreateRecommendationRequest(BaseModel):
    title: str
    description: Optional[str] = None
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    affected_groups: List[str]
    steps: List[str]


class UpdateRecommendationRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    recommendation_type: Optional[RecommendationType] = None
    priority: Optional[RecommendationPriority] = None
    status: Optional[RecommendationStatus] = None
    affected_groups: Optional[List[str]] = None
    steps: Optional[List[str]] = None
    rejection_reason: Optional[str] = None


class GenerateRecommendationRequest(BaseModel):
    focus: Optional[str] = None


class GeneratedRecommendationResponse(BaseModel):
    recommendation: dict  # Contains title, description, type, priority, affected_groups, steps


class RegenerateRequest(BaseModel):
    additional_context: Optional[str] = None


# --- Helper Functions ---

def row_to_recommendation(row) -> RecommendationModel:
    """Convert a database row to a RecommendationModel."""
    data = dict_from_row(row)
    # Parse JSON fields
    affected_groups = json.loads(data.get("affected_groups") or "[]")
    steps = json.loads(data.get("steps") or "[]")

    return RecommendationModel(
        id=data["id"],
        project_id=data["project_id"],
        title=data["title"],
        description=data.get("description"),
        recommendation_type=data["recommendation_type"],
        priority=data["priority"],
        status=data["status"],
        affected_groups=affected_groups,
        steps=steps,
        rejection_reason=data.get("rejection_reason"),
        parent_id=data.get("parent_id"),
        created_at=data["created_at"],
        approved_at=data.get("approved_at"),
        started_at=data.get("started_at"),
        completed_at=data.get("completed_at")
    )


def get_project_context(cursor, project_id: str) -> dict:
    """Get project context for AI generation."""
    # Get project info
    cursor.execute("SELECT id, name, goal FROM projects WHERE id = ?", (project_id,))
    project_row = cursor.fetchone()
    if not project_row:
        raise HTTPException(status_code=404, detail="Project not found")

    project = dict_from_row(project_row)

    # Get stakeholder groups
    cursor.execute(
        """
        SELECT id, name, group_type, power_level, interest_level
        FROM stakeholder_groups
        WHERE project_id = ?
        """,
        (project_id,)
    )
    groups = [dict_from_row(r) for r in cursor.fetchall()]

    # Get impulse summaries for each group
    impulse_summaries = []
    for group in groups:
        cursor.execute(
            """
            SELECT indicator_key, rating, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
            LIMIT 50
            """,
            (group["id"],)
        )
        assessments = [dict_from_row(r) for r in cursor.fetchall()]

        if assessments:
            # Calculate average and find weak areas
            ratings = [a["rating"] for a in assessments if a["rating"] is not None]
            avg = sum(ratings) / len(ratings) if ratings else None

            # Group by indicator to find weak ones
            indicator_ratings = {}
            for a in assessments:
                key = a["indicator_key"]
                if key not in indicator_ratings:
                    indicator_ratings[key] = []
                if a["rating"] is not None:
                    indicator_ratings[key].append(a["rating"])

            weak_indicators = []
            for key, vals in indicator_ratings.items():
                ind_avg = sum(vals) / len(vals)
                if ind_avg < 6:
                    weak_indicators.append({
                        "name": key,
                        "rating": round(ind_avg, 1)
                    })

            # Sort by rating (lowest first)
            weak_indicators.sort(key=lambda x: x["rating"])

            impulse_summaries.append({
                "group_id": group["id"],
                "group_name": group.get("name") or group["group_type"],
                "average_rating": round(avg, 1) if avg else None,
                "weak_indicators": weak_indicators[:3]  # Top 3 weak areas
            })

    return {
        "project_goal": project.get("goal"),
        "project_description": None,
        "stakeholder_groups": [
            {
                "id": g["id"],
                "name": g.get("name") or g["group_type"],
                "type": g["group_type"],
                "power_level": g["power_level"],
                "interest_level": g["interest_level"]
            }
            for g in groups
        ],
        "impulse_summaries": impulse_summaries
    }


# --- Endpoints ---

@router.get("/projects/{project_id}/recommendations", response_model=List[RecommendationModel])
async def list_recommendations(project_id: str, status: Optional[str] = None):
    """List all recommendations for a project, optionally filtered by status."""
    with get_connection() as conn:
        cursor = conn.cursor()

        if status:
            cursor.execute(
                """
                SELECT * FROM recommendations
                WHERE project_id = ?
                AND status = ?
                ORDER BY created_at DESC
                """,
                (project_id, status)
            )
        else:
            cursor.execute(
                """
                SELECT * FROM recommendations
                WHERE project_id = ?
                ORDER BY created_at DESC
                """,
                (project_id,)
            )

        rows = cursor.fetchall()
        return [row_to_recommendation(row) for row in rows]


@router.post("/projects/{project_id}/recommendations", response_model=RecommendationModel)
async def create_recommendation(project_id: str, request: CreateRecommendationRequest):
    """Create a new recommendation (after user edits AI-generated or manual creation)."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        rec_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO recommendations (
                id, project_id, title, description, recommendation_type,
                priority, status, affected_groups, steps, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rec_id,
                project_id,
                request.title,
                request.description,
                request.recommendation_type.value,
                request.priority.value,
                RecommendationStatus.pending_approval.value,
                json.dumps(request.affected_groups),
                json.dumps(request.steps),
                now
            )
        )

        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (rec_id,))
        return row_to_recommendation(cursor.fetchone())


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationModel)
async def get_recommendation(recommendation_id: str):
    """Get a single recommendation by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        return row_to_recommendation(row)


@router.patch("/recommendations/{recommendation_id}", response_model=RecommendationModel)
async def update_recommendation(recommendation_id: str, request: UpdateRecommendationRequest):
    """Update a recommendation (status, content, etc.)."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get current recommendation
        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        current = dict_from_row(row)
        now = datetime.utcnow().isoformat()

        # Build update fields
        updates = []
        values = []

        if request.title is not None:
            updates.append("title = ?")
            values.append(request.title)

        if request.description is not None:
            updates.append("description = ?")
            values.append(request.description)

        if request.recommendation_type is not None:
            updates.append("recommendation_type = ?")
            values.append(request.recommendation_type.value)

        if request.priority is not None:
            updates.append("priority = ?")
            values.append(request.priority.value)

        if request.affected_groups is not None:
            updates.append("affected_groups = ?")
            values.append(json.dumps(request.affected_groups))

        if request.steps is not None:
            updates.append("steps = ?")
            values.append(json.dumps(request.steps))

        if request.rejection_reason is not None:
            updates.append("rejection_reason = ?")
            values.append(request.rejection_reason)

        # Handle status changes with timestamp updates
        if request.status is not None:
            updates.append("status = ?")
            values.append(request.status.value)

            # Update relevant timestamp based on new status
            if request.status == RecommendationStatus.approved:
                updates.append("approved_at = ?")
                values.append(now)
            elif request.status == RecommendationStatus.started:
                updates.append("started_at = ?")
                values.append(now)
            elif request.status == RecommendationStatus.completed:
                updates.append("completed_at = ?")
                values.append(now)

        if not updates:
            # Nothing to update
            return row_to_recommendation(row)

        # Execute update
        values.append(recommendation_id)
        cursor.execute(
            f"UPDATE recommendations SET {', '.join(updates)} WHERE id = ?",
            values
        )

        # Return updated recommendation
        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        return row_to_recommendation(cursor.fetchone())


@router.delete("/recommendations/{recommendation_id}")
async def delete_recommendation(recommendation_id: str):
    """Delete a recommendation."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM recommendations WHERE id = ?", (recommendation_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Recommendation not found")

        cursor.execute("DELETE FROM recommendations WHERE id = ?", (recommendation_id,))

        return {"message": "Recommendation deleted"}


@router.post("/projects/{project_id}/recommendations/generate", response_model=GeneratedRecommendationResponse)
async def generate_recommendation(project_id: str, request: GenerateRecommendationRequest):
    """Generate a recommendation using AI based on project context."""
    # Verify project exists
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Generate recommendation using MCP tools for context
        generated = await recommendation_agent.generate_recommendation(
            project_id=project_id,
            focus=request.focus
        )

        return GeneratedRecommendationResponse(
            recommendation={
                "title": generated.title,
                "description": generated.description,
                "recommendation_type": generated.recommendation_type,
                "priority": generated.priority,
                "affected_groups": generated.affected_groups,
                "steps": generated.steps
            }
        )
    except Exception as e:
        print(f"Error generating recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")


@router.post("/recommendations/{recommendation_id}/regenerate", response_model=GeneratedRecommendationResponse)
async def regenerate_recommendation(recommendation_id: str, request: RegenerateRequest):
    """Generate an alternative recommendation based on a rejected one."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get the original recommendation
        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Recommendation not found")

        original = dict_from_row(row)
        project_id = original["project_id"]

        # Build rejection context
        rejection_context = original.get("rejection_reason") or ""
        if request.additional_context:
            rejection_context = f"{rejection_context}\n\nZusaetzlicher Kontext: {request.additional_context}"

    try:
        # Generate alternative recommendation using MCP tools for context
        generated = await recommendation_agent.generate_recommendation(
            project_id=project_id,
            rejection_context=rejection_context
        )

        return GeneratedRecommendationResponse(
            recommendation={
                "title": generated.title,
                "description": generated.description,
                "recommendation_type": generated.recommendation_type,
                "priority": generated.priority,
                "affected_groups": generated.affected_groups,
                "steps": generated.steps
            }
        )
    except Exception as e:
        print(f"Error regenerating recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate recommendation: {str(e)}")
