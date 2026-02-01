"""
MCP Tools for Workflow and Dashboard operations.
"""

import json
from typing import Optional

from app.database import get_connection, dict_from_row
from app.constants import (
    CORE_INDICATORS,
    FUEHRUNGSKRAEFTE_INDICATORS,
    MENDELOW_QUADRANTS,
    get_indicator_by_key
)


async def indicators_get() -> str:
    """Get all indicator definitions."""
    return json.dumps({
        "core_indicators": CORE_INDICATORS,
        "fuehrungskraefte_indicators": FUEHRUNGSKRAEFTE_INDICATORS,
        "all_indicators": CORE_INDICATORS + FUEHRUNGSKRAEFTE_INDICATORS
    })


async def dashboard_data_get(project_id: str) -> str:
    """Get comprehensive dashboard data for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get project info
        cursor.execute("SELECT id, name, goal, created_at FROM projects WHERE id = ?", (project_id,))
        project_row = cursor.fetchone()
        if not project_row:
            return json.dumps({"error": "Project not found", "project_id": project_id})

        project = dict_from_row(project_row)

        # Get stakeholder groups with assessments
        cursor.execute("""
            SELECT id, group_type, name, power_level, interest_level
            FROM stakeholder_groups
            WHERE project_id = ?
        """, (project_id,))
        groups = [dict_from_row(row) for row in cursor.fetchall()]

        # Aggregate assessment data per group
        group_summaries = []
        all_ratings = []

        for group in groups:
            cursor.execute("""
                SELECT indicator_key, rating, assessed_at
                FROM stakeholder_assessments
                WHERE stakeholder_group_id = ?
                ORDER BY assessed_at DESC
            """, (group["id"],))
            assessments = [dict_from_row(row) for row in cursor.fetchall()]

            if assessments:
                ratings = [a["rating"] for a in assessments if a["rating"] is not None]
                avg = sum(ratings) / len(ratings) if ratings else None
                all_ratings.extend(ratings)

                # Get weak indicators for this group
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
                        indicator = get_indicator_by_key(key)
                        weak_indicators.append({
                            "key": key,
                            "name": indicator["name"] if indicator else key,
                            "rating": round(ind_avg, 1)
                        })
                weak_indicators.sort(key=lambda x: x["rating"])

                # Add Mendelow info
                key = (group["power_level"], group["interest_level"])
                quadrant = MENDELOW_QUADRANTS.get(key, {})

                group_summaries.append({
                    "id": group["id"],
                    "name": group.get("name") or group["group_type"],
                    "type": group["group_type"],
                    "power_level": group["power_level"],
                    "interest_level": group["interest_level"],
                    "mendelow_quadrant": quadrant.get("name", "Unknown"),
                    "average_rating": round(avg, 1) if avg else None,
                    "assessment_count": len(assessments),
                    "weak_indicators": weak_indicators[:3]
                })

        # Calculate overall project health
        overall_avg = sum(all_ratings) / len(all_ratings) if all_ratings else None

        # Get recommendation summary
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM recommendations
            WHERE project_id = ?
            GROUP BY status
        """, (project_id,))
        rec_status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}

        # Get document count
        cursor.execute("SELECT COUNT(*) as count FROM documents WHERE project_id = ?", (project_id,))
        doc_count = cursor.fetchone()["count"]

        # Get session count
        cursor.execute("SELECT COUNT(*) as count FROM chat_sessions WHERE project_id = ?", (project_id,))
        session_count = cursor.fetchone()["count"]

        return json.dumps({
            "project": {
                "id": project["id"],
                "name": project["name"],
                "goal": project["goal"],
                "created_at": project["created_at"]
            },
            "health": {
                "overall_rating": round(overall_avg, 1) if overall_avg else None,
                "total_assessments": len(all_ratings),
                "stakeholder_group_count": len(groups)
            },
            "stakeholder_groups": group_summaries,
            "recommendations": {
                "pending_approval": rec_status_counts.get("pending_approval", 0),
                "approved": rec_status_counts.get("approved", 0),
                "rejected": rec_status_counts.get("rejected", 0),
                "started": rec_status_counts.get("started", 0),
                "completed": rec_status_counts.get("completed", 0),
                "total": sum(rec_status_counts.values())
            },
            "activity": {
                "document_count": doc_count,
                "chat_session_count": session_count
            }
        })


async def assessment_history_get(project_id: str, days: int = 30) -> str:
    """Get assessment history over time for trend analysis."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get all assessments for the project via stakeholder groups
        cursor.execute("""
            SELECT sa.indicator_key, sa.rating, sa.assessed_at,
                   sg.id as group_id, sg.name as group_name, sg.group_type
            FROM stakeholder_assessments sa
            JOIN stakeholder_groups sg ON sa.stakeholder_group_id = sg.id
            WHERE sg.project_id = ?
            ORDER BY sa.assessed_at DESC
        """, (project_id,))

        assessments = [dict_from_row(row) for row in cursor.fetchall()]

        # Group by date
        by_date = {}
        for assessment in assessments:
            date_str = assessment["assessed_at"][:10] if assessment["assessed_at"] else "unknown"
            if date_str not in by_date:
                by_date[date_str] = {
                    "date": date_str,
                    "ratings": [],
                    "by_group": {},
                    "by_indicator": {}
                }

            if assessment["rating"] is not None:
                by_date[date_str]["ratings"].append(assessment["rating"])

                # Group by stakeholder group
                group_name = assessment.get("group_name") or assessment["group_type"]
                if group_name not in by_date[date_str]["by_group"]:
                    by_date[date_str]["by_group"][group_name] = []
                by_date[date_str]["by_group"][group_name].append(assessment["rating"])

                # Group by indicator
                indicator_key = assessment["indicator_key"]
                if indicator_key not in by_date[date_str]["by_indicator"]:
                    by_date[date_str]["by_indicator"][indicator_key] = []
                by_date[date_str]["by_indicator"][indicator_key].append(assessment["rating"])

        # Calculate averages
        history = []
        for date_str in sorted(by_date.keys(), reverse=True):
            data = by_date[date_str]
            ratings = data["ratings"]

            group_averages = {}
            for group_name, group_ratings in data["by_group"].items():
                group_averages[group_name] = round(sum(group_ratings) / len(group_ratings), 1)

            indicator_averages = {}
            for ind_key, ind_ratings in data["by_indicator"].items():
                indicator = get_indicator_by_key(ind_key)
                ind_name = indicator["name"] if indicator else ind_key
                indicator_averages[ind_name] = round(sum(ind_ratings) / len(ind_ratings), 1)

            history.append({
                "date": date_str,
                "average_rating": round(sum(ratings) / len(ratings), 1) if ratings else None,
                "assessment_count": len(ratings),
                "by_group": group_averages,
                "by_indicator": indicator_averages
            })

        return json.dumps({
            "project_id": project_id,
            "period_days": days,
            "history": history[:days] if days else history
        })


# Tool definitions for the MCP server
TOOLS = {
    "indicators_get": {
        "description": "Get all indicator definitions including core indicators and leadership-specific indicators.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": indicators_get
    },
    "dashboard_data_get": {
        "description": "Get comprehensive dashboard data for a project including stakeholder summaries, recommendations, and activity metrics.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                }
            },
            "required": ["project_id"]
        },
        "handler": dashboard_data_get
    },
    "assessment_history_get": {
        "description": "Get assessment history over time for trend analysis.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID"
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (default 30)"
                }
            },
            "required": ["project_id"]
        },
        "handler": assessment_history_get
    }
}
