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
import json
from typing import Optional


GENERATOR_CHAT_SYSTEM_PROMPT = """Du bist ein AI-Assistent, der bei der Erstellung von {generator_type_german} hilft.

=== PROJEKT-KONTEXT ===
Projekt-ID: {project_id}

Du hast Zugriff auf Projektdaten ueber Tools. WICHTIG: Verwende IMMER die obige Projekt-ID wenn du Tools aufrufst!

Tool-Verwendung:
- stakeholder_group_list(project_id="{project_id}"): Alle Stakeholder-Gruppen des Projekts
- recommendation_list(project_id="{project_id}"): Bestehende Empfehlungen
- insight_list(project_id="{project_id}"): Alle Insights des Projekts
- impulse_history_get(group_id="<group_id>"): Feedback fuer eine spezifische Gruppe (erst stakeholder_group_list aufrufen, um group_id zu erhalten)
- document_retrieve_context(project_id="{project_id}"): Projektdokumente durchsuchen
- retrieve_knowledge(query="<suchbegriff>"): Wissen aus der Dokumenten-Wissensbasis

=== AKTUELLER CANVAS-INHALT ===
{canvas_json}

=== REGELN ===

1. FRAGEN BEANTWORTEN:
   - Beantworte Fragen zum Projekt basierend auf den verfuegbaren Daten
   - Nutze die Tools, um aktuelle Informationen abzurufen
   - Antworte immer auf Deutsch, es sei denn der Benutzer schreibt auf Englisch

2. CANVAS AENDERUNGEN:
   - Wenn der Benutzer Aenderungen am Canvas wuenscht, fuehre sie aus
   - Erklaere kurz, was du geaendert hast
   - Fuege am Ende deiner Antwort einen Canvas-Update-Block hinzu:

   <<CANVAS_UPDATE>>
   {{"feldname": "neuer_wert", ...}}

3. FELDNAMEN FUER EMPFEHLUNGEN:
   - title: Titel der Empfehlung
   - description: Beschreibung
   - recommendation_type: "habit", "communication", "workshop", "process", oder "campaign"
   - priority: "high", "medium", oder "low"
   - affected_groups: Array von Gruppen-IDs oder ["all"]
   - steps: Array von Schritten (Strings)

4. WICHTIG:
   - Aendere NUR die Felder, die der Benutzer explizit erwaehnt
   - Der Canvas-Update-Block muss valides JSON sein
   - Wenn keine Aenderung gewuenscht ist, fuege KEINEN Canvas-Update-Block hinzu

=== BEISPIELE ===

Benutzer: "Setze die Prioritaet auf hoch"
Antwort: "Ich habe die Prioritaet auf hoch gesetzt.

<<CANVAS_UPDATE>>
{{"priority": "high"}}"

Benutzer: "Fuege einen Schritt hinzu: Team informieren"
Antwort: "Ich habe den Schritt 'Team informieren' hinzugefuegt.

<<CANVAS_UPDATE>>
{{"steps": ["Schritt 1", "Schritt 2", "Team informieren"]}}"

Benutzer: "Was sind die aktuellen Stakeholder-Gruppen?"
Antwort: [Rufe stakeholder_group_list mit project_id auf und beschreibe die Gruppen - KEIN Canvas-Update]

Benutzer: "Wie viele Impulse gab es?"
Antwort: [Erst stakeholder_group_list aufrufen um die group_ids zu erhalten, dann impulse_history_get fuer jede Gruppe - KEIN Canvas-Update]
"""

GENERATOR_TYPE_GERMAN = {
    "recommendation": "Handlungsempfehlungen",
    "insight": "Insights",
    "survey": "Umfragen"
}


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
        generator_type_german = GENERATOR_TYPE_GERMAN.get(generator_type, generator_type)

        # Format canvas data as readable JSON
        canvas_json = json.dumps(canvas_data, indent=2, ensure_ascii=False)

        return GENERATOR_CHAT_SYSTEM_PROMPT.format(
            generator_type_german=generator_type_german,
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

        # Add tool usage instructions
        system_prompt += f"\n\nVerwende die verfuegbaren Tools, wenn du Fakten, Dokumente oder Daten zum Projekt nachschlagen musst. Denke daran: Die Projekt-ID ist '{project_id}'."

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
