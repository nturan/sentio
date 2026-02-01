"""
MCP Tools for Stakeholder Assessment operations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_connection, dict_from_row
from app.constants import get_indicators_for_group_type, get_indicator_by_key


async def assessment_list(group_id: str, limit: int = 50) -> str:
    """List assessments for a stakeholder group."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify group exists
        cursor.execute("SELECT id, group_type FROM stakeholder_groups WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        if not group_row:
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        cursor.execute("""
            SELECT id, stakeholder_group_id, indicator_key, rating, notes, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
            LIMIT ?
        """, (group_id, limit))

        assessments = []
        for row in cursor.fetchall():
            assessment = dict_from_row(row)
            # Add indicator details
            indicator = get_indicator_by_key(assessment["indicator_key"])
            if indicator:
                assessment["indicator_name"] = indicator["name"]
                assessment["indicator_description"] = indicator["description"]
            assessments.append(assessment)

        return json.dumps(assessments)


async def assessment_create(
    group_id: str,
    indicator_key: str,
    rating: int,
    notes: Optional[str] = None
) -> str:
    """Create a new assessment for a stakeholder group."""
    # Validate rating
    if not 1 <= rating <= 10:
        return json.dumps({"error": "Rating must be between 1 and 10"})

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify group exists and get type
        cursor.execute("SELECT id, group_type FROM stakeholder_groups WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        if not group_row:
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        group = dict_from_row(group_row)

        # Verify indicator is valid for this group type
        valid_indicators = get_indicators_for_group_type(group["group_type"])
        valid_keys = [ind["key"] for ind in valid_indicators]
        if indicator_key not in valid_keys:
            return json.dumps({
                "error": f"Invalid indicator_key for group type '{group['group_type']}'",
                "valid_keys": valid_keys
            })

        assessment_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO stakeholder_assessments (id, stakeholder_group_id, indicator_key, rating, notes, assessed_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (assessment_id, group_id, indicator_key, rating, notes, now))

        cursor.execute("SELECT * FROM stakeholder_assessments WHERE id = ?", (assessment_id,))
        assessment = dict_from_row(cursor.fetchone())

        # Add indicator details
        indicator = get_indicator_by_key(indicator_key)
        if indicator:
            assessment["indicator_name"] = indicator["name"]
            assessment["indicator_description"] = indicator["description"]

        return json.dumps(assessment)


async def assessment_batch_create(group_id: str, ratings_json: str) -> str:
    """Create multiple assessments at once (for an impulse entry)."""
    try:
        ratings = json.loads(ratings_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid JSON in ratings_json"})

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify group exists and get type
        cursor.execute("SELECT id, group_type FROM stakeholder_groups WHERE id = ?", (group_id,))
        group_row = cursor.fetchone()
        if not group_row:
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        group = dict_from_row(group_row)

        # Verify indicators are valid for this group type
        valid_indicators = get_indicators_for_group_type(group["group_type"])
        valid_keys = [ind["key"] for ind in valid_indicators]

        now = datetime.utcnow().isoformat()
        created_assessments = []

        for indicator_key, rating in ratings.items():
            if indicator_key not in valid_keys:
                continue  # Skip invalid indicators
            if not isinstance(rating, int) or not 1 <= rating <= 10:
                continue  # Skip invalid ratings

            assessment_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO stakeholder_assessments (id, stakeholder_group_id, indicator_key, rating, notes, assessed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (assessment_id, group_id, indicator_key, rating, None, now))

            assessment = {
                "id": assessment_id,
                "stakeholder_group_id": group_id,
                "indicator_key": indicator_key,
                "rating": rating,
                "assessed_at": now
            }
            indicator = get_indicator_by_key(indicator_key)
            if indicator:
                assessment["indicator_name"] = indicator["name"]
            created_assessments.append(assessment)

        return json.dumps({
            "success": True,
            "created_count": len(created_assessments),
            "assessments": created_assessments
        })


async def assessment_delete(assessment_id: str) -> str:
    """Delete an assessment."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM stakeholder_assessments WHERE id = ?", (assessment_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Assessment not found", "assessment_id": assessment_id})

        cursor.execute("DELETE FROM stakeholder_assessments WHERE id = ?", (assessment_id,))

        return json.dumps({"success": True, "message": "Assessment deleted", "assessment_id": assessment_id})


async def impulse_history_get(group_id: str) -> str:
    """Get impulse history for a stakeholder group with trend analysis."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify group exists and get type
        cursor.execute("""
            SELECT sg.id, sg.group_type, sg.name, sg.power_level, sg.interest_level
            FROM stakeholder_groups sg
            WHERE sg.id = ?
        """, (group_id,))
        group_row = cursor.fetchone()
        if not group_row:
            return json.dumps({"error": "Stakeholder group not found", "group_id": group_id})

        group = dict_from_row(group_row)

        # Get all assessments
        cursor.execute("""
            SELECT indicator_key, rating, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
        """, (group_id,))

        assessments = [dict_from_row(row) for row in cursor.fetchall()]

        if not assessments:
            return json.dumps({
                "group_id": group_id,
                "group_name": group.get("name") or group["group_type"],
                "group_type": group["group_type"],
                "total_assessments": 0,
                "impulse_dates": [],
                "average_rating": None,
                "trend": "stable",
                "weak_indicators": [],
                "indicator_averages": {}
            })

        # Group by date to identify impulses
        impulses_by_date = {}
        for assessment in assessments:
            date_str = assessment["assessed_at"][:10] if assessment["assessed_at"] else "unknown"
            if date_str not in impulses_by_date:
                impulses_by_date[date_str] = []
            impulses_by_date[date_str].append(assessment)

        # Calculate averages by indicator
        indicator_values = {}
        for assessment in assessments:
            key = assessment["indicator_key"]
            if key not in indicator_values:
                indicator_values[key] = []
            if assessment["rating"] is not None:
                indicator_values[key].append(assessment["rating"])

        indicator_averages = {}
        weak_indicators = []
        for key, values in indicator_values.items():
            if values:
                avg = sum(values) / len(values)
                indicator_averages[key] = round(avg, 1)

                indicator = get_indicator_by_key(key)
                indicator_name = indicator["name"] if indicator else key

                if avg < 6:
                    weak_indicators.append({
                        "key": key,
                        "name": indicator_name,
                        "rating": round(avg, 1)
                    })

        # Sort weak indicators by rating (lowest first)
        weak_indicators.sort(key=lambda x: x["rating"])

        # Calculate overall average
        all_ratings = [a["rating"] for a in assessments if a["rating"] is not None]
        overall_avg = sum(all_ratings) / len(all_ratings) if all_ratings else None

        # Calculate trend (compare first half vs second half)
        trend = "stable"
        if len(all_ratings) >= 4:
            mid = len(all_ratings) // 2
            recent_avg = sum(all_ratings[:mid]) / mid
            older_avg = sum(all_ratings[mid:]) / (len(all_ratings) - mid)
            if recent_avg > older_avg + 0.5:
                trend = "up"
            elif recent_avg < older_avg - 0.5:
                trend = "down"

        # Build impulse dates with daily averages
        impulse_dates = []
        for date_str in sorted(impulses_by_date.keys(), reverse=True)[:10]:
            impulse_assessments = impulses_by_date[date_str]
            ratings = [a["rating"] for a in impulse_assessments if a["rating"] is not None]
            daily_avg = sum(ratings) / len(ratings) if ratings else None

            impulse_dates.append({
                "date": date_str,
                "assessment_count": len(impulse_assessments),
                "average_rating": round(daily_avg, 1) if daily_avg else None,
                "ratings": {
                    a["indicator_key"]: a["rating"]
                    for a in impulse_assessments
                }
            })

        return json.dumps({
            "group_id": group_id,
            "group_name": group.get("name") or group["group_type"],
            "group_type": group["group_type"],
            "power_level": group["power_level"],
            "interest_level": group["interest_level"],
            "total_assessments": len(assessments),
            "impulse_dates": impulse_dates,
            "average_rating": round(overall_avg, 1) if overall_avg else None,
            "trend": trend,
            "weak_indicators": weak_indicators[:5],
            "indicator_averages": indicator_averages
        })


# Tool definitions for the MCP server
TOOLS = {
    "assessment_list": {
        "description": "List assessments for a stakeholder group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The stakeholder group ID to get assessments for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of assessments to return (default 50)"
                }
            },
            "required": ["group_id"]
        },
        "handler": assessment_list
    },
    "assessment_create": {
        "description": "Create a new assessment for a stakeholder group.",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The stakeholder group ID"
                },
                "indicator_key": {
                    "type": "string",
                    "description": "The indicator key being assessed"
                },
                "rating": {
                    "type": "integer",
                    "description": "Rating value from 1 to 10"
                },
                "notes": {
                    "type": "string",
                    "description": "Optional notes for the assessment"
                }
            },
            "required": ["group_id", "indicator_key", "rating"]
        },
        "handler": assessment_create
    },
    "assessment_batch_create": {
        "description": "Create multiple assessments at once (for an impulse entry).",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_id": {
                    "type": "string",
                    "description": "The stakeholder group ID"
                },
                "ratings_json": {
                    "type": "string",
                    "description": "JSON string of ratings dict {indicator_key: rating, ...}"
                }
            },
            "required": ["group_id", "ratings_json"]
        },
        "handler": assessment_batch_create
    },
    "assessment_delete": {
        "description": "Delete an assessment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "assessment_id": {
                    "type": "string",
                    "description": "The unique identifier of the assessment"
                }
            },
            "required": ["assessment_id"]
        },
        "handler": assessment_delete
    },
    "impulse_history_get": {
        "description": "Get impulse history for a stakeholder group with trend analysis. Useful for generating recommendations and surveys.",
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
        "handler": impulse_history_get
    }
}
