"""
Base scenario generator class for creating complete project scenarios.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import sqlite3

from ..factories import (
    ProjectFactory,
    StakeholderGroupFactory,
    StakeholderAssessmentFactory,
    RecommendationFactory,
    SessionFactory,
    MessageFactory,
)
from .rating_patterns import RatingPatternGenerator, PatternType


class ScenarioGenerator(ABC):
    """
    Abstract base class for scenario generators.

    Each scenario represents a project at a specific stage of its lifecycle,
    with appropriate amounts of historical data.
    """

    # Scenario metadata (override in subclasses)
    SCENARIO_NAME: str = "base"
    SCENARIO_DESCRIPTION: str = "Base scenario"
    PROJECT_AGE_DAYS: int = 0
    NUM_IMPULSES: int = 0
    NUM_RECOMMENDATIONS: int = 0
    NUM_SESSIONS: int = 0

    @classmethod
    @abstractmethod
    def generate(cls, conn: sqlite3.Connection) -> Dict[str, Any]:
        """
        Generate the complete scenario.

        Args:
            conn: Database connection

        Returns:
            Dict containing all created entities and summary info
        """
        pass

    @classmethod
    def create_project(
        cls,
        conn: sqlite3.Connection,
        name: Optional[str] = None,
        goal: Optional[str] = None,
        days_ago: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create the project for this scenario."""
        return ProjectFactory.create_with_workflow_state(
            conn,
            name=name,
            goal=goal,
            days_ago=days_ago or cls.PROJECT_AGE_DAYS,
            current_stage="define_indicators",
        )

    @classmethod
    def create_stakeholder_groups(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        created_at: str,
        mendelow_positions: Optional[Dict[str, tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """Create stakeholder groups for the project."""
        return StakeholderGroupFactory.create_standard_set(
            conn,
            project_id=project_id,
            created_at=created_at,
            mendelow_positions=mendelow_positions,
        )

    @classmethod
    def create_impulse_history(
        cls,
        conn: sqlite3.Connection,
        groups: List[Dict[str, Any]],
        patterns: Dict[str, PatternType],
        num_impulses: int,
        start_days_ago: int,
    ) -> Dict[str, List]:
        """
        Create impulse history for all stakeholder groups.

        Args:
            conn: Database connection
            groups: List of stakeholder groups
            patterns: Dict mapping group_type to pattern type
            num_impulses: Number of impulses per group
            start_days_ago: How many days ago the first impulse was

        Returns:
            Dict mapping group_id to list of impulses
        """
        from ..constants import get_indicators_for_group_type

        all_impulses = {}

        for group in groups:
            group_type = group["group_type"]
            group_id = group["id"]
            pattern = patterns.get(group_type, "steady_improvement")

            # Get indicators for this group type
            indicators = get_indicators_for_group_type(group_type)
            indicator_keys = [ind["key"] for ind in indicators]

            # Generate rating history using pattern
            rating_history = RatingPatternGenerator.generate_assessment_history(
                pattern_type=pattern,
                num_impulses=num_impulses,
                group_type=group_type,
                indicator_keys=indicator_keys,
            )

            # Create the impulses
            impulses = StakeholderAssessmentFactory.create_impulse_history(
                conn,
                stakeholder_group_id=group_id,
                group_type=group_type,
                num_impulses=num_impulses,
                start_days_ago=start_days_ago,
                rating_history=rating_history,
            )

            all_impulses[group_id] = impulses

        return all_impulses

    @classmethod
    def create_recommendations(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        status_counts: Dict[str, int],
        days_range: tuple = (7, 60),
    ) -> List[Dict[str, Any]]:
        """Create recommendations with various statuses."""
        return RecommendationFactory.create_recommendation_set(
            conn,
            project_id=project_id,
            status_counts=status_counts,
            days_range=days_range,
        )

    @classmethod
    def create_chat_sessions(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        num_sessions: int,
        days_range: tuple = (1, 60),
    ) -> List[Dict[str, Any]]:
        """Create chat sessions with conversations."""
        return MessageFactory.create_sessions_with_conversations(
            conn,
            project_id=project_id,
            num_sessions=num_sessions,
            days_range=days_range,
        )

    @classmethod
    def get_summary(cls, result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the created scenario."""
        return {
            "scenario": cls.SCENARIO_NAME,
            "description": cls.SCENARIO_DESCRIPTION,
            "project_id": result.get("project", {}).get("id"),
            "project_name": result.get("project", {}).get("name"),
            "stakeholder_groups": len(result.get("stakeholder_groups", [])),
            "impulses_per_group": cls.NUM_IMPULSES,
            "recommendations": len(result.get("recommendations", [])),
            "chat_sessions": len(result.get("sessions", [])),
        }
