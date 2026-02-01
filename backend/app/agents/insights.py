"""
Insights Generator Agent - generates actionable insights based on project context.

Uses MCP tools for data access instead of direct database queries.
"""

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from .mcp_client import MCPClientManager
from ..prompts import load_prompt, load_constants


class GeneratedInsight(BaseModel):
    """A generated insight from AI."""
    title: str = Field(description="Concise title of the insight")
    content: str = Field(description="Detailed explanation with data references")
    insight_type: str = Field(description="Type: 'trend', 'opportunity', 'warning', 'success', or 'pattern'")
    priority: str = Field(description="Priority: 'high', 'medium', or 'low'")
    related_groups: List[str] = Field(description="List of related stakeholder group IDs or []")
    related_recommendations: List[str] = Field(description="List of related recommendation IDs or []")
    action_suggestions: List[str] = Field(description="List of 2-3 concrete action suggestions")


class InsightsAgent:
    """Agent that generates insights based on project context."""

    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)

    async def _get_insights_context(self, project_id: str) -> dict:
        """
        Gather comprehensive context for insight generation using MCP tools.

        Args:
            project_id: The project ID to get context for

        Returns:
            Dict containing project_goal, stakeholder_groups, impulse_summaries, recommendations
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
                        "weak_indicators": history.get("weak_indicators", []),
                        "assessment_count": history.get("total_assessments", 0)
                    })

            # Get recommendations
            recommendations_result = await MCPClientManager.invoke_tool("recommendation_list", project_id=project_id)
            recommendations = json.loads(recommendations_result)

            # Get existing insights to avoid duplicates
            existing_insights_result = await MCPClientManager.invoke_tool("insight_list", project_id=project_id)
            existing_insights = json.loads(existing_insights_result)

            return {
                "project_goal": project.get("goal"),
                "project_name": project.get("name"),
                "stakeholder_groups": [
                    {
                        "id": g["id"],
                        "name": g.get("name") or g["group_type"],
                        "type": g["group_type"],
                        "power_level": g["power_level"],
                        "interest_level": g["interest_level"],
                        "mendelow_quadrant": g.get("mendelow_quadrant", "Unknown"),
                        "mendelow_strategy": g.get("mendelow_strategy", "")
                    }
                    for g in groups
                ],
                "impulse_summaries": impulse_summaries,
                "recommendations": [
                    {
                        "id": r["id"],
                        "title": r["title"],
                        "status": r["status"],
                        "type": r["recommendation_type"],
                        "priority": r["priority"]
                    }
                    for r in recommendations
                ],
                "existing_insights": [
                    {
                        "title": i["title"],
                        "insight_type": i["insight_type"],
                        "content": i["content"][:200] + "..." if len(i.get("content", "")) > 200 else i.get("content", "")
                    }
                    for i in existing_insights[:10]  # Last 10 insights
                ]
            }

        except Exception as e:
            print(f"Error getting insights context via MCP: {e}")
            raise

    async def generate_insight(
        self,
        project_id: str,
        trigger_type: str = "manual",
        trigger_context: Optional[dict] = None
    ) -> GeneratedInsight:
        """
        Generate a single insight based on project context.

        Args:
            project_id: The project ID to generate an insight for
            trigger_type: How the insight was triggered ('manual', 'impulse_completed', 'recommendation_completed')
            trigger_context: Optional context about the trigger (e.g., group_id or recommendation_id)

        Returns:
            GeneratedInsight: Generated insight object
        """
        # Get context via MCP tools
        context = await self._get_insights_context(project_id)

        return await self._generate_with_context(
            project_goal=context["project_goal"],
            project_name=context["project_name"],
            stakeholder_groups=context["stakeholder_groups"],
            impulse_summaries=context["impulse_summaries"],
            recommendations=context["recommendations"],
            existing_insights=context.get("existing_insights", []),
            trigger_type=trigger_type,
            trigger_context=trigger_context
        )

    async def _generate_with_context(
        self,
        project_goal: str,
        project_name: Optional[str],
        stakeholder_groups: List[dict],
        impulse_summaries: List[dict],
        recommendations: List[dict],
        existing_insights: List[dict],
        trigger_type: str = "manual",
        trigger_context: Optional[dict] = None
    ) -> GeneratedInsight:
        """
        Internal method to generate insight with provided context.
        """
        # Load localized labels
        labels = load_prompt("insights", "labels")
        status_labels = load_prompt("insights", "status_labels")
        sections = load_prompt("insights", "sections")
        triggers = load_prompt("insights", "triggers")
        user_message_template = load_prompt("insights", "user_message")

        # Build stakeholder context
        stakeholder_context = ""
        if stakeholder_groups:
            stakeholder_context = f"\n{sections['stakeholder_groups']}\n"
            for group in stakeholder_groups:
                stakeholder_context += f"- {group.get('name', labels['unnamed'])} ({group.get('type', labels['unknown'])}): "
                stakeholder_context += f"{labels['power']}={group.get('power_level', '?')}, {labels['interest']}={group.get('interest_level', '?')}, "
                stakeholder_context += f"{labels['position']}={group.get('mendelow_quadrant', '?')}\n"

        # Build impulse context
        impulse_context = ""
        if impulse_summaries:
            impulse_context = f"\n{sections['impulse_overview']}\n"
            for summary in impulse_summaries:
                group_name = summary.get('group_name', labels['unknown'])
                avg = summary.get('average_rating')
                trend = summary.get('trend', '')
                trend_symbol = labels['trend_up'] if trend == 'up' else labels['trend_down'] if trend == 'down' else labels['trend_stable']
                count = summary.get('assessment_count', 0)

                if avg is not None:
                    impulse_context += f"- {group_name}: {labels['average']} {avg:.1f} {trend_symbol}, {count} {labels['assessments']}\n"

                    # List weak indicators
                    weak_indicators = summary.get('weak_indicators', [])
                    if weak_indicators:
                        for indicator in weak_indicators[:3]:
                            impulse_context += f"  * {labels['weak']}: {indicator.get('name', labels['unknown'])} ({indicator.get('rating', '?')})\n"

        # Build recommendations context
        recommendations_context = ""
        if recommendations:
            recommendations_context = f"\n{sections['recommendations']}\n"
            status_groups_dict = {}
            for rec in recommendations:
                status = rec.get('status', 'unknown')
                if status not in status_groups_dict:
                    status_groups_dict[status] = []
                status_groups_dict[status].append(rec)

            for status, recs in status_groups_dict.items():
                status_label = status_labels.get(status, status)
                recommendations_context += f"- {status_label}: {len(recs)} recommendations\n"
                for rec in recs[:2]:  # Show first 2 per status
                    recommendations_context += f"  * {rec.get('title', labels['unknown'])} ({rec.get('priority', '?')} {labels['priority_label']})\n"

        # Build existing insights context (for duplicate avoidance)
        existing_insights_context = ""
        if existing_insights:
            existing_insights_context = f"\n{sections['existing_insights']}\n"
            for insight in existing_insights:
                existing_insights_context += f"- [{insight.get('insight_type', '?')}] {insight.get('title', labels['unknown'])}\n"
                if insight.get('content'):
                    existing_insights_context += f"  {sections['content']} {insight['content']}\n"

        # Build trigger context
        trigger_prompt = ""
        if trigger_type == "impulse_completed":
            group_id = trigger_context.get("group_id") if trigger_context else None
            if group_id:
                trigger_prompt = "\n\n" + triggers['impulse_completed'].format(group_id=group_id)
        elif trigger_type == "recommendation_completed":
            rec_id = trigger_context.get("recommendation_id") if trigger_context else None
            if rec_id:
                trigger_prompt = "\n\n" + triggers['recommendation_completed'].format(rec_id=rec_id)

        # Build user message from template
        project_display_name = project_name or labels['default_project']
        user_message = user_message_template.format(
            project_name=project_display_name,
            project_goal=project_goal or labels['not_defined'],
            stakeholder_context=stakeholder_context if stakeholder_context else labels['not_defined'],
            impulse_context=impulse_context if impulse_context else labels['not_defined'],
            recommendations_context=recommendations_context if recommendations_context else labels['not_defined'],
            existing_insights_context=existing_insights_context if existing_insights_context else labels['not_defined'],
            trigger_prompt=trigger_prompt
        )

        # Build system prompt from localized prompts
        system_prompt = load_prompt("insights", "system")
        json_format = load_prompt("insights", "json_format")
        system_message = system_prompt + json_format

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
            insight_data = json.loads(content)
            return GeneratedInsight(**insight_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse insight response as JSON: {e}. Raw content: {content[:500]}")
        except Exception as e:
            raise ValueError(f"Failed to create insight from response: {e}. Raw content: {content[:500]}")
