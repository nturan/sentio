"""
Survey Generator Agent - generates surveys for Mitarbeitende and Multiplikatoren groups.
"""

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
import json


class SurveyQuestion(BaseModel):
    """A single survey question."""
    id: str = Field(description="Unique identifier for the question")
    type: str = Field(description="Question type: 'scale' or 'freetext'")
    question: str = Field(description="The question text in German")
    includeJustification: Optional[bool] = Field(default=False, description="Whether to include optional justification field for scale questions")


class Survey(BaseModel):
    """A generated survey."""
    title: str = Field(description="Survey title in German")
    description: str = Field(description="Brief description of the survey purpose in German")
    questions: List[SurveyQuestion] = Field(description="List of survey questions")
    estimated_duration: str = Field(default="~3 Minuten", description="Estimated time to complete")


SURVEY_SYSTEM_PROMPT = """Du bist ein Experte fuer Change Management Umfragen. Du erstellst kurze, praegende Puls-Check Umfragen fuer Mitarbeitende und Multiplikatoren.

Deine Aufgabe:
1. Erstelle eine kurze Umfrage (3-5 Fragen) basierend auf dem Kontext
2. Verwende die Bewertungsfaktoren als Inspiration
3. Fokussiere auf Bereiche, die laut Impulse-Historie Verbesserungspotenzial haben
4. Formuliere Fragen klar, neutral und auf Deutsch
5. Mische Skala-Fragen (1-10) mit mindestens einer Freitext-Frage

Bewertungsfaktoren zur Orientierung:
- Orientierung & Sinn: Klarheit der Projektvision und intrinsische Motivation
- Psychologische Sicherheit: Offene Fehlerkultur und Mut zu abweichenden Meinungen
- Empowerment: Echte Entscheidungsbefugnisse und Autonomie
- Partizipation: Aktive Einbindung und Transparenz
- Wertschaetzung: Empathischer Umgang und Anerkennung

Antwortformat: JSON mit folgender Struktur:
{{
    "title": "Umfragetitel",
    "description": "Kurze Beschreibung",
    "questions": [
        {{"id": "q1", "type": "scale", "question": "Fragetext", "includeJustification": true}},
        {{"id": "q2", "type": "freetext", "question": "Fragetext"}}
    ],
    "estimated_duration": "~3 Minuten"
}}"""


class SurveyAgent:
    """Agent that generates surveys based on stakeholder context."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.parser = JsonOutputParser(pydantic_object=Survey)

    async def generate_survey(
        self,
        project_goal: str,
        group_name: str,
        group_type: str,
        mendelow_quadrant: str,
        mendelow_strategy: str,
        impulse_history: List[dict]
    ) -> Survey:
        """
        Generate a survey based on the stakeholder group context.

        Args:
            project_goal: The project's goal
            group_name: Name of the stakeholder group
            group_type: Type (mitarbeitende, multiplikatoren)
            mendelow_quadrant: Mendelow position (Key Players, Keep Informed, etc.)
            mendelow_strategy: Recommended engagement strategy
            impulse_history: List of recent impulses with ratings

        Returns:
            Survey: Generated survey object
        """
        # Build context from impulse history
        history_context = ""
        if impulse_history:
            history_context = "\nLetzte Impulse:\n"
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
                    history_context += f"\nSchwachstellen: {', '.join(weak_areas)}\n"

        # Build prompt
        user_message = f"""Erstelle eine Puls-Check Umfrage fuer folgende Stakeholder-Gruppe:

Projektziel: {project_goal or 'Nicht definiert'}

Stakeholder-Gruppe:
- Name: {group_name or group_type}
- Typ: {group_type}
- Mendelow-Position: {mendelow_quadrant}
- Empfohlene Strategie: {mendelow_strategy}
{history_context}

Erstelle 3-5 gezielte Fragen, die helfen, die aktuelle Stimmung und Beduerfnisse dieser Gruppe zu erfassen. Beruecksichtige besonders die identifizierten Schwachstellen."""

        prompt = ChatPromptTemplate.from_messages([
            ("system", SURVEY_SYSTEM_PROMPT),
            ("human", "{input}")
        ])

        chain = prompt | self.llm

        response = await chain.ainvoke({"input": user_message})

        # Parse the response
        try:
            # Extract JSON from the response
            content = response.content
            # Try to find JSON in the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            survey_data = json.loads(content)
            return Survey(**survey_data)
        except Exception as e:
            # Return a default survey if parsing fails
            print(f"Failed to parse survey response: {e}")
            return Survey(
                title=f"Puls-Check fuer {group_name or group_type}",
                description="Kurze Umfrage zur aktuellen Projektsituation",
                questions=[
                    SurveyQuestion(
                        id="q1",
                        type="scale",
                        question="Wie klar ist Ihnen der Nutzen der aktuellen Veraenderung?",
                        includeJustification=True
                    ),
                    SurveyQuestion(
                        id="q2",
                        type="scale",
                        question="Wie gut fuehlen Sie sich in Entscheidungen eingebunden?",
                        includeJustification=True
                    ),
                    SurveyQuestion(
                        id="q3",
                        type="freetext",
                        question="Was wuerden Sie sich fuer die naechsten Wochen wuenschen?"
                    )
                ],
                estimated_duration="~3 Minuten"
            )
