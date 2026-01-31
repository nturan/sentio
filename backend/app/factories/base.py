"""
Base factory class with common functionality for all entity factories.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, TypeVar
from datetime import datetime, timedelta
import uuid
import sqlite3

T = TypeVar("T")


class BaseFactory(ABC, Generic[T]):
    """Abstract base class for all entity factories."""

    # Shared sequence counters across all factories
    _sequence_counters: Dict[str, int] = {}

    @classmethod
    def reset_sequences(cls) -> None:
        """Reset all sequence counters. Useful between test runs."""
        cls._sequence_counters = {}

    @classmethod
    def next_sequence(cls, name: str) -> int:
        """Get the next sequence number for a named counter."""
        if name not in cls._sequence_counters:
            cls._sequence_counters[name] = 0
        cls._sequence_counters[name] += 1
        return cls._sequence_counters[name]

    @classmethod
    def generate_id(cls) -> str:
        """Generate a new UUID."""
        return str(uuid.uuid4())

    @classmethod
    def generate_timestamp(cls, days_ago: int = 0, hours_ago: int = 0, minutes_ago: int = 0) -> str:
        """Generate an ISO timestamp, optionally offset from now."""
        dt = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
        return dt.isoformat()

    @classmethod
    def generate_timestamp_from_base(cls, base_date: datetime, days_offset: int = 0) -> str:
        """Generate an ISO timestamp relative to a base date."""
        dt = base_date + timedelta(days=days_offset)
        return dt.isoformat()

    @classmethod
    def get_base_date(cls, days_ago: int) -> datetime:
        """Get a base datetime for relative calculations."""
        return datetime.utcnow() - timedelta(days=days_ago)

    @classmethod
    @abstractmethod
    def build(cls, **kwargs) -> Dict[str, Any]:
        """
        Build an entity dict in memory without persisting.
        Returns a dictionary with all entity fields.
        """
        pass

    @classmethod
    @abstractmethod
    def create(cls, conn: sqlite3.Connection, **kwargs) -> Dict[str, Any]:
        """
        Create and persist an entity to the database.
        Returns the created entity as a dictionary.
        """
        pass

    @classmethod
    def create_batch(cls, conn: sqlite3.Connection, count: int, **kwargs) -> List[Dict[str, Any]]:
        """Create multiple entities with the same base kwargs."""
        return [cls.create(conn, **kwargs) for _ in range(count)]
