"""
Session and Message factories for generating test chat data.
"""

import random
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseFactory
from ..prompts import load_constants


def get_session_titles() -> List[str]:
    """Load localized session titles."""
    return load_constants("session_titles")


def get_conversations() -> List[List[tuple]]:
    """Load localized conversations and convert to tuple format."""
    conversations_data = load_constants("conversations")
    result = []
    for conv in conversations_data:
        messages = [(msg["role"], msg["content"]) for msg in conv]
        result.append(messages)
    return result


class SessionFactory(BaseFactory):
    """Factory for creating chat session entities."""

    @classmethod
    def build(
        cls,
        project_id: str,
        title: Optional[str] = None,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a session dict without persisting."""
        return {
            "id": cls.generate_id(),
            "project_id": project_id,
            "title": title or random.choice(get_session_titles()),
            "created_at": created_at or cls.generate_timestamp(),
            "updated_at": created_at or cls.generate_timestamp(),
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        title: Optional[str] = None,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist a session."""
        data = cls.build(
            project_id=project_id,
            title=title,
            created_at=created_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["project_id"],
                data["title"],
                data["created_at"],
                data["updated_at"],
            )
        )

        return data


class MessageFactory(BaseFactory):
    """Factory for creating chat message entities."""

    @classmethod
    def build(
        cls,
        session_id: str,
        role: str,
        content: str,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a message dict without persisting."""
        return {
            "id": cls.generate_id(),
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": created_at or cls.generate_timestamp(),
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        session_id: str,
        role: str,
        content: str,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist a message."""
        data = cls.build(
            session_id=session_id,
            role=role,
            content=content,
            created_at=created_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["session_id"],
                data["role"],
                data["content"],
                data["created_at"],
            )
        )

        return data

    @classmethod
    def create_conversation(
        cls,
        conn: sqlite3.Connection,
        session_id: str,
        conversation: Optional[List[tuple]] = None,
        base_timestamp: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create a full conversation in a session.

        Args:
            conn: Database connection
            session_id: Session ID
            conversation: List of (role, content) tuples. If None, picks random.
            base_timestamp: Base timestamp for first message

        Returns:
            List of created messages
        """
        if conversation is None:
            conversation = random.choice(get_conversations())

        if base_timestamp is None:
            base_date = cls.get_base_date(random.randint(1, 30))
        else:
            base_date = datetime.fromisoformat(base_timestamp.replace('Z', '+00:00'))

        messages = []
        for i, (role, content) in enumerate(conversation):
            # Add 1-5 minutes between messages
            message_time = base_date + timedelta(minutes=i * random.randint(1, 5))
            msg = cls.create(
                conn,
                session_id=session_id,
                role=role,
                content=content,
                created_at=message_time.isoformat(),
            )
            messages.append(msg)

        return messages

    @classmethod
    def create_sessions_with_conversations(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        num_sessions: int,
        days_range: tuple = (1, 60),
    ) -> List[Dict[str, Any]]:
        """
        Create multiple sessions with German conversations.

        Args:
            conn: Database connection
            project_id: Project ID
            num_sessions: Number of sessions to create
            days_range: Tuple of (min_days_ago, max_days_ago) for session creation

        Returns:
            List of created sessions with their messages
        """
        min_days, max_days = days_range
        sessions = []

        # Shuffle conversations to vary content
        available_conversations = get_conversations().copy()
        random.shuffle(available_conversations)

        for i in range(num_sessions):
            days_ago = random.randint(min_days, max_days)
            base_date = cls.get_base_date(days_ago)

            # Create session
            session = SessionFactory.create(
                conn,
                project_id=project_id,
                created_at=base_date.isoformat(),
            )

            # Pick a conversation (cycle through if more sessions than conversations)
            conv_idx = i % len(available_conversations)
            conversation = available_conversations[conv_idx]

            # Create messages
            messages = cls.create_conversation(
                conn,
                session_id=session["id"],
                conversation=conversation,
                base_timestamp=base_date.isoformat(),
            )

            session["messages"] = messages
            sessions.append(session)

        return sessions
