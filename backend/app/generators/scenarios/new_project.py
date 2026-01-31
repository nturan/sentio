"""
Scenario A: New Project - Fresh start with no history.
"""

import sqlite3
from typing import Any, Dict

from ..scenario_base import ScenarioGenerator
from ...factories import SessionFactory


class NewProjectScenario(ScenarioGenerator):
    """
    Scenario A: Fresh project with no history.

    - Age: 3 days
    - Impulses: 0
    - Recommendations: 0
    - Sessions: 1 (empty)
    """

    SCENARIO_NAME = "new"
    SCENARIO_DESCRIPTION = "Frisches Projekt ohne Historie (3 Tage alt)"
    PROJECT_AGE_DAYS = 3
    NUM_IMPULSES = 0
    NUM_RECOMMENDATIONS = 0
    NUM_SESSIONS = 1

    @classmethod
    def generate(cls, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Generate a new project scenario."""
        result = {
            "scenario": cls.SCENARIO_NAME,
            "project": None,
            "stakeholder_groups": [],
            "impulses": {},
            "recommendations": [],
            "sessions": [],
        }

        # Create the project
        project = cls.create_project(
            conn,
            name="Neues Change-Projekt",
            goal="Ziel noch zu definieren",
            days_ago=cls.PROJECT_AGE_DAYS,
        )
        result["project"] = project

        # Create stakeholder groups (but no assessments)
        groups = cls.create_stakeholder_groups(
            conn,
            project_id=project["id"],
            created_at=project["created_at"],
        )
        result["stakeholder_groups"] = groups

        # Create one empty session
        session = SessionFactory.create(
            conn,
            project_id=project["id"],
            title="Neuer Chat",
            created_at=project["created_at"],
        )
        result["sessions"] = [session]

        # Add summary
        result["summary"] = cls.get_summary(result)

        return result
