from fastapi import APIRouter, HTTPException
from typing import List
from datetime import datetime
import uuid

from ..database import get_connection, dict_from_row
from ..models import (
    Session,
    SessionCreate,
    SessionWithMessages,
    Message,
    MessageCreate
)

router = APIRouter(prefix="/api", tags=["sessions"])


@router.get("/projects/{project_id}/sessions", response_model=List[Session])
async def list_sessions(project_id: str):
    """List all chat sessions for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, project_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE project_id = ?
            ORDER BY updated_at DESC
            """,
            (project_id,)
        )
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@router.post("/projects/{project_id}/sessions", response_model=Session)
async def create_session(project_id: str, session: SessionCreate):
    """Create a new chat session for a project."""
    session_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, project_id, session.title or "New Chat", now, now)
        )

        return {
            "id": session_id,
            "project_id": project_id,
            "title": session.title or "New Chat",
            "created_at": now,
            "updated_at": now
        }


@router.get("/sessions/{session_id}", response_model=SessionWithMessages)
async def get_session(session_id: str):
    """Get a session with all its messages."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get session
        cursor.execute(
            """
            SELECT id, project_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE id = ?
            """,
            (session_id,)
        )
        session_row = cursor.fetchone()

        if not session_row:
            raise HTTPException(status_code=404, detail="Session not found")

        session = dict_from_row(session_row)

        # Get messages
        cursor.execute(
            """
            SELECT id, session_id, role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            """,
            (session_id,)
        )
        messages = [dict_from_row(row) for row in cursor.fetchall()]

        return {**session, "messages": messages}


@router.patch("/sessions/{session_id}", response_model=Session)
async def update_session(session_id: str, session: SessionCreate):
    """Update a session's title."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if session exists
        cursor.execute(
            "SELECT id, project_id, created_at FROM chat_sessions WHERE id = ?",
            (session_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Session not found")

        now = datetime.utcnow().isoformat()

        cursor.execute(
            "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
            (session.title, now, session_id)
        )

        return {
            "id": session_id,
            "project_id": row["project_id"],
            "title": session.title,
            "created_at": row["created_at"],
            "updated_at": now
        }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session and all its messages."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if session exists
        cursor.execute(
            "SELECT id FROM chat_sessions WHERE id = ?",
            (session_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Session not found")

        # Delete session (messages will cascade delete)
        cursor.execute(
            "DELETE FROM chat_sessions WHERE id = ?",
            (session_id,)
        )

        return {"message": "Session deleted"}


@router.post("/sessions/{session_id}/messages", response_model=Message)
async def save_message(session_id: str, message: MessageCreate):
    """Save a message to a session."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if session exists
        cursor.execute(
            "SELECT id FROM chat_sessions WHERE id = ?",
            (session_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Session not found")

        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        cursor.execute(
            """
            INSERT INTO messages (id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (message_id, session_id, message.role, message.content, now)
        )

        # Update session's updated_at timestamp
        cursor.execute(
            "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
            (now, session_id)
        )

        return {
            "id": message_id,
            "session_id": session_id,
            "role": message.role,
            "content": message.content,
            "created_at": now
        }
