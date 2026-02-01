"""
MCP Tools for Stakeholder Group operations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_connection, dict_from_row
from app.constants import MENDELOW_QUADRANTS, STAKEHOLDER_GROUP_TYPES, get_indicators_for_group_type


async def stakeholder_group_list(project_id: str) -> str:
    """List all stakeholder groups for a project with Mendelow analysis."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, project_id, group_type, name, power_level, interest_level, notes, created_at
            FROM stakeholder_groups
            WHERE project_id = ?
            ORDER BY created_at ASC
        """, (project_id,))

        groups = []
        for row in cursor.fetchall():
            group = dict_from_row(row)

            # Add Mendelow quadrant information
            key = (group["power_level"], group["interest_level"])
            quadrant = MENDELOW_QUADRANTS.get(key, {})
            group["mendelow_quadrant"] = quadrant.get("name", "Unknown")
            group["mendelow_strategy"] = quadrant.get("strategy", "")

            # Add group type info
            group_type_info = STAKEHOLDER_GROUP_TYPES.get(group["group_type"], {})
            group["group_type_name"] = group_type_info.get("name", group["group_type"])
            group["group_type_description"] = group_type_info.get("description", "")

            groups.append(group)

        return json.dumps(groups)


async def stakeholder_group_get(group_id: str) -> str:
    """Get a single stakeholder group by ID with full details."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sg.*, p.name as project_name, p.goal as project_goal
            FROM stakeholder_groups sg
            JOIN projects p ON sg.project_id = p.id
            WHERE sg.id = ?
        """, (group_id,))
        row = cursor.fetchone()

        if not row:
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        group = dict_from_row(row)

        # Add Mendelow quadrant information
        key = (group["power_level"], group["interest_level"])
        quadrant = MENDELOW_QUADRANTS.get(key, {})
        group["mendelow_quadrant"] = quadrant.get("name", "Unknown")
        group["mendelow_strategy"] = quadrant.get("strategy", "")

        # Add indicators for this group type
        indicators = get_indicators_for_group_type(group["group_type"])
        group["indicators"] = indicators

        return json.dumps(group)


async def stakeholder_group_create(
    project_id: str,
    group_type: str,
    power_level: str,
    interest_level: str,
    name: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """Create a new stakeholder group."""
    # Validate group_type
    if group_type not in STAKEHOLDER_GROUP_TYPES:
        return json.dumps({
            "error": "Invalid group_type",
            "valid_types": list(STAKEHOLDER_GROUP_TYPES.keys())
        })

    # Validate power/interest levels
    if power_level not in ("high", "low"):
        return json.dumps({"error": "power_level must be 'high' or 'low'"})
    if interest_level not in ("high", "low"):
        return json.dumps({"error": "interest_level must be 'high' or 'low'"})

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Project not found", "project_id": project_id})

        group_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO stakeholder_groups (id, project_id, group_type, name, power_level, interest_level, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (group_id, project_id, group_type, name, power_level, interest_level, notes, now))

        cursor.execute("SELECT * FROM stakeholder_groups WHERE id = ?", (group_id,))
        group = dict_from_row(cursor.fetchone())

        # Add Mendelow info
        key = (group["power_level"], group["interest_level"])
        quadrant = MENDELOW_QUADRANTS.get(key, {})
        group["mendelow_quadrant"] = quadrant.get("name", "Unknown")
        group["mendelow_strategy"] = quadrant.get("strategy", "")

        return json.dumps(group)


async def stakeholder_group_update(
    group_id: str,
    name: Optional[str] = None,
    power_level: Optional[str] = None,
    interest_level: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """Update an existing stakeholder group."""
    # Validate power/interest levels if provided
    if power_level is not None and power_level not in ("high", "low"):
        return json.dumps({"error": "power_level must be 'high' or 'low'"})
    if interest_level is not None and interest_level not in ("high", "low"):
        return json.dumps({"error": "interest_level must be 'high' or 'low'"})

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM stakeholder_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        # Build update query
        updates = []
        values = []

        if name is not None:
            updates.append("name = ?")
            values.append(name)
        if power_level is not None:
            updates.append("power_level = ?")
            values.append(power_level)
        if interest_level is not None:
            updates.append("interest_level = ?")
            values.append(interest_level)
        if notes is not None:
            updates.append("notes = ?")
            values.append(notes)

        if updates:
            values.append(group_id)
            cursor.execute(
                f"UPDATE stakeholder_groups SET {', '.join(updates)} WHERE id = ?",
                values
            )

        cursor.execute("SELECT * FROM stakeholder_groups WHERE id = ?", (group_id,))
        group = dict_from_row(cursor.fetchone())

        # Add Mendelow info
        key = (group["power_level"], group["interest_level"])
        quadrant = MENDELOW_QUADRANTS.get(key, {})
        group["mendelow_quadrant"] = quadrant.get("name", "Unknown")
        group["mendelow_strategy"] = quadrant.get("strategy", "")

        return json.dumps(group)


async def stakeholder_group_delete(group_id: str) -> str:
    """Delete a stakeholder group and all related assessments."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM stakeholder_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        # Delete cascades due to foreign key constraints
        cursor.execute("DELETE FROM stakeholder_groups WHERE id = ?", (group_id,))

        return json.dumps({"success": True, "message": "Stakeholder group deleted", "group_id": group_id})


async def stakeholder_group_types_list() -> str:
    """Get available stakeholder group types and their configurations."""
    result = {}
    for key, value in STAKEHOLDER_GROUP_TYPES.items():
        result[key] = {
            "name": value["name"],
            "description": value["description"],
            "indicators": value["indicators"]
        }
    return json.dumps(result)


# Tool definitions for the MCP server
TOOLS = {
    "stakeholder_group_list": {
        "description": "List all stakeholder groups for a project with Mendelow analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to get stakeholder groups for"
                }
            },
            "required": ["project_id"]
        },
        "handler": stakeholder_group_list
    },
    "stakeholder_group_get": {
        "description": "Get a single stakeholder group by ID with full details including Mendelow analysis and indicators.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The unique identifier of the stakeholder group"
                }
            },
            "required": ["group_id"]
        },
        "handler": stakeholder_group_get
    },
    "stakeholder_group_create": {
        "description": "Create a new stakeholder group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to create the group for"
                },
                "group_type": {
                    "type": "string",
                    "description": "Type of group: 'fuehrungskraefte', 'multiplikatoren', or 'mitarbeitende'"
                },
                "power_level": {
                    "type": "string",
                    "description": "Power level: 'high' or 'low'"
                },
                "interest_level": {
                    "type": "string",
                    "description": "Interest level: 'high' or 'low'"
                },
                "name": {
                    "type": "string",
                    "description": "Optional custom name for the group"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes about the group"
                }
            },
            "required": ["project_id", "group_type", "power_level", "interest_level"]
        },
        "handler": stakeholder_group_create
    },
    "stakeholder_group_update": {
        "description": "Update an existing stakeholder group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The unique identifier of the stakeholder group"
                },
                "name": {
                    "type": "string",
                    "description": "Optional new name"
                },
                "power_level": {
                    "type": "string",
                    "description": "Optional new power level: 'high' or 'low'"
                },
                "interest_level": {
                    "type": "string",
                    "description": "Optional new interest level: 'high' or 'low'"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional new notes"
                }
            },
            "required": ["group_id"]
        },
        "handler": stakeholder_group_update
    },
    "stakeholder_group_delete": {
        "description": "Delete a stakeholder group and all related assessments.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The unique identifier of the stakeholder group"
                }
            },
            "required": ["group_id"]
        },
        "handler": stakeholder_group_delete
    },
    "stakeholder_group_types": {
        "description": "Get available stakeholder group types and their configurations with indicators.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": stakeholder_group_types_list
    }
}
