from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from .knowledge import KnowledgeAgent
from ..database import get_connection, dict_from_row
from ..constants import CORE_INDICATORS, get_indicator_by_key
import uuid
from datetime import datetime
import json


# Simplified system prompt - no longer stage-based
SYSTEM_PROMPT = """You are Sentio, an AI Change Management Assistant helping executives navigate organizational change.

The project goal is: {goal}

You help with:
- Discussing change management strategies
- Providing guidance on stakeholder engagement
- Answering questions about the project
- Offering insights based on uploaded documents

The project uses these fixed assessment factors (Bewertungsfaktoren):
{indicators}

Be helpful, professional, and focus on practical change management advice. Use German when responding unless the user writes in English."""


class ChatAgent:
    def __init__(self, knowledge_agent: KnowledgeAgent):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        self.knowledge_agent = knowledge_agent

        # Define Tools
        @tool
        async def retrieve_knowledge(query: str, project_id: str) -> str:
            """
            Use this tool to search for facts, documents, or context about the project from the knowledge base.
            """
            result = await self.knowledge_agent.retrieve_context(query, project_id)
            return result.get("context", "No information found.")

        self.tools = [retrieve_knowledge]

    def _get_project_context(self, project_id: str) -> dict:
        """Get project data for context."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get project goal
            cursor.execute("SELECT goal FROM projects WHERE id = ?", (project_id,))
            project_row = cursor.fetchone()
            goal = project_row["goal"] if project_row else None

        return {
            "goal": goal
        }

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
        # Get project context
        context = self._get_project_context(project_id)

        # Build system prompt
        system_prompt = self._build_system_prompt(context)

        # Add tool usage instructions
        system_prompt += "\n\nUse the `retrieve_knowledge` tool when you need to check for facts or documents in the knowledge base."

        # Create agent with updated prompt
        agent_executor = create_react_agent(self.llm, self.tools, prompt=system_prompt)

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
