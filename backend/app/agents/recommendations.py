"""
Recommendation Generator Agent - generates actionable recommendations based on project context.

Uses MCP tools for data access instead of direct database queries.
"""

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from .mcp_client import MCPClientManager
from ..prompts import load_prompt


class GeneratedRecommendation(BaseModel):
    """A generated recommendation from AI."""
    title: str = Field(description="Title of the recommendation")
    description: str = Field(description="Detailed description of the recommendation")
    recommendation_type: str = Field(description="Type: 'habit', 'communication', 'workshop', 'process', or 'campaign'")
    priority: str = Field(description="Priority: 'high', 'medium', or 'low'")
    affected_groups: List[str] = Field(description="List of affected stakeholder group IDs or ['all']")
    steps: List[str] = Field(description="List of concrete action steps")


class RecommendationAgent:
    """Agent that generates actionable recommendations based on project context."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    async def _get_project_context(self, project_id: str) -> dict:
        """
        Gather project context using MCP tools.

        Args:
            project_id: The project ID to get context for

        Returns:
            Dict containing project_goal, project_description, stakeholder_groups, impulse_summaries
        """
        try:
            # Get project info
            project_result = await MCPClientManager.invoke_tool("project_get", project_id=project_id)
            project = json.loads(project_result)
            if "error" in project:
                raise ValueError(f"Project not found: {project_id}")

            # Get stakeholder groups
            groups_result = await MCPClientManager.invoke_tool("stakeholder_group_list", project_id=project_id)
            groups = json.loads(groups_result)

            # Get impulse history for each group
            impulse_summaries = []
            for group in groups:
                history_result = await MCPClientManager.invoke_tool("impulse_history_get", group_id=group["id"])
                history = json.loads(history_result)

                if history.get("total_assessments", 0) > 0:
                    impulse_summaries.append({
                        "group_id": group["id"],
                        "group_name": history.get("group_name") or group.get("name") or group["group_type"],
                        "average_rating": history.get("average_rating"),
                        "trend": history.get("trend", "stable"),
                        "weak_indicators": history.get("weak_indicators", [])
                    })

            return {
                "project_goal": project.get("goal"),
                "project_description": None,
                "stakeholder_groups": [
                    {
                        "id": g["id"],
                        "name": g.get("name") or g["group_type"],
                        "type": g["group_type"],
                        "power_level": g["power_level"],
                        "interest_level": g["interest_level"]
                    }
                    for g in groups
                ],
                "impulse_summaries": impulse_summaries
            }

        except Exception as e:
            print(f"Error getting project context via MCP: {e}")
            raise

    async def generate_recommendation(
        self,
        project_id: str,
        focus: Optional[str] = None,
        rejection_context: Optional[str] = None
    ) -> GeneratedRecommendation:
        """
        Generate a single actionable recommendation.

        Args:
            project_id: The project ID to generate a recommendation for
            focus: Optional focus area for the recommendation
            rejection_context: Context from a rejected recommendation for regeneration

        Returns:
            GeneratedRecommendation: Generated recommendation object
        """
        # Get context via MCP tools
        context = await self._get_project_context(project_id)

        return await self._generate_with_context(
            project_goal=context["project_goal"],
            project_description=context["project_description"],
            stakeholder_groups=context["stakeholder_groups"],
            impulse_summaries=context["impulse_summaries"],
            focus=focus,
            rejection_context=rejection_context
        )

    async def generate_recommendation_with_context(
        self,
        project_goal: str,
        project_description: Optional[str],
        stakeholder_groups: List[dict],
        impulse_summaries: List[dict],
        focus: Optional[str] = None,
        rejection_context: Optional[str] = None
    ) -> GeneratedRecommendation:
        """
        Generate a recommendation with pre-fetched context.

        This method is provided for backward compatibility with routers
        that already have the context data.

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
        return await self._generate_with_context(
            project_goal=project_goal,
            project_description=project_description,
            stakeholder_groups=stakeholder_groups,
            impulse_summaries=impulse_summaries,
            focus=focus,
            rejection_context=rejection_context
        )

    async def _generate_with_context(
        self,
        project_goal: str,
        project_description: Optional[str],
        stakeholder_groups: List[dict],
        impulse_summaries: List[dict],
        focus: Optional[str] = None,
        rejection_context: Optional[str] = None
    ) -> GeneratedRecommendation:
        """
        Internal method to generate recommendation with provided context.
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
            rejection_template = load_prompt("recommendations", "rejection_context")
            rejection_prompt = rejection_template.format(reason=rejection_context)

        # Build focus context
        focus_prompt = ""
        if focus:
            focus_prompt = f"\n\nFOKUS: Der Benutzer moechte sich auf folgenden Bereich konzentrieren: {focus}"

        # Build user message
        user_message = f"""Erstelle eine konkrete Handlungsempfehlung fuer folgendes Change-Projekt:

=== PROJEKTKONTEXT ===
Projektziel: {project_goal or 'Nicht definiert'}
{f'Projektbeschreibung: {project_description}' if project_description else ''}

=== STAKEHOLDER-GRUPPEN ===
{stakeholder_context if stakeholder_context else 'Keine Stakeholder-Gruppen definiert.'}

=== STAKEHOLDER-FEEDBACK & SCHWACHSTELLEN ===
{impulse_context if impulse_context else 'Noch kein Feedback erfasst.'}
{focus_prompt}

=== AUFGABE ===
Erstelle EINE gezielte, umsetzbare Empfehlung mit 3-5 konkreten Schritten.
Die Empfehlung soll direkt auf die identifizierten Schwachstellen eingehen und die betroffenen Stakeholder-Gruppen beruecksichtigen.

Bei der Auswahl der affected_groups: Verwende die tatsaechlichen Gruppen-IDs oder "all" wenn alle betroffen sind."""

        # Build system prompt from localized prompts
        system_prompt = load_prompt("recommendations", "system")
        json_format = load_prompt("recommendations", "json_format")
        system_parts = [system_prompt]
        if rejection_prompt:
            system_parts.append(rejection_prompt)
        system_parts.append(json_format)
        system_message = "\n".join(system_parts)

        # Use direct message list instead of ChatPromptTemplate to avoid escaping issues
        messages = [
            ("system", system_message),
            ("human", user_message)
        ]

        response = await self.llm.ainvoke(messages)

        # Parse the response
        content = response.content
        # Extract JSON from the response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        try:
            recommendation_data = json.loads(content)
            return GeneratedRecommendation(**recommendation_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse recommendation response as JSON: {e}. Raw content: {content[:500]}")
        except Exception as e:
            raise ValueError(f"Failed to create recommendation from response: {e}. Raw content: {content[:500]}")
