"""
Scenario D: Ten Month Project - Mature project with rich history.
"""

import sqlite3
from typing import Any, Dict, List

from ..scenario_base import ScenarioGenerator
from ...factories import StakeholderGroupFactory, StakeholderAssessmentFactory
from ..rating_patterns import RatingPatternGenerator
from ...prompts import load_constants


class TenMonthScenario(ScenarioGenerator):
    """
    Scenario D: Project at 10 months.

    - Age: 300 days
    - Impulses: 22 bi-weekly entries
    - Stakeholders: 4 groups (1 added at month 5)
    - Patterns:
        - Fuehrungskraefte: volatile (inconsistent leadership)
        - Multiplikatoren: struggle_then_improve (breakthrough at month 7)
        - Mitarbeitende: declining (current crisis - needs intervention)
        - Mitarbeitende 2: steady_improvement (added later, better managed)
    - Recommendations: 18 (8 completed, 3 started, 2 approved, 2 pending, 3 rejected)
    - Sessions: 11 with rich conversation history
    """

    SCENARIO_NAME = "10month"
    SCENARIO_DESCRIPTION = "10-month project with complex history and active crisis"
    PROJECT_AGE_DAYS = 300
    NUM_IMPULSES = 22
    NUM_RECOMMENDATIONS = 18
    NUM_SESSIONS = 11

    @classmethod
    def generate(cls, conn: sqlite3.Connection) -> Dict[str, Any]:
        """Generate a 10-month project scenario."""
        from ...constants import get_indicators_for_group_type

        # Load localized scenario data
        scenarios = load_constants("scenarios")
        scenario_data = scenarios["10month"]

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

        # Create initial stakeholder groups (3 groups from start)
        initial_positions = {
            "fuehrungskraefte": ("high", "low"),   # Keep Satisfied - lost some interest
            "multiplikatoren": ("high", "high"),   # Key Players
            "mitarbeitende": ("low", "low"),       # Monitor - disengaged
        }
        initial_groups = cls.create_stakeholder_groups(
            conn,
            project_id=project["id"],
            created_at=project["created_at"],
            mendelow_positions=initial_positions,
        )
        result["stakeholder_groups"] = initial_groups

        # Add a 4th group (added at month 5 = 150 days ago)
        later_group = StakeholderGroupFactory.create(
            conn,
            project_id=project["id"],
            group_type="mitarbeitende",
            name=scenario_data["extra_group_name"],
            power_level="low",
            interest_level="high",  # Keep Informed - higher interest
            created_at=StakeholderGroupFactory.generate_timestamp(days_ago=150),
        )
        result["stakeholder_groups"].append(later_group)

        # Define patterns for each group
        # Note: Original 3 groups have full history, 4th group has partial
        patterns = {
            "fuehrungskraefte": "volatile",
            "multiplikatoren": "struggle_then_improve",
        }

        # Create impulse history for original groups
        for group in initial_groups:
            group_type = group["group_type"]
            group_id = group["id"]

            if group_type == "mitarbeitende":
                # Original mitarbeitende group: declining pattern (crisis)
                pattern = "declining"
            else:
                pattern = patterns.get(group_type, "steady_improvement")

            indicators = get_indicators_for_group_type(group_type)
            indicator_keys = [ind["key"] for ind in indicators]

            rating_history = RatingPatternGenerator.generate_assessment_history(
                pattern_type=pattern,
                num_impulses=cls.NUM_IMPULSES,
                group_type=group_type,
                indicator_keys=indicator_keys,
            )

            impulses = StakeholderAssessmentFactory.create_impulse_history(
                conn,
                stakeholder_group_id=group_id,
                group_type=group_type,
                num_impulses=cls.NUM_IMPULSES,
                start_days_ago=cls.PROJECT_AGE_DAYS - 7,
                rating_history=rating_history,
            )
            result["impulses"][group_id] = impulses

        # Create partial impulse history for the later-added group
        # Only 10 impulses (since added at month 5)
        later_indicators = get_indicators_for_group_type("mitarbeitende")
        later_indicator_keys = [ind["key"] for ind in later_indicators]

        later_rating_history = RatingPatternGenerator.generate_assessment_history(
            pattern_type="steady_improvement",  # Better managed group
            num_impulses=10,
            group_type="mitarbeitende",
            indicator_keys=later_indicator_keys,
        )

        later_impulses = StakeholderAssessmentFactory.create_impulse_history(
            conn,
            stakeholder_group_id=later_group["id"],
            group_type="mitarbeitende",
            num_impulses=10,
            start_days_ago=140,  # Started 140 days ago
            rating_history=later_rating_history,
        )
        result["impulses"][later_group["id"]] = later_impulses

        # Create recommendations with various statuses
        status_counts = {
            "completed": 8,
            "started": 3,
            "approved": 2,
            "pending_approval": 2,
            "rejected": 3,
        }
        recommendations = cls.create_recommendations(
            conn,
            project_id=project["id"],
            status_counts=status_counts,
            days_range=(14, 285),
        )
        result["recommendations"] = recommendations

        # Create chat sessions with rich history
        sessions = cls.create_chat_sessions(
            conn,
            project_id=project["id"],
            num_sessions=cls.NUM_SESSIONS,
            days_range=(7, 295),
        )
        result["sessions"] = sessions

        # Add summary with extra context about the crisis
        summary = cls.get_summary(result)
        summary["notes"] = scenario_data["notes"]
        result["summary"] = summary

        return result
