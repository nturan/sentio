from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_connection, dict_from_row
from ..constants import (
    CORE_INDICATORS,
    FUEHRUNGSKRAEFTE_INDICATORS,
    STAKEHOLDER_GROUP_TYPES,
    get_indicators_for_group_type,
    get_indicator_by_key
)

router = APIRouter(prefix="/api", tags=["workflow"])


# --- Pydantic Models ---

class PredefinedIndicator(BaseModel):
    key: str
    name: str
    description: str


class AssessmentRoundCreate(BaseModel):
    title: Optional[str] = None


class AssessmentRound(BaseModel):
    id: str
    project_id: str
    title: Optional[str]
    created_at: str


class RatingCreate(BaseModel):
    indicator_key: str
    assessment_type: str = "self_rating"
    rating: int
    notes: Optional[str] = None


class Assessment(BaseModel):
    id: str
    round_id: str
    indicator_key: str
    assessment_type: str
    rating: int
    notes: Optional[str]
    created_at: str


class AssessmentRoundWithRatings(BaseModel):
    id: str
    project_id: str
    title: Optional[str]
    created_at: str
    ratings: List[Assessment]


class DashboardIndicatorScore(BaseModel):
    key: str
    name: str
    description: str
    average_rating: Optional[float]
    latest_rating: Optional[int]
    rating_count: int


class DashboardData(BaseModel):
    indicators: List[DashboardIndicatorScore]
    trend_data: List[dict]


# --- Predefined Indicators Endpoint ---

@router.get("/indicators/predefined", response_model=List[PredefinedIndicator])
async def get_predefined_indicators():
    """Get all predefined indicator definitions."""
    all_indicators = []
    for ind in CORE_INDICATORS:
        all_indicators.append(PredefinedIndicator(**ind))
    for ind in FUEHRUNGSKRAEFTE_INDICATORS:
        all_indicators.append(PredefinedIndicator(**ind))
    return all_indicators


@router.get("/indicators/core", response_model=List[PredefinedIndicator])
async def get_core_indicators():
    """Get the 5 core Bewertungsfaktoren."""
    return [PredefinedIndicator(**ind) for ind in CORE_INDICATORS]


@router.get("/indicators/fuehrungskraefte", response_model=List[PredefinedIndicator])
async def get_fuehrungskraefte_indicators():
    """Get the 4 additional Fuehrungskraefte indicators."""
    return [PredefinedIndicator(**ind) for ind in FUEHRUNGSKRAEFTE_INDICATORS]


# --- Dashboard Data Endpoint ---

@router.get("/projects/{project_id}/dashboard-data", response_model=DashboardData)
async def get_dashboard_data(project_id: str):
    """Get indicator scores and trend data for the dashboard."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Get all stakeholder assessments for this project
        cursor.execute("""
            SELECT sa.indicator_key, sa.rating, sa.assessed_at, sg.group_type
            FROM stakeholder_assessments sa
            JOIN stakeholder_groups sg ON sa.stakeholder_group_id = sg.id
            WHERE sg.project_id = ?
            ORDER BY sa.assessed_at ASC
        """, (project_id,))

        assessments = [dict_from_row(row) for row in cursor.fetchall()]

        # Calculate scores per indicator
        indicator_scores = {}
        for ind in CORE_INDICATORS:
            key = ind["key"]
            ratings = [a["rating"] for a in assessments if a["indicator_key"] == key and a["rating"] is not None]

            indicator_scores[key] = DashboardIndicatorScore(
                key=key,
                name=ind["name"],
                description=ind["description"],
                average_rating=sum(ratings) / len(ratings) if ratings else None,
                latest_rating=ratings[-1] if ratings else None,
                rating_count=len(ratings)
            )

        # Build trend data (group by assessment date)
        trend_data = []
        dates_seen = {}
        for assessment in assessments:
            # Only include core indicators in trend
            if assessment["indicator_key"] not in [i["key"] for i in CORE_INDICATORS]:
                continue

            date_str = assessment["assessed_at"][:10]  # Get date part only
            if date_str not in dates_seen:
                dates_seen[date_str] = {"date": date_str}

            key = assessment["indicator_key"]
            # Use latest rating for each indicator on each date
            dates_seen[date_str][key] = assessment["rating"]

        trend_data = list(dates_seen.values())
        trend_data.sort(key=lambda x: x["date"])

        return DashboardData(
            indicators=list(indicator_scores.values()),
            trend_data=trend_data
        )


# --- Assessment Round Endpoints (kept for backward compatibility) ---

@router.get("/projects/{project_id}/assessment-rounds", response_model=List[AssessmentRound])
async def list_assessment_rounds(project_id: str):
    """List all assessment rounds for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_id, title, created_at
            FROM assessment_rounds
            WHERE project_id = ?
            ORDER BY created_at DESC
            """,
            (project_id,)
        )
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@router.post("/projects/{project_id}/assessment-rounds", response_model=AssessmentRound)
async def create_assessment_round(project_id: str, round_data: AssessmentRoundCreate):
    """Create a new assessment round."""
    round_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Generate default title if not provided
        title = round_data.title
        if not title:
            cursor.execute(
                "SELECT COUNT(*) as count FROM assessment_rounds WHERE project_id = ?",
                (project_id,)
            )
            count = cursor.fetchone()["count"]
            title = f"Bewertung #{count + 1}"

        cursor.execute(
            """
            INSERT INTO assessment_rounds (id, project_id, title, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (round_id, project_id, title, now)
        )

        return {
            "id": round_id,
            "project_id": project_id,
            "title": title,
            "created_at": now
        }


@router.get("/assessment-rounds/{round_id}", response_model=AssessmentRoundWithRatings)
async def get_assessment_round(round_id: str):
    """Get an assessment round with all its ratings."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, project_id, title, created_at
            FROM assessment_rounds
            WHERE id = ?
            """,
            (round_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Assessment round not found")

        round_data = dict_from_row(row)

        # Get all ratings for this round - now using indicator_key instead of indicator_id
        cursor.execute(
            """
            SELECT id, round_id, indicator_id as indicator_key, assessment_type, rating, notes, created_at
            FROM assessments
            WHERE round_id = ?
            ORDER BY created_at ASC
            """,
            (round_id,)
        )
        ratings = [dict_from_row(r) for r in cursor.fetchall()]

        return {
            **round_data,
            "ratings": ratings
        }


@router.delete("/assessment-rounds/{round_id}")
async def delete_assessment_round(round_id: str):
    """Delete an assessment round and all its ratings."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM assessment_rounds WHERE id = ?", (round_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Assessment round not found")

        cursor.execute("DELETE FROM assessment_rounds WHERE id = ?", (round_id,))

        return {"message": "Assessment round deleted"}


@router.get("/projects/{project_id}/assessment-history")
async def get_assessment_history(project_id: str):
    """Get all assessments for a project with indicator details for charting."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Build indicators map from constants
        indicators = {}
        for ind in CORE_INDICATORS:
            indicators[ind["key"]] = ind["name"]
        for ind in FUEHRUNGSKRAEFTE_INDICATORS:
            indicators[ind["key"]] = ind["name"]

        # Get stakeholder assessments grouped by date
        cursor.execute(
            """
            SELECT sa.indicator_key, sa.rating, sa.notes, sa.assessed_at, sg.name as group_name
            FROM stakeholder_assessments sa
            JOIN stakeholder_groups sg ON sa.stakeholder_group_id = sg.id
            WHERE sg.project_id = ?
            ORDER BY sa.assessed_at ASC
            """,
            (project_id,)
        )
        rows = cursor.fetchall()

        # Group by date
        rounds_map = {}
        for row in rows:
            row_dict = dict_from_row(row)
            date_str = row_dict["assessed_at"][:10]

            if date_str not in rounds_map:
                rounds_map[date_str] = {
                    "id": date_str,
                    "title": f"Assessment {date_str}",
                    "date": row_dict["assessed_at"],
                    "ratings": {}
                }

            indicator_name = indicators.get(row_dict["indicator_key"], row_dict["indicator_key"])
            rounds_map[date_str]["ratings"][indicator_name] = {
                "indicator_key": row_dict["indicator_key"],
                "rating": row_dict["rating"],
                "notes": row_dict["notes"]
            }

        return {
            "indicators": indicators,
            "rounds": list(rounds_map.values())
        }
