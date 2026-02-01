"""
MCP Tools for Recommendation operations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_connection, dict_from_row


VALID_TYPES = ("habit", "communication", "workshop", "process", "campaign")
VALID_PRIORITIES = ("high", "medium", "low")
VALID_STATUSES = ("pending_approval", "approved", "rejected", "started", "completed")


async def recommendation_list(project_id: str, status: Optional[str] = None) -> str:
    """List all recommendations for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        if status:
            if status not in VALID_STATUSES:
                return json.dumps({
                    "error": f"Invalid status. Valid statuses: {VALID_STATUSES}"
                })
            cursor.execute("""
                SELECT * FROM recommendations
                WHERE project_id = ?
                AND status = ?
                ORDER BY created_at DESC
            """, (project_id, status))
        else:
            cursor.execute("""
                SELECT * FROM recommendations
                WHERE project_id = ?
                ORDER BY created_at DESC
            """, (project_id,))

        recommendations = []
        for row in cursor.fetchall():
            rec = dict_from_row(row)
            # Parse JSON fields
            rec["affected_groups"] = json.loads(rec.get("affected_groups") or "[]")
            rec["steps"] = json.loads(rec.get("steps") or "[]")
            recommendations.append(rec)

        return json.dumps(recommendations)


async def recommendation_get(recommendation_id: str) -> str:
    """Get a single recommendation by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        row = cursor.fetchone()

        if not row:
            return json.dumps({"error": "Recommendation not found", "recommendation_id": recommendation_id})

        rec = dict_from_row(row)
        # Parse JSON fields
        rec["affected_groups"] = json.loads(rec.get("affected_groups") or "[]")
        rec["steps"] = json.loads(rec.get("steps") or "[]")

        return json.dumps(rec)


async def recommendation_create(
    project_id: str,
    title: str,
    recommendation_type: str,
    priority: str,
    affected_groups_json: str,
    steps_json: str,
    description: Optional[str] = None,
    parent_id: Optional[str] = None
) -> str:
    """Create a new recommendation."""
    # Validate type
    if recommendation_type not in VALID_TYPES:
        return json.dumps({
            "error": f"Invalid recommendation_type. Valid types: {VALID_TYPES}"
        })

    # Validate priority
    if priority not in VALID_PRIORITIES:
        return json.dumps({
            "error": f"Invalid priority. Valid priorities: {VALID_PRIORITIES}"
        })

    # Parse JSON arrays
    try:
        affected_groups = json.loads(affected_groups_json)
        steps = json.loads(steps_json)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {str(e)}"})

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Project not found", "project_id": project_id})

        rec_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO recommendations (
                id, project_id, title, description, recommendation_type,
                priority, status, affected_groups, steps, parent_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rec_id,
            project_id,
            title,
            description,
            recommendation_type,
            priority,
            "pending_approval",
            json.dumps(affected_groups),
            json.dumps(steps),
            parent_id,
            now
        ))

        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (rec_id,))
        rec = dict_from_row(cursor.fetchone())
        rec["affected_groups"] = affected_groups
        rec["steps"] = steps

        return json.dumps(rec)


async def recommendation_update(
    recommendation_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    recommendation_type: Optional[str] = None,
    priority: Optional[str] = None,
    status: Optional[str] = None,
    affected_groups_json: Optional[str] = None,
    steps_json: Optional[str] = None,
    rejection_reason: Optional[str] = None
) -> str:
    """Update an existing recommendation."""
    # Validate optional fields
    if recommendation_type is not None and recommendation_type not in VALID_TYPES:
        return json.dumps({
            "error": f"Invalid recommendation_type. Valid types: {VALID_TYPES}"
        })
    if priority is not None and priority not in VALID_PRIORITIES:
        return json.dumps({
            "error": f"Invalid priority. Valid priorities: {VALID_PRIORITIES}"
        })
    if status is not None and status not in VALID_STATUSES:
        return json.dumps({
            "error": f"Invalid status. Valid statuses: {VALID_STATUSES}"
        })

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        row = cursor.fetchone()
        if not row:
            return json.dumps({"error": "Recommendation not found", "recommendation_id": recommendation_id})

        now = datetime.utcnow().isoformat()

        # Build update query
        updates = []
        values = []

        if title is not None:
            updates.append("title = ?")
            values.append(title)
        if description is not None:
            updates.append("description = ?")
            values.append(description)
        if recommendation_type is not None:
            updates.append("recommendation_type = ?")
            values.append(recommendation_type)
        if priority is not None:
            updates.append("priority = ?")
            values.append(priority)
        if affected_groups_json is not None:
            updates.append("affected_groups = ?")
            values.append(affected_groups_json)
        if steps_json is not None:
            updates.append("steps = ?")
            values.append(steps_json)
        if rejection_reason is not None:
            updates.append("rejection_reason = ?")
            values.append(rejection_reason)

        # Handle status changes with timestamp updates
        if status is not None:
            updates.append("status = ?")
            values.append(status)

            if status == "approved":
                updates.append("approved_at = ?")
                values.append(now)
            elif status == "started":
                updates.append("started_at = ?")
                values.append(now)
            elif status == "completed":
                updates.append("completed_at = ?")
                values.append(now)

        if updates:
            values.append(recommendation_id)
            cursor.execute(
                f"UPDATE recommendations SET {', '.join(updates)} WHERE id = ?",
                values
            )

        cursor.execute("SELECT * FROM recommendations WHERE id = ?", (recommendation_id,))
        rec = dict_from_row(cursor.fetchone())
        rec["affected_groups"] = json.loads(rec.get("affected_groups") or "[]")
        rec["steps"] = json.loads(rec.get("steps") or "[]")

        return json.dumps(rec)


async def recommendation_delete(recommendation_id: str) -> str:
    """Delete a recommendation."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM recommendations WHERE id = ?", (recommendation_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Recommendation not found", "recommendation_id": recommendation_id})

        cursor.execute("DELETE FROM recommendations WHERE id = ?", (recommendation_id,))

        return json.dumps({"success": True, "message": "Recommendation deleted", "recommendation_id": recommendation_id})


# Tool definitions for the MCP server
TOOLS = {
    "recommendation_list": {
        "description": "List all recommendations for a project, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to get recommendations for"
                },
                "status": {
                    "type": "string",
                    "description": "Optional status filter (pending_approval, approved, rejected, started, completed)"
                }
            },
            "required": ["project_id"]
        },
        "handler": recommendation_list
    },
    "recommendation_get": {
        "description": "Get a single recommendation by ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendation_id": {
                    "type": "string",
                    "description": "The unique identifier of the recommendation"
                }
            },
            "required": ["recommendation_id"]
        },
        "handler": recommendation_get
    },
    "recommendation_create": {
        "description": "Create a new recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to create the recommendation for"
                },
                "title": {
                    "type": "string",
                    "description": "Title of the recommendation"
                },
                "recommendation_type": {
                    "type": "string",
                    "description": "Type: habit, communication, workshop, process, or campaign"
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level: high, medium, or low"
                },
                "affected_groups_json": {
                    "type": "string",
                    "description": "JSON array of affected group IDs or ['all']"
                },
                "steps_json": {
                    "type": "string",
                    "description": "JSON array of action steps"
                },
                "description": {
                    "type": "string",
                    "description": "Optional detailed description"
                },
                "parent_id": {
                    "type": "string",
                    "description": "Optional parent recommendation ID (for regenerated alternatives)"
                }
            },
            "required": ["project_id", "title", "recommendation_type", "priority", "affected_groups_json", "steps_json"]
        },
        "handler": recommendation_create
    },
    "recommendation_update": {
        "description": "Update an existing recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendation_id": {
                    "type": "string",
                    "description": "The unique identifier of the recommendation"
                },
                "title": {
                    "type": "string",
                    "description": "Optional new title"
                },
                "description": {
                    "type": "string",
                    "description": "Optional new description"
                },
                "recommendation_type": {
                    "type": "string",
                    "description": "Optional new type"
                },
                "priority": {
                    "type": "string",
                    "description": "Optional new priority"
                },
                "status": {
                    "type": "string",
                    "description": "Optional new status (triggers timestamp updates)"
                },
                "affected_groups_json": {
                    "type": "string",
                    "description": "Optional new affected groups JSON"
                },
                "steps_json": {
                    "type": "string",
                    "description": "Optional new steps JSON"
                },
                "rejection_reason": {
                    "type": "string",
                    "description": "Optional rejection reason"
                }
            },
            "required": ["recommendation_id"]
        },
        "handler": recommendation_update
    },
    "recommendation_delete": {
        "description": "Delete a recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recommendation_id": {
                    "type": "string",
                    "description": "The unique identifier of the recommendation"
                }
            },
            "required": ["recommendation_id"]
        },
        "handler": recommendation_delete
    }
}
