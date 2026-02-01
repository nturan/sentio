"""
Recommendation factory for generating test recommendation data.
"""

import random
import json
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseFactory
from ..prompts import load_constants


def get_recommendation_templates() -> Dict[str, List[Dict]]:
    """Load localized recommendation templates."""
    return load_constants("recommendation_templates")


def get_rejection_reasons() -> List[str]:
    """Load localized rejection reasons."""
    return load_constants("rejection_reasons")


class RecommendationFactory(BaseFactory):
    """Factory for creating recommendation entities."""

    @classmethod
    def build(
        cls,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        recommendation_type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        affected_groups: Optional[List[str]] = None,
        steps: Optional[List[str]] = None,
        rejection_reason: Optional[str] = None,
        created_at: Optional[str] = None,
        approved_at: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a recommendation dict without persisting."""
        # Pick a random type and template if not specified
        recommendation_templates = get_recommendation_templates()
        rec_type = recommendation_type or random.choice(list(recommendation_templates.keys()))
        templates = recommendation_templates.get(rec_type, recommendation_templates["habit"])
        template = random.choice(templates)

        return {
            "id": cls.generate_id(),
            "project_id": project_id,
            "title": title or template["title"],
            "description": description or template["description"],
            "recommendation_type": rec_type,
            "priority": priority or random.choice(["high", "medium", "low"]),
            "status": status or "pending_approval",
            "affected_groups": affected_groups or ["multiplikatoren"],
            "steps": steps or template["steps"],
            "rejection_reason": rejection_reason,
            "parent_id": None,
            "created_at": created_at or cls.generate_timestamp(),
            "approved_at": approved_at,
            "started_at": started_at,
            "completed_at": completed_at,
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        recommendation_type: Optional[str] = None,
        priority: Optional[str] = None,
        status: Optional[str] = None,
        affected_groups: Optional[List[str]] = None,
        steps: Optional[List[str]] = None,
        rejection_reason: Optional[str] = None,
        created_at: Optional[str] = None,
        approved_at: Optional[str] = None,
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist a recommendation."""
        data = cls.build(
            project_id=project_id,
            title=title,
            description=description,
            recommendation_type=recommendation_type,
            priority=priority,
            status=status,
            affected_groups=affected_groups,
            steps=steps,
            rejection_reason=rejection_reason,
            created_at=created_at,
            approved_at=approved_at,
            started_at=started_at,
            completed_at=completed_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO recommendations
            (id, project_id, title, description, recommendation_type, priority, status,
             affected_groups, steps, rejection_reason, parent_id, created_at,
             approved_at, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["project_id"],
                data["title"],
                data["description"],
                data["recommendation_type"],
                data["priority"],
                data["status"],
                json.dumps(data["affected_groups"]),
                json.dumps(data["steps"]),
                data["rejection_reason"],
                data["parent_id"],
                data["created_at"],
                data["approved_at"],
                data["started_at"],
                data["completed_at"],
            )
        )

        return data

    @classmethod
    def create_with_lifecycle(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        status: str,
        days_ago: int = 30,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a recommendation with realistic lifecycle timestamps based on status.

        Args:
            conn: Database connection
            project_id: Project ID
            status: Target status (pending_approval, approved, rejected, started, completed)
            days_ago: How many days ago the recommendation was created
            **kwargs: Additional recommendation fields

        Returns:
            Created recommendation with appropriate timestamps
        """
        base_date = cls.get_base_date(days_ago)
        created_at = cls.generate_timestamp_from_base(base_date, 0)

        approved_at = None
        started_at = None
        completed_at = None
        rejection_reason = None

        if status == "rejected":
            # Rejected after 2-3 days
            rejection_reason = random.choice(get_rejection_reasons())

        elif status == "approved":
            # Approved after 1-2 days
            approved_at = cls.generate_timestamp_from_base(base_date, random.randint(1, 2))

        elif status == "started":
            # Approved after 1-2 days, started after 3-5 days
            approved_at = cls.generate_timestamp_from_base(base_date, random.randint(1, 2))
            started_at = cls.generate_timestamp_from_base(base_date, random.randint(3, 5))

        elif status == "completed":
            # Full lifecycle
            approved_at = cls.generate_timestamp_from_base(base_date, random.randint(1, 2))
            started_at = cls.generate_timestamp_from_base(base_date, random.randint(3, 5))
            completed_at = cls.generate_timestamp_from_base(base_date, random.randint(14, days_ago))

        return cls.create(
            conn,
            project_id=project_id,
            status=status,
            created_at=created_at,
            approved_at=approved_at,
            started_at=started_at,
            completed_at=completed_at,
            rejection_reason=rejection_reason,
            **kwargs
        )

    @classmethod
    def create_recommendation_set(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        status_counts: Dict[str, int],
        days_range: tuple = (7, 60),
    ) -> List[Dict[str, Any]]:
        """
        Create a set of recommendations with various statuses.

        Args:
            conn: Database connection
            project_id: Project ID
            status_counts: Dict mapping status -> count
            days_range: Tuple of (min_days_ago, max_days_ago) for creation dates

        Returns:
            List of created recommendations
        """
        recommendations = []
        min_days, max_days = days_range

        # Track used templates to avoid duplicates
        used_templates = set()
        recommendation_templates = get_recommendation_templates()

        for status, count in status_counts.items():
            for _ in range(count):
                days_ago = random.randint(min_days, max_days)

                # Try to pick unused template
                rec_type = random.choice(list(recommendation_templates.keys()))
                templates = recommendation_templates[rec_type]

                # Find unused template
                template = None
                for t in templates:
                    if t["title"] not in used_templates:
                        template = t
                        used_templates.add(t["title"])
                        break

                # If all used, pick random
                if template is None:
                    template = random.choice(templates)

                rec = cls.create_with_lifecycle(
                    conn,
                    project_id=project_id,
                    status=status,
                    days_ago=days_ago,
                    title=template["title"],
                    description=template["description"],
                    recommendation_type=rec_type,
                    steps=template["steps"],
                )
                recommendations.append(rec)

        return recommendations
