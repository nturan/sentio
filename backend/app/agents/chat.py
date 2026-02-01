"""
Chat Agent - uses MCP tools for data access and ReAct pattern for responses.
"""

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage
from .knowledge import KnowledgeAgent
from .mcp_client import MCPClientManager
from .web_search import web_search
from ..prompts import load_prompt, load_constants
import json


class ChatAgent:
    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.knowledge_agent = knowledge_agent
        self._tools = None
        self._agent = None

    async def _get_tools(self):
        """Get tools for the chat agent, including MCP tools."""
        if self._tools is not None:
            return self._tools

        # Create the knowledge retrieval tool
        @tool
        async def retrieve_knowledge(query: str, project_id: str) -> str:
            """
            Use this tool to search for facts, documents, or context about the project from the knowledge base.
            """
            result = await self.knowledge_agent.retrieve_context(query, project_id)
            return result.get("context", "No information found.")

        # Get MCP tools for data retrieval and creation
        mcp_tools = await MCPClientManager.get_tools_by_names([
            "project_get",
            "stakeholder_group_list",
            "impulse_history_get",
            "recommendation_list",
            "document_retrieve_context",
            "document_create",
            "insight_create_interactive"
        ])
        self._tools = [retrieve_knowledge, web_search] + mcp_tools

        return self._tools

    async def _get_project_context(self, project_id: str) -> dict:
        """Get project data for context using MCP tool."""
        result = await MCPClientManager.invoke_tool("project_get", project_id=project_id)
        project = json.loads(result)
        if "error" in project:
            raise ValueError(f"Project not found: {project_id}")
        return {"goal": project.get("goal")}

    def _build_system_prompt(self, context: dict) -> str:
        """Build system prompt with project context."""
        goal = context.get("goal") or "Not yet defined"

        # Load indicators from localized constants
        indicators = load_constants("core_indicators")
        indicators_text = ""
        for ind in indicators:
            indicators_text += f"- {ind['name']}: {ind['description']}\n"

        # Load system prompt template
        prompt_template = load_prompt("chat", "system")
        return prompt_template.format(
            goal=goal,
            indicators=indicators_text
        )

    async def chat(self, message: str, project_id: str, history: list):
        """
        Chat with the agent using streaming.

        Args:
            message: The user's message
            project_id: The project ID for context
            history: List of previous messages [{role: 'user'|'assistant', content: '...'}]

        Yields:
            String chunks of the response
        """
        # Get project context
        context = await self._get_project_context(project_id)

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Add tool usage instructions
        system_prompt += "\n\nUse the available tools when you need to check for facts, documents, or data about the project."

        # Get tools
        tools = await self._get_tools()

        # Create agent with updated prompt
        agent_executor = create_react_agent(self.llm, tools, prompt=system_prompt)

        # Convert simple history to LangChain messages
        chat_history = []
        for msg in history:
            if msg.get("role") == "user":
                chat_history.append(HumanMessage(content=msg.get("content")))
            elif msg.get("role") == "assistant":
                chat_history.append(AIMessage(content=msg.get("content")))

        # Add current message with project context
        chat_history.append(HumanMessage(content=f"{message} (Project ID: {project_id})"))

        # Stream response token by token
        async for event in agent_executor.astream_events({"messages": chat_history}, version="v2"):
            if event["event"] == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    yield content
