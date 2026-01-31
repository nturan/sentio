"""
Project factory for generating test project data.
"""

import random
import sqlite3
from typing import Any, Dict, Optional
from datetime import datetime

from .base import BaseFactory


# German project names
PROJECT_NAMES = [
    "Digitale Transformation 2026",
    "Agile Transformation Vertrieb",
    "New Work Initiative",
    "Reorganisation Kundenservice",
    "ERP-Systemeinführung",
    "Kulturwandel Produktion",
    "Prozessoptimierung Logistik",
    "IT-Modernisierung",
    "Fusion Integration",
    "Standortzusammenführung",
]

# Project goals
PROJECT_GOALS = [
    "Steigerung der Kundenzufriedenheit um 20% durch verbesserte digitale Services",
    "Einführung agiler Arbeitsmethoden in allen Vertriebsteams bis Q4",
    "Etablierung einer hybriden Arbeitskultur mit flexiblen Arbeitsmodellen",
    "Optimierung der Durchlaufzeiten im Kundenservice um 30%",
    "Erfolgreiche Migration aller Geschäftsprozesse auf das neue ERP-System",
]

# Project icons
PROJECT_ICONS = ["🚀", "💡", "🎯", "📊", "🔄", "⚡", "🌟", "🏗️"]


class ProjectFactory(BaseFactory):
    """Factory for creating project entities."""

    @classmethod
    def build(
        cls,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        goal: Optional[str] = None,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a project dict without persisting."""
        seq = cls.next_sequence("project")

        return {
            "id": cls.generate_id(),
            "name": name or random.choice(PROJECT_NAMES),
            "icon": icon or random.choice(PROJECT_ICONS),
            "goal": goal or random.choice(PROJECT_GOALS),
            "created_at": created_at or cls.generate_timestamp(),
            "updated_at": created_at or cls.generate_timestamp(),
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        name: Optional[str] = None,
        icon: Optional[str] = None,
        goal: Optional[str] = None,
        created_at: Optional[str] = None,
        days_ago: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist a project."""
        # Handle days_ago for created_at
        if days_ago is not None and created_at is None:
            created_at = cls.generate_timestamp(days_ago=days_ago)

        data = cls.build(
            name=name,
            icon=icon,
            goal=goal,
            created_at=created_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (id, name, icon, goal, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["name"],
                data["icon"],
                data["goal"],
                data["created_at"],
                data["updated_at"],
            )
        )

        return data

    @classmethod
    def create_with_workflow_state(
        cls,
        conn: sqlite3.Connection,
        current_stage: str = "define_indicators",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a project with an initialized workflow state."""
        project = cls.create(conn, **kwargs)

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO workflow_state (id, project_id, current_stage, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cls.generate_id(),
                project["id"],
                current_stage,
                project["created_at"],
                project["created_at"],
            )
        )

        project["workflow_stage"] = current_stage
        return project
