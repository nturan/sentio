"""
Scenario B: Three Month Project - Early stage with initial data.
"""

import sqlite3
from typing import Any, Dict

from ..scenario_base import ScenarioGenerator
from ...prompts import load_constants


class ThreeMonthScenario(ScenarioGenerator):
    """
    Scenario B: Project at 3 months.

    - Age: 90 days
    - Impulses: 6 bi-weekly entries
    - Patterns:
        - Fuehrungskraefte: honeymoon_dip_recovery (started optimistic, facing reality)
        - Multiplikatoren: steady_improvement (committed, seeing progress)
        - Mitarbeitende: struggle_then_improve (skeptical but improving)
    - Recommendations: 5 (1 completed, 1 started, 1 approved, 1 pending, 1 rejected)
    - Sessions: 3 with conversations
    """

    SCENARIO_NAME = "3month"
    SCENARIO_DESCRIPTION = "3-month project with initial impulses and actions"
    PROJECT_AGE_DAYS = 90
    NUM_IMPULSES = 6
    NUM_RECOMMENDATIONS = 5
    NUM_SESSIONS = 3

    @classmethod
    def generate(cls, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Generate a 3-month project scenario."""
        # Load localized scenario data
        scenarios = load_constants("scenarios")
        scenario_data = scenarios["3month"]

        result = {
            "scenario": cls.SCENARIO_NAME,
            "project": None,
            "stakeholder_groups": [],
            "impulses": {},
            "recommendations": [],
            "sessions": [],
        }

        # Create the project with localized name and goal
        project = cls.create_project(
            conn,
            name=scenario_data["project_name"],
            goal=scenario_data["project_goal"],
            days_ago=cls.PROJECT_AGE_DAYS,
        )
        result["project"] = project

        # Create stakeholder groups with Mendelow positions
        mendelow_positions = {
            "fuehrungskraefte": ("high", "high"),  # Key Players
            "multiplikatoren": ("low", "high"),    # Keep Informed
            "mitarbeitende": ("low", "low"),       # Monitor
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
            "fuehrungskraefte": "honeymoon_dip_recovery",
            "multiplikatoren": "steady_improvement",
            "mitarbeitende": "struggle_then_improve",
        }

        # Create impulse history
        impulses = cls.create_impulse_history(
            conn,
            groups=groups,
            patterns=patterns,
            num_impulses=cls.NUM_IMPULSES,
            start_days_ago=cls.PROJECT_AGE_DAYS - 7,  # First impulse a week after project start
        )
        result["impulses"] = impulses

        # Create recommendations with various statuses
        status_counts = {
            "completed": 1,
            "started": 1,
            "approved": 1,
            "pending_approval": 1,
            "rejected": 1,
        }
        recommendations = cls.create_recommendations(
            conn,
            project_id=project["id"],
            status_counts=status_counts,
            days_range=(14, 75),
        )
        result["recommendations"] = recommendations

        # Create chat sessions
        sessions = cls.create_chat_sessions(
            conn,
            project_id=project["id"],
            num_sessions=cls.NUM_SESSIONS,
            days_range=(7, 85),
        )
        result["sessions"] = sessions

        # Add summary
        result["summary"] = cls.get_summary(result)

        return result
