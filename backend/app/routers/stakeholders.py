from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import asyncio

from ..database import get_connection, dict_from_row
from ..constants import (
    STAKEHOLDER_GROUP_TYPES,
    MENDELOW_QUADRANTS,
    get_indicators_for_group_type,
    get_indicator_by_key,
    CORE_INDICATORS,
    FUEHRUNGSKRAEFTE_INDICATORS
)

router = APIRouter(prefix="/api", tags=["stakeholders"])


# --- Pydantic Models ---

class StakeholderGroupCreate(BaseModel):
    group_type: str  # 'fuehrungskraefte', 'multiplikatoren', 'mitarbeitende'
    name: Optional[str] = None
    power_level: str  # 'high' or 'low'
    interest_level: str  # 'high' or 'low'
    notes: Optional[str] = None


class StakeholderGroupUpdate(BaseModel):
    name: Optional[str] = None
    power_level: Optional[str] = None
    interest_level: Optional[str] = None
    notes: Optional[str] = None


class StakeholderGroup(BaseModel):
    id: str
    project_id: str
    group_type: str
    name: Optional[str]
    power_level: str
    interest_level: str
    notes: Optional[str]
    created_at: str
    mendelow_quadrant: str
    mendelow_strategy: str


class StakeholderAssessmentCreate(BaseModel):
    indicator_key: str
    rating: int
    notes: Optional[str] = None
    assessed_at: Optional[str] = None  # ISO format date string (e.g., "2026-01-31")


class StakeholderAssessment(BaseModel):
    id: str
    stakeholder_group_id: str
    indicator_key: str
    rating: int
    notes: Optional[str]
    assessed_at: str


class StakeholderGroupWithAssessments(BaseModel):
    id: str
    project_id: str
    group_type: str
    name: Optional[str]
    power_level: str
    interest_level: str
    notes: Optional[str]
    created_at: str
    mendelow_quadrant: str
    mendelow_strategy: str
    assessments: List[StakeholderAssessment]
    available_indicators: List[dict]


class StakeholderGroupTypeInfo(BaseModel):
    key: str
    name: str
    description: str
    indicator_count: int


# --- Helper Functions ---

def get_mendelow_info(power_level: str, interest_level: str) -> tuple:
    """Get Mendelow quadrant name and strategy."""
    key = (power_level, interest_level)
    if key in MENDELOW_QUADRANTS:
        return MENDELOW_QUADRANTS[key]["name"], MENDELOW_QUADRANTS[key]["strategy"]
    return "Unknown", "No strategy defined"


def enrich_group_with_mendelow(group: dict) -> dict:
    """Add Mendelow quadrant info to a group dict."""
    quadrant, strategy = get_mendelow_info(group["power_level"], group["interest_level"])
    return {
        **group,
        "mendelow_quadrant": quadrant,
        "mendelow_strategy": strategy
    }


# --- Group Type Info Endpoints ---

@router.get("/stakeholder-group-types", response_model=List[StakeholderGroupTypeInfo])
async def list_stakeholder_group_types():
    """Get all available stakeholder group types."""
    types = []
    for key, info in STAKEHOLDER_GROUP_TYPES.items():
        types.append(StakeholderGroupTypeInfo(
            key=key,
            name=info["name"],
            description=info["description"],
            indicator_count=len(info["indicators"])
        ))
    return types


# --- Stakeholder Group Endpoints ---

@router.get("/projects/{project_id}/stakeholder-groups", response_model=List[StakeholderGroup])
async def list_stakeholder_groups(project_id: str):
    """List all stakeholder groups for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        cursor.execute(
            """
            SELECT id, project_id, group_type, name, power_level, interest_level, notes, created_at
            FROM stakeholder_groups
            WHERE project_id = ?
            ORDER BY created_at ASC
            """,
            (project_id,)
        )
        rows = cursor.fetchall()

        return [enrich_group_with_mendelow(dict_from_row(row)) for row in rows]


@router.post("/projects/{project_id}/stakeholder-groups", response_model=StakeholderGroup)
async def create_stakeholder_group(project_id: str, data: StakeholderGroupCreate):
    """Create a new stakeholder group for a project."""

    # Validate group_type
    if data.group_type not in STAKEHOLDER_GROUP_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid group_type. Must be one of: {', '.join(STAKEHOLDER_GROUP_TYPES.keys())}"
        )

    # Validate power_level and interest_level
    if data.power_level not in ("high", "low"):
        raise HTTPException(status_code=400, detail="power_level must be 'high' or 'low'")
    if data.interest_level not in ("high", "low"):
        raise HTTPException(status_code=400, detail="interest_level must be 'high' or 'low'")

    group_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        cursor.execute(
            """
            INSERT INTO stakeholder_groups (id, project_id, group_type, name, power_level, interest_level, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (group_id, project_id, data.group_type, data.name, data.power_level, data.interest_level, data.notes, now)
        )

        result = {
            "id": group_id,
            "project_id": project_id,
            "group_type": data.group_type,
            "name": data.name,
            "power_level": data.power_level,
            "interest_level": data.interest_level,
            "notes": data.notes,
            "created_at": now
        }

        return enrich_group_with_mendelow(result)


@router.get("/stakeholder-groups/{group_id}", response_model=StakeholderGroupWithAssessments)
async def get_stakeholder_group(group_id: str):
    """Get a stakeholder group with all its assessments."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, project_id, group_type, name, power_level, interest_level, notes, created_at
            FROM stakeholder_groups
            WHERE id = ?
            """,
            (group_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        group_data = enrich_group_with_mendelow(dict_from_row(row))

        # Get all assessments for this group
        cursor.execute(
            """
            SELECT id, stakeholder_group_id, indicator_key, rating, notes, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
            """,
            (group_id,)
        )
        assessments = [dict_from_row(r) for r in cursor.fetchall()]

        # Get available indicators for this group type
        available_indicators = get_indicators_for_group_type(group_data["group_type"])

        return {
            **group_data,
            "assessments": assessments,
            "available_indicators": available_indicators
        }


@router.patch("/stakeholder-groups/{group_id}", response_model=StakeholderGroup)
async def update_stakeholder_group(group_id: str, data: StakeholderGroupUpdate):
    """Update a stakeholder group."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, project_id, group_type, name, power_level, interest_level, notes, created_at
            FROM stakeholder_groups
            WHERE id = ?
            """,
            (group_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        current = dict_from_row(row)

        # Validate new values if provided
        new_power = data.power_level if data.power_level is not None else current["power_level"]
        new_interest = data.interest_level if data.interest_level is not None else current["interest_level"]

        if new_power not in ("high", "low"):
            raise HTTPException(status_code=400, detail="power_level must be 'high' or 'low'")
        if new_interest not in ("high", "low"):
            raise HTTPException(status_code=400, detail="interest_level must be 'high' or 'low'")

        new_name = data.name if data.name is not None else current["name"]
        new_notes = data.notes if data.notes is not None else current["notes"]

        cursor.execute(
            """
            UPDATE stakeholder_groups
            SET name = ?, power_level = ?, interest_level = ?, notes = ?
            WHERE id = ?
            """,
            (new_name, new_power, new_interest, new_notes, group_id)
        )

        result = {
            "id": group_id,
            "project_id": current["project_id"],
            "group_type": current["group_type"],
            "name": new_name,
            "power_level": new_power,
            "interest_level": new_interest,
            "notes": new_notes,
            "created_at": current["created_at"]
        }

        return enrich_group_with_mendelow(result)


@router.delete("/stakeholder-groups/{group_id}")
async def delete_stakeholder_group(group_id: str):
    """Delete a stakeholder group and all its assessments."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM stakeholder_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        cursor.execute("DELETE FROM stakeholder_groups WHERE id = ?", (group_id,))

        return {"message": "Stakeholder group deleted"}


# --- Assessment Endpoints ---

@router.get("/stakeholder-groups/{group_id}/assessments", response_model=List[StakeholderAssessment])
async def list_stakeholder_assessments(group_id: str):
    """Get all assessments for a stakeholder group."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify group exists
        cursor.execute("SELECT id FROM stakeholder_groups WHERE id = ?", (group_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        cursor.execute(
            """
            SELECT id, stakeholder_group_id, indicator_key, rating, notes, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
            """,
            (group_id,)
        )
        rows = cursor.fetchall()

        return [dict_from_row(row) for row in rows]


@router.post("/stakeholder-groups/{group_id}/assessments", response_model=StakeholderAssessment)
async def add_stakeholder_assessment(group_id: str, data: StakeholderAssessmentCreate):
    """Add an assessment for a stakeholder group."""

    # Validate rating
    if data.rating < 1 or data.rating > 10:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 10")

    # Validate indicator_key
    indicator = get_indicator_by_key(data.indicator_key)
    if not indicator:
        raise HTTPException(status_code=400, detail=f"Invalid indicator_key: {data.indicator_key}")

    assessment_id = str(uuid.uuid4())

    # Use custom assessed_at if provided, otherwise use now
    if data.assessed_at:
        try:
            # Validate and parse the date
            assessed_at = datetime.fromisoformat(data.assessed_at.replace('Z', '+00:00')).isoformat()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid assessed_at format. Use ISO format (e.g., '2026-01-31')")
    else:
        assessed_at = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify group exists and get its type
        cursor.execute(
            "SELECT id, group_type FROM stakeholder_groups WHERE id = ?",
            (group_id,)
        )
        group_row = cursor.fetchone()
        if not group_row:
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        group_type = group_row["group_type"]

        # Verify this indicator is valid for this group type
        valid_indicators = get_indicators_for_group_type(group_type)
        valid_keys = [ind["key"] for ind in valid_indicators]
        if data.indicator_key not in valid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Indicator '{data.indicator_key}' is not valid for group type '{group_type}'"
            )

        # Extract just the date part for comparison (allows one assessment per indicator per day)
        assessed_date = assessed_at[:10]  # e.g., "2026-01-31"

        # Check if assessment already exists for this indicator ON THE SAME DATE
        cursor.execute(
            """
            SELECT id FROM stakeholder_assessments
            WHERE stakeholder_group_id = ? AND indicator_key = ? AND DATE(assessed_at) = ?
            """,
            (group_id, data.indicator_key, assessed_date)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing assessment for same date
            cursor.execute(
                """
                UPDATE stakeholder_assessments
                SET rating = ?, notes = ?, assessed_at = ?
                WHERE id = ?
                """,
                (data.rating, data.notes, assessed_at, existing["id"])
            )
            assessment_id = existing["id"]
        else:
            # Create NEW assessment (different date = new historical entry)
            cursor.execute(
                """
                INSERT INTO stakeholder_assessments (id, stakeholder_group_id, indicator_key, rating, notes, assessed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (assessment_id, group_id, data.indicator_key, data.rating, data.notes, assessed_at)
            )

        return {
            "id": assessment_id,
            "stakeholder_group_id": group_id,
            "indicator_key": data.indicator_key,
            "rating": data.rating,
            "notes": data.notes,
            "assessed_at": assessed_at
        }


@router.delete("/stakeholder-assessments/{assessment_id}")
async def delete_stakeholder_assessment(assessment_id: str):
    """Delete a stakeholder assessment."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM stakeholder_assessments WHERE id = ?", (assessment_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Assessment not found")

        cursor.execute("DELETE FROM stakeholder_assessments WHERE id = ?", (assessment_id,))

        return {"message": "Assessment deleted"}


# --- Batch Assessment Endpoint ---

@router.post("/stakeholder-groups/{group_id}/assessments/batch")
async def batch_add_assessments(group_id: str, assessments: List[StakeholderAssessmentCreate]):
    """Add multiple assessments for a stakeholder group at once."""
    results = []
    errors = []

    for assessment in assessments:
        try:
            result = await add_stakeholder_assessment(group_id, assessment)
            results.append(result)
        except HTTPException as e:
            errors.append({
                "indicator_key": assessment.indicator_key,
                "error": e.detail
            })

    # Trigger insight generation on successful batch completion
    if len(results) > 0 and len(errors) == 0:
        # Get project_id from group
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT project_id FROM stakeholder_groups WHERE id = ?", (group_id,))
            row = cursor.fetchone()
            if row:
                project_id = row["project_id"]
                # Fire and forget - generate insight in background
                asyncio.create_task(_generate_impulse_insight(project_id, group_id))

    return {
        "success_count": len(results),
        "error_count": len(errors),
        "results": results,
        "errors": errors
    }


async def _generate_impulse_insight(project_id: str, group_id: str):
    """Background task to generate insight after impulse completion."""
    try:
        from .insights import generate_and_save_insight
        await generate_and_save_insight(
            project_id=project_id,
            trigger_type="impulse_completed",
            trigger_context={"group_id": group_id},
            trigger_entity_id=group_id
        )
        print(f"Generated insight for impulse completion (project={project_id}, group={group_id})")
    except Exception as e:
        print(f"Error generating impulse insight: {e}")


# --- Impulse History Endpoints ---

class ImpulseEntry(BaseModel):
    """A single impulse (assessment snapshot) for a date."""
    date: str
    average_rating: float
    ratings: dict  # indicator_key -> rating
    notes: dict  # indicator_key -> notes
    source: str  # 'manual' or 'survey'


class ImpulseHistory(BaseModel):
    """Impulse history for a stakeholder group."""
    group_id: str
    group_name: Optional[str]
    group_type: str
    impulses: List[ImpulseEntry]


@router.get("/stakeholder-groups/{group_id}/impulse-history", response_model=ImpulseHistory)
async def get_impulse_history(group_id: str, limit: int = 50):
    """
    Get the last N impulses (assessment snapshots) for a stakeholder group.
    Impulses are grouped by date.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get group info
        cursor.execute(
            """
            SELECT id, group_type, name
            FROM stakeholder_groups
            WHERE id = ?
            """,
            (group_id,)
        )
        group_row = cursor.fetchone()
        if not group_row:
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        group_data = dict_from_row(group_row)

        # Get all assessments ordered by date
        cursor.execute(
            """
            SELECT id, indicator_key, rating, notes, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
            """,
            (group_id,)
        )
        assessments = [dict_from_row(r) for r in cursor.fetchall()]

        # Group assessments by date (just the date part, not time)
        impulses_by_date = {}
        for assessment in assessments:
            # Extract just the date part
            date_str = assessment["assessed_at"][:10] if assessment["assessed_at"] else "unknown"

            if date_str not in impulses_by_date:
                impulses_by_date[date_str] = {
                    "date": date_str,
                    "ratings": {},
                    "notes": {},
                    "source": "manual"  # Default source
                }

            impulses_by_date[date_str]["ratings"][assessment["indicator_key"]] = assessment["rating"]
            if assessment["notes"]:
                impulses_by_date[date_str]["notes"][assessment["indicator_key"]] = assessment["notes"]

        # Calculate average ratings and convert to list
        impulses = []
        for date_str, impulse_data in impulses_by_date.items():
            ratings = impulse_data["ratings"]
            if ratings:
                avg = sum(ratings.values()) / len(ratings)
            else:
                avg = 0

            impulses.append(ImpulseEntry(
                date=impulse_data["date"],
                average_rating=round(avg, 1),
                ratings=impulse_data["ratings"],
                notes=impulse_data["notes"],
                source=impulse_data["source"]
            ))

        # Sort by date descending and limit
        impulses.sort(key=lambda x: x.date, reverse=True)
        impulses = impulses[:limit]

        return ImpulseHistory(
            group_id=group_id,
            group_name=group_data["name"],
            group_type=group_data["group_type"],
            impulses=impulses
        )
