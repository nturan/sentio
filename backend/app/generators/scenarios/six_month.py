"""
Scenario C: Six Month Project - Mid-stage with substantial history.
"""

import sqlite3
from typing import Any, Dict

from ..scenario_base import ScenarioGenerator


class SixMonthScenario(ScenarioGenerator):
    """
    Scenario C: Project at 6 months.

    - Age: 180 days
    - Impulses: 13 bi-weekly entries
    - Stakeholders: Mixed Mendelow positions (some movement)
    - Patterns:
        - Fuehrungskraefte: steady_improvement (got on board after initial dip)
        - Multiplikatoren: honeymoon_dip_recovery (facing scaling challenges)
        - Mitarbeitende: steady_improvement (seeing benefits)
    - Recommendations: 11 (3 completed, 2 started, 2 approved, 2 pending, 2 rejected)
    - Sessions: 5 with conversations
    """

    SCENARIO_NAME = "6month"
    SCENARIO_DESCRIPTION = "6-Monats-Projekt mit umfangreicher Historie"
    PROJECT_AGE_DAYS = 180
    NUM_IMPULSES = 13
    NUM_RECOMMENDATIONS = 11
    NUM_SESSIONS = 5

    @classmethod
    def generate(cls, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Generate a 6-month project scenario."""
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
            name="Digitale Transformation 2026",
            goal="Steigerung der Kundenzufriedenheit um 20% durch verbesserte digitale Services",
            days_ago=cls.PROJECT_AGE_DAYS,
        )
        result["project"] = project

        # Create stakeholder groups with mixed Mendelow positions
        # Showing some movement from initial positions
        mendelow_positions = {
            "fuehrungskraefte": ("high", "high"),  # Key Players - still engaged
            "multiplikatoren": ("high", "high"),   # Elevated to Key Players (more influence now)
            "mitarbeitende": ("low", "high"),      # Moved to Keep Informed (higher interest)
        }
        groups = cls.create_stakeholder_groups(
            conn,
            project_id=project["id"],
            created_at=project["created_at"],
            mendelow_positions=mendelow_positions,
        )
        result["stakeholder_groups"] = groups

        # Define patterns for each group type
        patterns = {
            "fuehrungskraefte": "steady_improvement",
            "multiplikatoren": "honeymoon_dip_recovery",
            "mitarbeitende": "steady_improvement",
        }

        # Create impulse history
        impulses = cls.create_impulse_history(
            conn,
            groups=groups,
            patterns=patterns,
            num_impulses=cls.NUM_IMPULSES,
            start_days_ago=cls.PROJECT_AGE_DAYS - 7,
        )
        result["impulses"] = impulses

        # Create recommendations with various statuses
        status_counts = {
            "completed": 3,
            "started": 2,
            "approved": 2,
            "pending_approval": 2,
            "rejected": 2,
        }
        recommendations = cls.create_recommendations(
            conn,
            project_id=project["id"],
            status_counts=status_counts,
            days_range=(14, 165),
        )
        result["recommendations"] = recommendations

        # Create chat sessions
        sessions = cls.create_chat_sessions(
            conn,
            project_id=project["id"],
            num_sessions=cls.NUM_SESSIONS,
            days_range=(7, 175),
        )
        result["sessions"] = sessions

        # Add summary
        result["summary"] = cls.get_summary(result)

        return result
