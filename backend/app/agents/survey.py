"""
Survey Generator Agent - generates surveys for Mitarbeitende and Multiplikatoren groups.

Uses MCP tools for data access instead of direct database queries.
"""

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from .mcp_client import MCPClientManager
from ..prompts import load_prompt


class SurveyQuestion(BaseModel):
    """A single survey question."""
    id: str = Field(description="Unique identifier for the question")
    type: str = Field(description="Question type: 'scale' or 'freetext'")
    question: str = Field(description="The question text")
    includeJustification: Optional[bool] = Field(default=False, description="Whether to include optional justification field for scale questions")


class Survey(BaseModel):
    """A generated survey."""
    project_title: Optional[str] = Field(default=None, description="Name of the change project")
    title: str = Field(description="Survey title")
    description: str = Field(description="Brief description of the survey purpose")
    questions: List[SurveyQuestion] = Field(description="List of survey questions")
    estimated_duration: str = Field(default="~3 minutes", description="Estimated time to complete")


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
        # Load localized labels
        history_header = load_prompt("survey", "history_header")
        history_line_template = load_prompt("survey", "history_line")
        history_rating_template = load_prompt("survey", "history_rating")
        history_weaknesses_template = load_prompt("survey", "history_weaknesses")
        history_average_label = load_prompt("survey", "history_average_label")
        history_unknown_date = load_prompt("survey", "history_unknown_date")

        # Build context from impulse history
        history_context = ""
        if impulse_history:
            history_context = "\n" + history_header
            for impulse in impulse_history[:5]:
                date = impulse.get('date', history_unknown_date)
                avg = impulse.get('average_rating', 'N/A')
                history_context += history_line_template.format(date=date, average=avg) + "\n"
                ratings = impulse.get('ratings', {})
                if ratings:
                    for key, value in ratings.items():
                        history_context += history_rating_template.format(key=key, value=value) + "\n"

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
                        weak_areas.append(f"{key} ({history_average_label}: {avg:.1f})")

                if weak_areas:
                    history_context += "\n" + history_weaknesses_template.format(weaknesses=", ".join(weak_areas)) + "\n"

        # Build user message from localized template
        project_display_name = project_name or "Change Project"
        default_goal = "Digital transformation and process optimization"
        user_message_template = load_prompt("survey", "user_message")
        user_message = user_message_template.format(
            project_name=project_display_name,
            project_goal=project_goal or default_goal,
            group_name=group_name or group_type,
            group_type=group_type,
            mendelow_quadrant=mendelow_quadrant,
            mendelow_strategy=mendelow_strategy,
            history_context=history_context
        )

        # Build system message from localized prompts
        system_prompt = load_prompt("survey", "system")
        json_format = load_prompt("survey", "json_format")
        system_message = system_prompt + json_format

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
