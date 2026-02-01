"""
MCP Tools for Project operations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_connection, dict_from_row


async def project_list() -> str:
    """List all projects."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, icon, goal, created_at, updated_at
            FROM projects
            ORDER BY created_at DESC
        """)
        projects = [dict_from_row(row) for row in cursor.fetchall()]
    return json.dumps(projects)


async def project_get(project_id: str) -> str:
    """Get a single project by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, icon, goal, created_at, updated_at
            FROM projects
            WHERE id = ?
        """, (project_id,))
        row = cursor.fetchone()

        if not row:
            return json.dumps({"error": "Project not found", "project_id": project_id})

        return json.dumps(dict_from_row(row))


async def project_create(name: str, goal: Optional[str] = None, icon: Optional[str] = None) -> str:
    """Create a new project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        project_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        project_icon = icon or "🚀"

        cursor.execute("""
            INSERT INTO projects (id, name, icon, goal, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, name, project_icon, goal, now, now))

        # Also create initial workflow state
        workflow_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO workflow_state (id, project_id, current_stage, created_at, updated_at)
            VALUES (?, ?, 'define_indicators', ?, ?)
        """, (workflow_id, project_id, now, now))

        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        return json.dumps(dict_from_row(cursor.fetchone()))


async def project_update(
    project_id: str,
    name: Optional[str] = None,
    goal: Optional[str] = None,
    icon: Optional[str] = None
) -> str:
    """Update an existing project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Project not found", "project_id": project_id})

        # Build update query
        updates = []
        values = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if goal is not None:
            updates.append("goal = ?")
            values.append(goal)
        if icon is not None:
            updates.append("icon = ?")
            values.append(icon)

        if updates:
            updates.append("updated_at = ?")
            values.append(datetime.utcnow().isoformat())
            values.append(project_id)

            cursor.execute(
                f"UPDATE projects SET {', '.join(updates)} WHERE id = ?",
                values
            )

        cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        return json.dumps(dict_from_row(cursor.fetchone()))


async def project_delete(project_id: str) -> str:
    """Delete a project and all related data."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Project not found", "project_id": project_id})

        # Delete cascades due to foreign key constraints
        cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

        return json.dumps({"success": True, "message": "Project deleted", "project_id": project_id})


# Tool definitions for the MCP server
TOOLS = {
    "project_list": {
        "description": "List all projects. Returns JSON array of project objects with id, name, icon, goal, created_at, updated_at.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": project_list
    },
    "project_get": {
        "description": "Get a single project by ID. Returns JSON object with project details or error.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The unique identifier of the project"
                }
            },
            "required": ["project_id"]
        },
        "handler": project_get
    },
    "project_create": {
        "description": "Create a new project. Returns the created project object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name of the project"
                },
                "goal": {
                    "type": "string",
                    "description": "Optional project goal/description"
                },
                "icon": {
                    "type": "string",
                    "description": "Optional emoji icon (defaults to rocket)"
                }
            },
            "required": ["name"]
        },
        "handler": project_create
    },
    "project_update": {
        "description": "Update an existing project. Returns the updated project object.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The unique identifier of the project"
                },
                "name": {
                    "type": "string",
                    "description": "Optional new name"
                },
                "goal": {
                    "type": "string",
                    "description": "Optional new goal"
                },
                "icon": {
                    "type": "string",
                    "description": "Optional new icon"
                }
            },
            "required": ["project_id"]
        },
        "handler": project_update
    },
    "project_delete": {
        "description": "Delete a project and all related data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The unique identifier of the project"
                }
            },
            "required": ["project_id"]
        },
        "handler": project_delete
    }
}
