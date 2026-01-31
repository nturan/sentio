"""
Recommendation Generator Agent - generates actionable recommendations based on project context.
"""

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
import json


class GeneratedRecommendation(BaseModel):
    """A generated recommendation from AI."""
    title: str = Field(description="Title of the recommendation in German")
    description: str = Field(description="Detailed description of the recommendation in German")
    recommendation_type: str = Field(description="Type: 'habit', 'communication', 'workshop', 'process', or 'campaign'")
    priority: str = Field(description="Priority: 'high', 'medium', or 'low'")
    affected_groups: List[str] = Field(description="List of affected stakeholder group IDs or ['all']")
    steps: List[str] = Field(description="List of concrete action steps in German")


RECOMMENDATION_SYSTEM_PROMPT_BASE = """Du bist ein Experte fuer Change Management. Du erstellst konkrete, umsetzbare Handlungsempfehlungen basierend auf Projektkontext und Stakeholder-Feedback.

Deine Empfehlungen sollten:
1. Konkret und umsetzbar sein (nicht vage)
2. Einen klaren Bezug zu den identifizierten Schwachstellen haben
3. Die betroffenen Stakeholder-Gruppen beruecksichtigen
4. Realistische Schritte zur Umsetzung enthalten
5. Sowohl kleine Gewohnheiten als auch groessere Initiativen umfassen koennen

Typen von Empfehlungen:
- habit: Kleine taegliche/woechentliche Routinen (z.B. "5-Minuten Daily Check-in")
- communication: Kommunikationsverbesserungen (z.B. "Woechentlicher Newsletter")
- workshop: Trainings oder Workshop-Sessions (z.B. "Change Agent Training")
- process: Prozessaenderungen (z.B. "Neuer Feedback-Loop")
- campaign: Groessere Initiativen (z.B. "Anerkennungsprogramm")

Prioritaeten:
- high: Dringend, sollte sofort angegangen werden
- medium: Wichtig, aber nicht zeitkritisch
- low: Nice-to-have, wenn Ressourcen verfuegbar"""

RECOMMENDATION_JSON_FORMAT = """
Antworte IMMER im JSON-Format mit folgender Struktur:
{
    "title": "Kurzer, praegananter Titel",
    "description": "Ausfuehrliche Beschreibung der Empfehlung",
    "recommendation_type": "habit|communication|workshop|process|campaign",
    "priority": "high|medium|low",
    "affected_groups": ["group_id_1", "group_id_2"] oder ["all"],
    "steps": [
        "Schritt 1: Konkrete Handlung",
        "Schritt 2: Konkrete Handlung",
        "Schritt 3: Konkrete Handlung"
    ]
}"""


class RecommendationAgent:
    """Agent that generates actionable recommendations based on project context."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    async def generate_recommendation(
        self,
        project_goal: str,
        project_description: Optional[str],
        stakeholder_groups: List[dict],
        impulse_summaries: List[dict],
        focus: Optional[str] = None,
        rejection_context: Optional[str] = None
    ) -> GeneratedRecommendation:
        """
        Generate a single actionable recommendation.

        Args:
            project_goal: The project's goal
            project_description: Optional project description
            stakeholder_groups: List of dicts with name, type, mendelow position
            impulse_summaries: List of dicts with group, avg rating, weak indicators
            focus: Optional focus area for the recommendation
            rejection_context: Context from a rejected recommendation for regeneration

        Returns:
            GeneratedRecommendation: Generated recommendation object
        """
        # Build stakeholder context
        stakeholder_context = ""
        if stakeholder_groups:
            stakeholder_context = "\nStakeholder-Gruppen:\n"
            for group in stakeholder_groups:
                stakeholder_context += f"- {group.get('name', 'Unbenannt')} ({group.get('type', 'Unbekannt')}): "
                stakeholder_context += f"Macht={group.get('power_level', '?')}, Interesse={group.get('interest_level', '?')}\n"

        # Build impulse context
        impulse_context = ""
        if impulse_summaries:
            impulse_context = "\nImpulse-Uebersicht (letzte Bewertungen):\n"
            weak_areas = []
            for summary in impulse_summaries:
                group_name = summary.get('group_name', 'Unbekannt')
                avg = summary.get('average_rating')
                trend = summary.get('trend', '')
                trend_symbol = '(aufwaerts)' if trend == 'up' else '(abwaerts)' if trend == 'down' else '(stabil)'

                if avg is not None:
                    impulse_context += f"- {group_name}: Durchschnitt {avg:.1f} {trend_symbol}\n"

                    # Collect weak indicators
                    weak_indicators = summary.get('weak_indicators', [])
                    for indicator in weak_indicators:
                        weak_areas.append(f"{indicator.get('name', 'Unbekannt')} ({group_name}): {indicator.get('rating', '?')}")

            if weak_areas:
                impulse_context += "\nSchwachstellen:\n"
                for area in weak_areas[:5]:  # Limit to top 5
                    impulse_context += f"- {area}\n"

        # Build rejection context if regenerating
        rejection_prompt = ""
        if rejection_context:
            rejection_prompt = f"""
WICHTIG: Die vorherige Empfehlung wurde abgelehnt. Hier ist der Grund:
"{rejection_context}"

Bitte generiere eine ALTERNATIVE Empfehlung, die diesen Einwand beruecksichtigt. Die neue Empfehlung sollte:
- Das gleiche Problem adressieren, aber auf eine andere Weise
- Den genannten Ablehnungsgrund beruecksichtigen
- Realistischer und umsetzbar sein"""

        # Build focus context
        focus_prompt = ""
        if focus:
            focus_prompt = f"\n\nFOKUS: Der Benutzer moechte sich auf folgenden Bereich konzentrieren: {focus}"

        # Build user message
        user_message = f"""Erstelle eine konkrete Handlungsempfehlung fuer folgendes Change-Projekt:

Projektziel: {project_goal or 'Nicht definiert'}
{f'Projektbeschreibung: {project_description}' if project_description else ''}
{stakeholder_context}
{impulse_context}
{focus_prompt}

Erstelle EINE gezielte, umsetzbare Empfehlung mit 3-5 konkreten Schritten.

Bei der Auswahl der affected_groups: Verwende die tatsaechlichen Gruppen-IDs oder "all" wenn alle betroffen sind."""

        # Build system prompt
        system_parts = [RECOMMENDATION_SYSTEM_PROMPT_BASE]
        if rejection_prompt:
            system_parts.append(rejection_prompt)
        system_parts.append(RECOMMENDATION_JSON_FORMAT)
        system_message = "\n".join(system_parts)

        # Use direct message list instead of ChatPromptTemplate to avoid escaping issues
        messages = [
            ("system", system_message),
            ("human", user_message)
        ]

        response = await self.llm.ainvoke(messages)

        # Parse the response
        try:
            content = response.content
            # Extract JSON from the response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            recommendation_data = json.loads(content)
            return GeneratedRecommendation(**recommendation_data)
        except Exception as e:
            print(f"Failed to parse recommendation response: {e}")
            print(f"Raw response: {response.content}")
            # Return a default recommendation if parsing fails
            return GeneratedRecommendation(
                title="Kommunikationsroutine einfuehren",
                description="Etablieren Sie eine regelmaessige Kommunikationsroutine, um alle Stakeholder auf dem Laufenden zu halten.",
                recommendation_type="communication",
                priority="medium",
                affected_groups=["all"],
                steps=[
                    "Format und Frequenz definieren (z.B. woechentlicher Newsletter)",
                    "Verantwortlichen festlegen",
                    "Erste Kommunikation versenden"
                ]
            )
