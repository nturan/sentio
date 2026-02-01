from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import json

from .agents.knowledge import KnowledgeAgent
from .agents.orchestrator import OrchestratorAgent
from .agents.chat import ChatAgent
from .agents.dashboard import DashboardAgent
from .agents.generator_chat import GeneratorChatAgent
from .agents.mcp_client import MCPClientManager
from .database import init_database
from .routers import sessions, projects, documents, workflow, stakeholders, surveys, recommendations, seed, insights

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize database
    init_database()

    # Initialize MCP client connection
    try:
        await MCPClientManager.get_tools()
        print("MCP client initialized successfully")
    except Exception as e:
        print(f"Warning: Failed to initialize MCP client: {e}")
        print("Agents will initialize MCP connection on first use")

    yield

    # Shutdown: Disconnect MCP client
    try:
        await MCPClientManager.disconnect()
        print("MCP client disconnected")
    except Exception as e:
        print(f"Warning: Error disconnecting MCP client: {e}")


app = FastAPI(title="Sentio Backend", lifespan=lifespan)

# Configure CORS
origins = [
    "http://localhost:5173",  # Vite dev server
    "http://localhost:4173",  # Vite preview
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Agents
knowledge_agent = KnowledgeAgent()
orchestrator_agent = OrchestratorAgent(knowledge_agent)
# Chat agent is initialized per request or reused.
# Since it holds stateless config, we can reuse, but agent_executor might keep some state if we used memory.
# Here we are using external history, so it is fine.
chat_agent = ChatAgent(knowledge_agent)
generator_chat_agent = GeneratorChatAgent(knowledge_agent)
dashboard_agent = DashboardAgent()

class ChatRequest(BaseModel):
    message: str
    projectId: str
    history: List[dict]

class OrchestratorRequest(BaseModel):
    goal: str
    projectId: str

class RetrieveRequest(BaseModel):
    query: str
    projectId: str

class DashboardRequest(BaseModel):
    text: str

class GeneratorChatRequest(BaseModel):
    message: str
    projectId: str
    generatorType: str  # 'recommendation', 'insight', 'survey'
    canvasData: dict
    history: List[dict]

@app.get("/")
def read_root():
    return {"message": "Welcome to Sentio Backend"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# --- Knowledge Endpoints ---

@app.post("/api/ingest")
async def ingest_document(
    file: UploadFile = File(...), 
    projectId: str = Form(...)
):
    metadata = {"projectId": projectId, "source": file.filename}
    return await knowledge_agent.ingest_document(file, metadata)

@app.post("/api/retrieval")
async def retrieve_context(request: RetrieveRequest):
    return await knowledge_agent.retrieve_context(request.query, request.projectId)

# --- Orchestrator Endpoints ---

@app.post("/api/brain")
async def orchestrate_plan(request: OrchestratorRequest):
    return await orchestrator_agent.generate_plan(request.goal, request.projectId)

# --- Chat Endpoints ---

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    async def stream_response():
        # Using a custom generator to format SSE or simple text stream
        async for chunk in chat_agent.chat(request.message, request.projectId, request.history):
            # Format as n8n style object if frontend expects that, or simple text
            # Frontend code in useChat.ts expects lines, JSON parsed.
            # It expects: { type: 'item', content: '...' }
            data = json.dumps({"type": "item", "content": chunk})
            yield f"{data}\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")

@app.post("/api/generator-chat")
async def generator_chat_endpoint(request: GeneratorChatRequest):
    """
    Interactive chat endpoint for generator modals.
    Allows users to ask questions about project context and request canvas modifications.
    """
    async def stream_response():
        async for chunk in generator_chat_agent.chat(
            message=request.message,
            project_id=request.projectId,
            generator_type=request.generatorType,
            canvas_data=request.canvasData,
            history=request.history
        ):
            # Same format as regular chat for frontend compatibility
            data = json.dumps({"type": "item", "content": chunk})
            yield f"{data}\n"

    return StreamingResponse(stream_response(), media_type="text/event-stream")

# --- Dashboard Endpoints ---

@app.post("/api/dashboard")
async def analyze_dashboard(request: DashboardRequest):
    # Depending on how the frontend calls this (raw body or JSON)
    # The new API config sends JSON body: { text: ... } ?
    # Let's check api.ts or just handle standard JSON.
    return await dashboard_agent.analyze(request.text)


# Register routers
app.include_router(sessions.router)
app.include_router(projects.router)
app.include_router(documents.router)
app.include_router(workflow.router)
app.include_router(stakeholders.router)
app.include_router(surveys.router)
app.include_router(recommendations.router)
app.include_router(seed.router)
app.include_router(insights.router)
