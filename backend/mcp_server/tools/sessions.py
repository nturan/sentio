"""
MCP Tools for Chat Session operations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from app.database import get_connection, dict_from_row


async def session_list(project_id: str) -> str:
    """List all chat sessions for a project."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                cs.id, cs.project_id, cs.title, cs.created_at, cs.updated_at,
                COUNT(m.id) as message_count
            FROM chat_sessions cs
            LEFT JOIN messages m ON cs.id = m.session_id
            WHERE cs.project_id = ?
            GROUP BY cs.id
            ORDER BY cs.updated_at DESC
        """, (project_id,))

        sessions = [dict_from_row(row) for row in cursor.fetchall()]
        return json.dumps(sessions)


async def session_get(session_id: str, include_messages: bool = True) -> str:
    """Get a single chat session by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, project_id, title, created_at, updated_at
            FROM chat_sessions
            WHERE id = ?
        """, (session_id,))
        row = cursor.fetchone()

        if not row:
            return json.dumps({"error": "Session not found", "session_id": session_id})

        session = dict_from_row(row)

        if include_messages:
            cursor.execute("""
                SELECT id, session_id, role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """, (session_id,))
            session["messages"] = [dict_from_row(r) for r in cursor.fetchall()]
        else:
            session["messages"] = []

        return json.dumps(session)


async def session_create(project_id: str, title: Optional[str] = None) -> str:
    """Create a new chat session."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Verify project exists
        cursor.execute("SELECT id FROM projects WHERE id = ?", (project_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Project not found", "project_id": project_id})

        session_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        session_title = title or "New Chat"

        cursor.execute("""
            INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (session_id, project_id, session_title, now, now))

        cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
        session = dict_from_row(cursor.fetchone())
        session["messages"] = []

        return json.dumps(session)


async def session_update(
    session_id: str,
    title: Optional[str] = None,
    add_message_role: Optional[str] = None,
    add_message_content: Optional[str] = None
) -> str:
    """Update a chat session (title or add a message)."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM chat_sessions WHERE id = ?", (session_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Session not found", "session_id": session_id})

        now = datetime.utcnow().isoformat()

        # Update title if provided
        if title is not None:
            cursor.execute("""
                UPDATE chat_sessions SET title = ?, updated_at = ?
                WHERE id = ?
            """, (title, now, session_id))

        # Add message if provided
        if add_message_role and add_message_content:
            if add_message_role not in ("user", "assistant"):
                return json.dumps({"error": "add_message_role must be 'user' or 'assistant'"})

            message_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO messages (id, session_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (message_id, session_id, add_message_role, add_message_content, now))

            # Update session timestamp
            cursor.execute("""
                UPDATE chat_sessions SET updated_at = ?
                WHERE id = ?
            """, (now, session_id))

        # Return updated session with messages
        cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
        session = dict_from_row(cursor.fetchone())

        cursor.execute("""
            SELECT id, session_id, role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
        """, (session_id,))
        session["messages"] = [dict_from_row(r) for r in cursor.fetchall()]

        return json.dumps(session)


async def session_delete(session_id: str) -> str:
    """Delete a chat session and all its messages."""
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM chat_sessions WHERE id = ?", (session_id,))
        if not cursor.fetchone():
            return json.dumps({"error": "Session not found", "session_id": session_id})

        # Delete cascades due to foreign key constraints
        cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))

        return json.dumps({"success": True, "message": "Session deleted", "session_id": session_id})


# Tool definitions for the MCP server
TOOLS = {
    "session_list": {
        "description": "List all chat sessions for a project with message counts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to get sessions for"
                }
            },
            "required": ["project_id"]
        },
        "handler": session_list
    },
    "session_get": {
        "description": "Get a single chat session by ID with optional message history.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The unique identifier of the session"
                },
                "include_messages": {
                    "type": "boolean",
                    "description": "Whether to include message history (default true)"
                }
            },
            "required": ["session_id"]
        },
        "handler": session_get
    },
    "session_create": {
        "description": "Create a new chat session.",
        "input_schema": {
            "type": "object",
            "properties": {
                "project_id": {
                    "type": "string",
                    "description": "The project ID to create the session for"
                },
                "title": {
                    "type": "string",
                    "description": "Optional title for the session (defaults to 'New Chat')"
                }
            },
            "required": ["project_id"]
        },
        "handler": session_create
    },
    "session_update": {
        "description": "Update a chat session (title or add a message).",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The unique identifier of the session"
                },
                "title": {
                    "type": "string",
                    "description": "Optional new title"
                },
                "add_message_role": {
                    "type": "string",
                    "description": "Optional message role to add ('user' or 'assistant')"
                },
                "add_message_content": {
                    "type": "string",
                    "description": "Optional message content to add"
                }
            },
            "required": ["session_id"]
        },
        "handler": session_update
    },
    "session_delete": {
        "description": "Delete a chat session and all its messages.",
        "input_schema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "The unique identifier of the session"
                }
            },
            "required": ["session_id"]
        },
        "handler": session_delete
    }
}
