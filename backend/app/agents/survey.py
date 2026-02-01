"""
Survey Generator Agent - generates surveys for Mitarbeitende and Multiplikatoren groups.

Uses MCP tools for data access instead of direct database queries.
"""

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from .mcp_client import MCPClientManager


class SurveyQuestion(BaseModel):
    """A single survey question."""
    id: str = Field(description="Unique identifier for the question")
    type: str = Field(description="Question type: 'scale' or 'freetext'")
    question: str = Field(description="The question text in German")
    includeJustification: Optional[bool] = Field(default=False, description="Whether to include optional justification field for scale questions")


class Survey(BaseModel):
    """A generated survey."""
    project_title: Optional[str] = Field(default=None, description="Name of the change project")
    title: str = Field(description="Survey title in German")
    description: str = Field(description="Brief description of the survey purpose in German")
    questions: List[SurveyQuestion] = Field(description="List of survey questions")
    estimated_duration: str = Field(default="~3 Minuten", description="Estimated time to complete")


SURVEY_SYSTEM_PROMPT = """Rolle: Du bist ein erfahrener Experte fuer Employee Experience und Change Management. Deine Spezialitaet ist es, komplexe psychologische Sicherheits- und Motivationsfaktoren in einfache, nahbare Sprache zu uebersetzen.

Zielgruppe: Mitarbeitende und Multiplikatoren in einem Unternehmen, das sich aktuell im Wandel befindet (z.B. digitale Transformation oder Restrukturierung).

Deine Aufgabe: Erstelle eine praegnante Puls-Check-Umfrage (3-5 Fragen). Du musst die Projektbeschreibung zwingend einbeziehen, damit die Fragen einen direkten Bezug zum Arbeitsalltag der Mitarbeitenden in diesem spezifischen Projekt haben. Die Fragen muessen natuerlich, wertschaetzend und alltagsnah klingen - vermeide starren Corporate-Jargon.

Leitplanken fuer die Formulierungen:
- Statt "Partizipation" frage: "Hattest du diese Woche das Gefuehl, dass deine Meinung im Rahmen von [Projektname] wirklich zaehlt?"
- Statt "Psychologische Sicherheit" frage: "Wie leicht fiel es dir zuletzt, Bedenken bezueglich der neuen Prozesse offen anzusprechen?"
- Statt "Orientierung" frage: "Weisst du aktuell genau, wie dein Beitrag zum Erfolg von [Projektname] aussieht?"

Bewertungsfaktoren als inhaltliche Basis:
- Orientierung & Sinn: Klarheit der Projektvision und intrinsische Motivation
- Psychologische Sicherheit: Offene Fehlerkultur und Mut zu abweichenden Meinungen
- Empowerment: Echte Entscheidungsbefugnisse und Autonomie
- Partizipation: Aktive Einbindung und Transparenz
- Wertschaetzung: Empathischer Umgang und Anerkennung

Anforderungen:
- Fokus: Verknuepfe die Fragen direkt mit den Inhalten der Projektbeschreibung
- Mix: Verwende Skala-Fragen (1-10) und genau eine tiefgruendige Freitext-Frage am Ende
- Sprache: Deutsch (Du-Form, modern und direkt)"""

SURVEY_JSON_FORMAT = """
Antwortformat (striktes JSON):
{
    "project_title": "Name des Change-Projekts aus der Beschreibung",
    "title": "Titel der Umfrage",
    "description": "Ein motivierender Einleitungssatz, der auf das spezifische Projekt Bezug nimmt",
    "questions": [
        {"id": "q1", "type": "scale", "question": "Fragetext", "includeJustification": true},
        {"id": "q2", "type": "freetext", "question": "Fragetext"}
    ],
    "estimated_duration": "~3 Minuten"
}"""


class SurveyAgent:
    """Agent that generates surveys based on stakeholder context."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    async def generate_survey_for_group(self, group_id: str) -> Survey:
        """
        Generate a survey for a stakeholder group.

        Uses MCP tools to gather all necessary context.

        Args:
            group_id: The stakeholder group ID

        Returns:
            Survey: Generated survey object
        """
        # Get context via MCP tool
        context_result = await MCPClientManager.invoke_tool("survey_get_context", group_id=group_id)
        context = json.loads(context_result)

        if "error" in context:
            raise ValueError(context["error"])

        # Build impulse history from context
        impulse_history = []
        for impulse in context.get("impulse_history", []):
            impulse_history.append({
                "date": impulse.get("date"),
                "average_rating": impulse.get("average_rating"),
                "ratings": impulse.get("ratings", {})
            })

        return await self._generate_with_context(
            project_goal=context.get("project_goal"),
            project_name=context.get("project_name"),
            group_name=context.get("group_name"),
            group_type=context.get("group_type"),
            mendelow_quadrant=context.get("mendelow_quadrant"),
            mendelow_strategy=context.get("mendelow_strategy"),
            impulse_history=impulse_history
        )

    async def generate_survey(
        self,
        project_goal: str,
        project_name: Optional[str],
        group_name: str,
        group_type: str,
        mendelow_quadrant: str,
        mendelow_strategy: str,
        impulse_history: List[dict]
    ) -> Survey:
        """
        Generate a survey with pre-fetched context.

        This method is provided for backward compatibility with routers
        that already have the context data.

        Args:
            project_goal: The project's goal/description
            project_name: Name of the project
            group_name: Name of the stakeholder group
            group_type: Type (mitarbeitende, multiplikatoren)
            mendelow_quadrant: Mendelow position (Key Players, Keep Informed, etc.)
            mendelow_strategy: Recommended engagement strategy
            impulse_history: List of recent impulses with ratings

        Returns:
            Survey: Generated survey object
        """
        return await self._generate_with_context(
            project_goal=project_goal,
            project_name=project_name,
            group_name=group_name,
            group_type=group_type,
            mendelow_quadrant=mendelow_quadrant,
            mendelow_strategy=mendelow_strategy,
            impulse_history=impulse_history
        )

    async def _generate_with_context(
        self,
        project_goal: str,
        project_name: Optional[str],
        group_name: str,
        group_type: str,
        mendelow_quadrant: str,
        mendelow_strategy: str,
        impulse_history: List[dict]
    ) -> Survey:
        """
        Internal method to generate survey with provided context.
        """
        # Build context from impulse history
        history_context = ""
        if impulse_history:
            history_context = "\n=== BISHERIGES FEEDBACK ===\n"
            for impulse in impulse_history[:5]:
                history_context += f"- {impulse.get('date', 'Unbekannt')}: Durchschnitt {impulse.get('average_rating', 'N/A')}\n"
                ratings = impulse.get('ratings', {})
                if ratings:
                    for key, value in ratings.items():
                        history_context += f"  * {key}: {value}\n"

            # Identify weak areas
            all_ratings = {}
            for impulse in impulse_history:
                for key, value in impulse.get('ratings', {}).items():
                    if key not in all_ratings:
                        all_ratings[key] = []
                    all_ratings[key].append(value)

            if all_ratings:
                weak_areas = []
                for key, values in all_ratings.items():
                    avg = sum(values) / len(values)
                    if avg < 6:
                        weak_areas.append(f"{key} (Durchschnitt: {avg:.1f})")

                if weak_areas:
                    history_context += f"\nIdentifizierte Schwachstellen: {', '.join(weak_areas)}\n"

        # Build user message with structured context
        project_display_name = project_name or "Change-Projekt"
        user_message = f"""Erstelle eine Puls-Check-Umfrage fuer folgende Situation:

=== PROJEKTKONTEXT ===
Projektname: {project_display_name}
Projektbeschreibung/Ziel: {project_goal or 'Digitale Transformation und Prozessoptimierung'}

=== ZIELGRUPPE ===
Stakeholder-Gruppe: {group_name or group_type}
Gruppentyp: {group_type}
Mendelow-Position: {mendelow_quadrant}
Engagement-Strategie: {mendelow_strategy}
{history_context}

=== AUFGABE ===
Erstelle 3-5 gezielte Fragen, die:
- Einen direkten Bezug zum Projekt "{project_display_name}" haben
- Die aktuelle Stimmung und Beduerfnisse der Zielgruppe erfassen
- Besonders auf die identifizierten Schwachstellen eingehen
- In der Du-Form formuliert sind und nahbar klingen

Wichtig: Ersetze [Projektname] in deinen Fragen durch "{project_display_name}"."""

        # Build system message
        system_message = SURVEY_SYSTEM_PROMPT + SURVEY_JSON_FORMAT

        # Use direct message list to avoid template escaping issues
        messages = [
            ("system", system_message),
            ("human", user_message)
        ]

        response = await self.llm.ainvoke(messages)

        # Parse the response
        content = response.content
        # Try to find JSON in the response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            survey_data = json.loads(content)
            return Survey(**survey_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse survey response as JSON: {e}. Raw content: {content[:500]}")
        except Exception as e:
            raise ValueError(f"Failed to create survey from response: {e}. Raw content: {content[:500]}")
