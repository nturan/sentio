"""
Generator Chat Agent - Interactive chat within generator modals.

This agent helps users refine generated content (recommendations, insights, etc.)
by answering questions about project context and making modifications to the canvas.
"""

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from .mcp_client import MCPClientManager
from .knowledge import KnowledgeAgent
from langchain_core.tools import tool
from ..prompts import load_prompt
import json
from typing import Optional


class GeneratorChatAgent:
    """Agent for interactive chat within generator modals."""

    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.knowledge_agent = knowledge_agent
        self._tools = None

    async def _get_tools(self, project_id: str):
        """Get tools for the generator chat agent."""
        # Create the knowledge retrieval tool with closure over project_id
        knowledge_agent = self.knowledge_agent

        @tool
        async def retrieve_knowledge(query: str) -> str:
            """
            Search for facts, documents, or context about the project from the knowledge base.
            Use this when you need information from uploaded documents.
            """
            result = await knowledge_agent.retrieve_context(query, project_id)
            return result.get("context", "No information found.")

        # Get MCP tools for data retrieval
        mcp_tools = await MCPClientManager.get_tools_by_names([
            "insight_list",
            "recommendation_list",
            "impulse_history_get",
            "document_retrieve_context",
            "stakeholder_group_list"
        ])

        return [retrieve_knowledge] + mcp_tools

    def _build_system_prompt(self, generator_type: str, canvas_data: dict, project_id: str) -> str:
        """Build system prompt with canvas context and project ID."""
        # Load generator types from localized prompts
        prompt_data = load_prompt("generator_chat", "generator_types")
        generator_type_label = prompt_data.get(generator_type, generator_type)

        # Format canvas data as readable JSON
        canvas_json = json.dumps(canvas_data, indent=2, ensure_ascii=False)

        # Load system prompt template
        prompt_template = load_prompt("generator_chat", "system")
        return prompt_template.format(
            generator_type_label=generator_type_label,
            canvas_json=canvas_json,
            project_id=project_id
        )

    async def chat(
        self,
        message: str,
        project_id: str,
        generator_type: str,
        canvas_data: dict,
        history: list
    ):
        """
        Chat with the agent using streaming.

        Args:
            message: The user's message
            project_id: The project ID for context
            generator_type: Type of generator ('recommendation', 'insight', 'survey')
            canvas_data: Current state of the canvas form
            history: List of previous messages [{role: 'user'|'assistant', content: '...'}]

        Yields:
            String chunks of the response
        """
        # Build system prompt with canvas context and project ID
        system_prompt = self._build_system_prompt(generator_type, canvas_data, project_id)

        # Add tool usage instructions from localized prompt
        tool_usage = load_prompt("generator_chat", "tool_usage")
        system_prompt += f"\n\n{tool_usage.format(project_id=project_id)}"

        # Get tools
        tools = await self._get_tools(project_id)

        # Create agent with updated prompt
        agent_executor = create_react_agent(self.llm, tools, prompt=system_prompt)

        # Convert simple history to LangChain messages
        chat_history = []
        for msg in history:
            if msg.get("role") == "user":
                chat_history.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "assistant":
                # Strip any previous canvas updates from history to avoid confusion
                content = msg.get("content", "")
                if "<<CANVAS_UPDATE>>" in content:
                    content = content.split("<<CANVAS_UPDATE>>")[0].strip()
                chat_history.append(AIMessage(content=content))

        # Add current message
        chat_history.append(HumanMessage(content=message))

        # Stream response token by token
        async for event in agent_executor.astream_events({"messages": chat_history}, version="v2"):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
