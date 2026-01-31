"""
Survey Router - handles survey generation and markdown export.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid
import os

from ..database import get_connection, dict_from_row
from ..agents.survey import SurveyAgent, Survey, SurveyQuestion

router = APIRouter(prefix="/api", tags=["surveys"])

# Initialize survey agent
survey_agent = SurveyAgent()

# Get the surveys directory path (at repo root)
SURVEYS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'surveys'))


# --- Pydantic Models ---

class SurveyQuestionModel(BaseModel):
    id: str
    type: str  # 'scale' or 'freetext'
    question: str
    includeJustification: Optional[bool] = False


class SurveyModel(BaseModel):
    title: str
    description: str
    questions: List[SurveyQuestionModel]
    stakeholder_group_id: Optional[str] = None
    estimated_duration: Optional[str] = "~3 Minuten"


class GenerateSurveyResponse(BaseModel):
    survey: SurveyModel


class SaveSurveyRequest(BaseModel):
    survey: SurveyModel


class SaveSurveyResponse(BaseModel):
    file_path: str
    survey_id: str


# --- Endpoints ---

@router.post("/stakeholder-groups/{group_id}/generate-survey", response_model=GenerateSurveyResponse)
async def generate_survey(group_id: str):
    """
    Generate a survey for a stakeholder group using AI.
    Only available for Mitarbeitende and Multiplikatoren groups.
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get group info
        cursor.execute(
            """
            SELECT sg.id, sg.project_id, sg.group_type, sg.name, sg.power_level, sg.interest_level,
                   p.goal as project_goal
            FROM stakeholder_groups sg
            JOIN projects p ON sg.project_id = p.id
            WHERE sg.id = ?
            """,
            (group_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        group = dict_from_row(row)

        # Verify group type allows surveys
        if group["group_type"] == "fuehrungskraefte":
            raise HTTPException(
                status_code=400,
                detail="Surveys are only available for Mitarbeitende and Multiplikatoren groups"
            )

        # Get Mendelow info
        mendelow_map = {
            ("high", "high"): ("Key Players", "Eng einbinden und aktiv managen"),
            ("high", "low"): ("Keep Satisfied", "Zufrieden halten, regelmaessig informieren"),
            ("low", "high"): ("Keep Informed", "Gut informiert halten"),
            ("low", "low"): ("Monitor", "Beobachten mit minimalem Aufwand"),
        }
        mendelow_key = (group["power_level"], group["interest_level"])
        mendelow_quadrant, mendelow_strategy = mendelow_map.get(mendelow_key, ("Unknown", ""))

        # Get impulse history
        cursor.execute(
            """
            SELECT indicator_key, rating, notes, assessed_at
            FROM stakeholder_assessments
            WHERE stakeholder_group_id = ?
            ORDER BY assessed_at DESC
            """,
            (group_id,)
        )
        assessments = [dict_from_row(r) for r in cursor.fetchall()]

        # Group by date
        impulses_by_date = {}
        for assessment in assessments:
            date_str = assessment["assessed_at"][:10] if assessment["assessed_at"] else "unknown"
            if date_str not in impulses_by_date:
                impulses_by_date[date_str] = {"date": date_str, "ratings": {}}
            impulses_by_date[date_str]["ratings"][assessment["indicator_key"]] = assessment["rating"]

        # Calculate averages
        impulse_history = []
        for date_str, data in sorted(impulses_by_date.items(), reverse=True)[:5]:
            ratings = data["ratings"]
            avg = sum(ratings.values()) / len(ratings) if ratings else 0
            impulse_history.append({
                "date": data["date"],
                "average_rating": round(avg, 1),
                "ratings": ratings
            })

    # Generate survey using agent
    try:
        survey = await survey_agent.generate_survey(
            project_goal=group["project_goal"],
            group_name=group["name"],
            group_type=group["group_type"],
            mendelow_quadrant=mendelow_quadrant,
            mendelow_strategy=mendelow_strategy,
            impulse_history=impulse_history
        )

        # Convert to response model
        return GenerateSurveyResponse(
            survey=SurveyModel(
                title=survey.title,
                description=survey.description,
                questions=[
                    SurveyQuestionModel(
                        id=q.id,
                        type=q.type,
                        question=q.question,
                        includeJustification=q.includeJustification
                    )
                    for q in survey.questions
                ],
                stakeholder_group_id=group_id,
                estimated_duration=survey.estimated_duration
            )
        )
    except Exception as e:
        print(f"Error generating survey: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate survey: {str(e)}")


@router.post("/stakeholder-groups/{group_id}/save-survey", response_model=SaveSurveyResponse)
async def save_survey(group_id: str, request: SaveSurveyRequest):
    """
    Save a survey as markdown file.
    """
    survey = request.survey

    with get_connection() as conn:
        cursor = conn.cursor()

        # Get group and project info
        cursor.execute(
            """
            SELECT sg.id, sg.project_id, sg.group_type, sg.name, p.name as project_name
            FROM stakeholder_groups sg
            JOIN projects p ON sg.project_id = p.id
            WHERE sg.id = ?
            """,
            (group_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Stakeholder group not found")

        group = dict_from_row(row)

        # Create surveys directory structure
        project_dir = os.path.join(SURVEYS_DIR, group["project_id"])
        os.makedirs(project_dir, exist_ok=True)

        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = (group["name"] or group["group_type"]).replace(" ", "_").replace("/", "-")
        filename = f"{timestamp}_{safe_name}.md"
        file_path = os.path.join(project_dir, filename)

        # Generate markdown content
        markdown = generate_survey_markdown(
            survey=survey,
            group_name=group["name"] or group["group_type"],
            created_date=datetime.utcnow().strftime("%d.%m.%Y")
        )

        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown)

        # Store in database
        survey_id = str(uuid.uuid4())
        cursor.execute(
            """
            INSERT INTO surveys (id, project_id, stakeholder_group_id, title, description, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (survey_id, group["project_id"], group_id, survey.title, survey.description, file_path, datetime.utcnow().isoformat())
        )

        # Return relative path from repo root for display
        relative_path = os.path.relpath(file_path, os.path.join(SURVEYS_DIR, '..'))

        return SaveSurveyResponse(
            file_path=relative_path,
            survey_id=survey_id
        )


def generate_survey_markdown(survey: SurveyModel, group_name: str, created_date: str) -> str:
    """Generate markdown content for a survey."""
    lines = [
        f"# {survey.title}",
        "",
        f"**Zielgruppe:** {group_name}",
        f"**Erstellt:** {created_date}",
        f"**Geschaetzte Dauer:** {survey.estimated_duration}",
        "",
        "---",
        "",
        "## Fragen",
        ""
    ]

    for i, question in enumerate(survey.questions, 1):
        if question.type == "scale":
            lines.extend([
                f"### {i}. {question.question} (Skala 1-10)",
                "",
                "Bitte bewerten Sie auf einer Skala von 1 (sehr niedrig) bis 10 (sehr hoch).",
                "",
                "[ ] 1  [ ] 2  [ ] 3  [ ] 4  [ ] 5  [ ] 6  [ ] 7  [ ] 8  [ ] 9  [ ] 10",
                ""
            ])
            if question.includeJustification:
                lines.extend([
                    "**Optional:** Was hat zu dieser Bewertung gefuehrt?",
                    "_________________________________________",
                    ""
                ])
        else:  # freetext
            lines.extend([
                f"### {i}. {question.question} (Freitext)",
                "",
                "_________________________________________",
                "_________________________________________",
                "_________________________________________",
                ""
            ])

    lines.extend([
        "---",
        "",
        "*Diese Umfrage wurde mit Sentio erstellt.*"
    ])

    return "\n".join(lines)
