"""
MCP Tools for Insight operations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_connection, dict_from_row


VALID_TYPES = ("trend", "opportunity", "warning", "success", "pattern")
VALID_PRIORITIES = ("high", "medium", "low")
VALID_TRIGGERS = ("manual", "impulse_completed", "recommendation_completed")


async def insight_list(project_id: str, include_dismissed: bool = False) -> str:
    """List all insights for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        if include_dismissed:
            cursor.execute("""
                SELECT * FROM insights
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))
        else:
            cursor.execute("""
                SELECT * FROM insights
                WHERE project_id = ?
                AND is_dismissed = FALSE
                ORDER BY created_at DESC
            """, (project_id,))

        insights = []
        for row in cursor.fetchall():
            insight = dict_from_row(row)
            # Parse JSON fields
            insight["related_groups"] = json.loads(insight.get("related_groups") or "[]")
            insight["related_recommendations"] = json.loads(insight.get("related_recommendations") or "[]")
            insight["action_suggestions"] = json.loads(insight.get("action_suggestions") or "[]")
            # Convert boolean
            insight["is_dismissed"] = bool(insight.get("is_dismissed", False))
            insights.append(insight)

        return json.dumps(insights)


async def insight_get(insight_id: str) -> str:
    """Get a single insight by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM insights WHERE id = ?", (insight_id,))
        row = cursor.fetchone()

        if not row:
            return json.dumps({"error": "Insight not found", "insight_id": insight_id})

        insight = dict_from_row(row)
        # Parse JSON fields
        insight["related_groups"] = json.loads(insight.get("related_groups") or "[]")
        insight["related_recommendations"] = json.loads(insight.get("related_recommendations") or "[]")
        insight["action_suggestions"] = json.loads(insight.get("action_suggestions") or "[]")
        # Convert boolean
        insight["is_dismissed"] = bool(insight.get("is_dismissed", False))

        return json.dumps(insight)


async def insight_create(
    project_id: str,
    title: str,
    content: str,
    insight_type: str,
    priority: str,
    trigger_type: str,
    related_groups_json: str,
    related_recommendations_json: str,
    action_suggestions_json: str,
    trigger_entity_id: Optional[str] = None
) -> str:
    """Create a new insight."""
    # Validate type
    if insight_type not in VALID_TYPES:
        return json.dumps({
            "error": f"Invalid insight_type. Valid types: {VALID_TYPES}"
        })

    # Validate priority
    if priority not in VALID_PRIORITIES:
        return json.dumps({
            "error": f"Invalid priority. Valid priorities: {VALID_PRIORITIES}"
        })

    # Validate trigger type
    if trigger_type not in VALID_TRIGGERS:
        return json.dumps({
            "error": f"Invalid trigger_type. Valid triggers: {VALID_TRIGGERS}"
        })

    # Parse JSON arrays
    try:
        related_groups = json.loads(related_groups_json)
        related_recommendations = json.loads(related_recommendations_json)
        action_suggestions = json.loads(action_suggestions_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {str(e)}"})

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Project not found", "project_id": project_id})

        insight_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO insights (
                id, project_id, title, content, insight_type,
                priority, trigger_type, trigger_entity_id,
                related_groups, related_recommendations, action_suggestions,
                is_dismissed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            insight_id,
            project_id,
            title,
            content,
            insight_type,
            priority,
            trigger_type,
            trigger_entity_id,
            json.dumps(related_groups),
            json.dumps(related_recommendations),
            json.dumps(action_suggestions),
            False,
            now
        ))

        cursor.execute("SELECT * FROM insights WHERE id = ?", (insight_id,))
        insight = dict_from_row(cursor.fetchone())
        insight["related_groups"] = related_groups
        insight["related_recommendations"] = related_recommendations
        insight["action_suggestions"] = action_suggestions
        insight["is_dismissed"] = False

        return json.dumps(insight)


async def insight_dismiss(insight_id: str) -> str:
    """Dismiss an insight (mark as acknowledged)."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM insights WHERE id = ?", (insight_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Insight not found", "insight_id": insight_id})

        cursor.execute("UPDATE insights SET is_dismissed = TRUE WHERE id = ?", (insight_id,))

        cursor.execute("SELECT * FROM insights WHERE id = ?", (insight_id,))
        insight = dict_from_row(cursor.fetchone())
        insight["related_groups"] = json.loads(insight.get("related_groups") or "[]")
        insight["related_recommendations"] = json.loads(insight.get("related_recommendations") or "[]")
        insight["action_suggestions"] = json.loads(insight.get("action_suggestions") or "[]")
        insight["is_dismissed"] = True

        return json.dumps(insight)


async def insight_delete(insight_id: str) -> str:
    """Delete an insight."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM insights WHERE id = ?", (insight_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Insight not found", "insight_id": insight_id})

        cursor.execute("DELETE FROM insights WHERE id = ?", (insight_id,))

        return json.dumps({"success": True, "message": "Insight deleted", "insight_id": insight_id})


# Tool definitions for the MCP server
TOOLS = {
    "insight_list": {
        "description": "List all insights for a project, optionally including dismissed ones.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to get insights for"
                },
                "include_dismissed": {
                    "type": "boolean",
                    "description": "Whether to include dismissed insights (default: false)"
                }
            },
            "required": ["project_id"]
        },
        "handler": insight_list
    },
    "insight_get": {
        "description": "Get a single insight by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_id": {
                    "type": "string",
                    "description": "The unique identifier of the insight"
                }
            },
            "required": ["insight_id"]
        },
        "handler": insight_get
    },
    "insight_create": {
        "description": "Create a new insight.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to create the insight for"
                },
                "title": {
                    "type": "string",
                    "description": "Title of the insight"
                },
                "content": {
                    "type": "string",
                    "description": "Detailed content/explanation of the insight"
                },
                "insight_type": {
                    "type": "string",
                    "description": "Type: trend, opportunity, warning, success, or pattern"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level: high, medium, or low"
                },
                "trigger_type": {
                    "type": "string",
                    "description": "How the insight was triggered: manual, impulse_completed, or recommendation_completed"
                },
                "related_groups_json": {
                    "type": "string",
                    "description": "JSON array of related stakeholder group IDs"
                },
                "related_recommendations_json": {
                    "type": "string",
                    "description": "JSON array of related recommendation IDs"
                },
                "action_suggestions_json": {
                    "type": "string",
                    "description": "JSON array of suggested actions"
                },
                "trigger_entity_id": {
                    "type": "string",
                    "description": "Optional ID of the entity that triggered the insight (group_id or recommendation_id)"
                }
            },
            "required": [
                "project_id", "title", "content", "insight_type", "priority",
                "trigger_type", "related_groups_json", "related_recommendations_json", "action_suggestions_json"
            ]
        },
        "handler": insight_create
    },
    "insight_dismiss": {
        "description": "Dismiss an insight (mark as acknowledged).",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_id": {
                    "type": "string",
                    "description": "The unique identifier of the insight"
                }
            },
            "required": ["insight_id"]
        },
        "handler": insight_dismiss
    },
    "insight_delete": {
        "description": "Delete an insight.",
        "input_schema": {
            "type": "object",
            "properties": {
                "insight_id": {
                    "type": "string",
                    "description": "The unique identifier of the insight"
                }
            },
            "required": ["insight_id"]
        },
        "handler": insight_delete
    }
}
