"""
MCP Tools for Survey operations.
"""

import json
import uuid
from datetime import datetime

from app.database import get_connection, dict_from_row
from app.constants import MENDELOW_QUADRANTS, get_indicators_for_group_type, get_indicator_by_key


async def survey_save(
    group_id: str,
    title: str,
    description: str,
    file_path: str
) -> str:
    """Save survey metadata to the database."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get group info
        cursor.execute("""
            SELECT sg.id, sg.project_id
            FROM stakeholder_groups sg
            WHERE sg.id = ?
        """, (group_id,))
        row = cursor.fetchone()

        if not row:
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        group = dict_from_row(row)

        survey_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO surveys (id, project_id, stakeholder_group_id, title, description, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (survey_id, group["project_id"], group_id, title, description, file_path, now))

        return json.dumps({
            "id": survey_id,
            "project_id": group["project_id"],
            "stakeholder_group_id": group_id,
            "title": title,
            "description": description,
            "file_path": file_path,
            "created_at": now
        })


async def survey_get_context(group_id: str) -> str:
    """Get all context needed for survey generation."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get group info with project
        cursor.execute("""
            SELECT sg.id, sg.project_id, sg.group_type, sg.name, sg.power_level, sg.interest_level,
                   p.goal as project_goal, p.name as project_name
            FROM stakeholder_groups sg
            JOIN projects p ON sg.project_id = p.id
            WHERE sg.id = ?
        """, (group_id,))
        row = cursor.fetchone()

        if not row:
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        group = dict_from_row(row)

        # Check if surveys are allowed for this group type
        if group["group_type"] == "fuehrungskraefte":
            return json.dumps({
                "error": "Surveys are only available for Mitarbeitende and Multiplikatoren groups",
                "group_type": group["group_type"]
            })

        # Get Mendelow info
        key = (group["power_level"], group["interest_level"])
        quadrant = MENDELOW_QUADRANTS.get(key, {})
        mendelow_quadrant = quadrant.get("name", "Unknown")
        mendelow_strategy = quadrant.get("strategy", "")

        # Get impulse history
        cursor.execute("""
            SELECT indicator_key, rating, notes, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
        """, (group_id,))
        assessments = [dict_from_row(r) for r in cursor.fetchall()]

        # Group by date
        impulses_by_date = {}
        for assessment in assessments:
            date_str = assessment["assessed_at"][:10] if assessment["assessed_at"] else "unknown"
            if date_str not in impulses_by_date:
                impulses_by_date[date_str] = {"date": date_str, "ratings": {}}
            impulses_by_date[date_str]["ratings"][assessment["indicator_key"]] = assessment["rating"]

        # Calculate averages and identify weak areas
        impulse_history = []
        for date_str, data in sorted(impulses_by_date.items(), reverse=True)[:5]:
            ratings = data["ratings"]
            avg = sum(ratings.values()) / len(ratings) if ratings else 0
            impulse_history.append({
                "date": data["date"],
                "average_rating": round(avg, 1),
                "ratings": ratings
            })

        # Calculate weak areas overall
        all_ratings = {}
        for assessment in assessments:
            key = assessment["indicator_key"]
            if key not in all_ratings:
                all_ratings[key] = []
            if assessment["rating"] is not None:
                all_ratings[key].append(assessment["rating"])

        weak_areas = []
        for indicator_key, values in all_ratings.items():
            if values:
                avg = sum(values) / len(values)
                if avg < 6:
                    indicator = get_indicator_by_key(indicator_key)
                    weak_areas.append({
                        "key": indicator_key,
                        "name": indicator["name"] if indicator else indicator_key,
                        "average": round(avg, 1)
                    })

        weak_areas.sort(key=lambda x: x["average"])

        # Get valid indicators for this group type
        indicators = get_indicators_for_group_type(group["group_type"])

        return json.dumps({
            "group_id": group_id,
            "group_name": group.get("name") or group["group_type"],
            "group_type": group["group_type"],
            "project_id": group["project_id"],
            "project_name": group["project_name"],
            "project_goal": group["project_goal"],
            "power_level": group["power_level"],
            "interest_level": group["interest_level"],
            "mendelow_quadrant": mendelow_quadrant,
            "mendelow_strategy": mendelow_strategy,
            "impulse_history": impulse_history,
            "weak_areas": weak_areas[:5],
            "indicators": indicators
        })


# Tool definitions for the MCP server
TOOLS = {
    "survey_save": {
        "description": "Save survey metadata to the database after a survey file has been created.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The stakeholder group ID"
                },
                "title": {
                    "type": "string",
                    "description": "Survey title"
                },
                "description": {
                    "type": "string",
                    "description": "Survey description"
                },
                "file_path": {
                    "type": "string",
                    "description": "Path where the survey markdown file is saved"
                }
            },
            "required": ["group_id", "title", "description", "file_path"]
        },
        "handler": survey_save
    },
    "survey_get_context": {
        "description": "Get all context needed for survey generation including group info, project context, Mendelow position, and impulse history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The stakeholder group ID"
                }
            },
            "required": ["group_id"]
        },
        "handler": survey_get_context
    }
}
