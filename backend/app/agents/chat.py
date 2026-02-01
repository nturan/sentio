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
from ..constants import CORE_INDICATORS
import json


# System prompt with web search and insight capabilities
SYSTEM_PROMPT = """You are Sentio, an AI Change Management Assistant helping executives navigate organizational change.

The project goal is: {goal}

You help with:
- Discussing change management strategies
- Providing guidance on stakeholder engagement
- Answering questions about the project
- Offering insights based on uploaded documents
- Researching topics from the web

The project uses these fixed assessment factors (Bewertungsfaktoren):
{indicators}

## Web Search
You can use web_search(query, num_results) to research topics from the internet.
When researching:
1. Search for relevant information using specific queries
2. Compile results as markdown with all sources cited
3. After presenting research, ask if the user wants to save it as a project document

## Saving Documents
When the user confirms they want to save research or content as a document:
- Use document_create with the project_id, a descriptive filename (e.g., "Research_TopicName.md"), and the content
- The content should be well-formatted markdown

## Saving Insights
When the user says "save as insight", "this is important", "save this finding", etc:
1. Extract the specific content they want to save
2. Generate a concise title summarizing the insight
3. Use insight_create_interactive tool
4. If the tool returns needs_clarification, present the options to the user and ask them to choose:
   - insight_type: trend (pattern over time), opportunity (improvement area), warning (risk), success (what worked), pattern (recurring theme)
   - priority: high (urgent), medium (important), low (informational)
5. If relevant, suggest related stakeholder groups based on the context

## Combining Knowledge
When combining web research with project knowledge:
1. Use web_search for external perspectives and best practices
2. Use retrieve_knowledge for project documents
3. Use impulse_history_get for stakeholder feedback data
4. Synthesize clearly, marking external vs internal sources
5. Offer to save the combined analysis as a document and/or insight

Be helpful, professional, and focus on practical change management advice. Use German when responding unless the user writes in English."""


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

        # Format indicators list
        indicators_text = ""
        for ind in CORE_INDICATORS:
            indicators_text += f"- {ind['name']}: {ind['description']}\n"

        return SYSTEM_PROMPT.format(
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
