"""
Recommendation factory for generating test recommendation data.
"""

import random
import json
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseFactory


# German recommendation templates by type
RECOMMENDATION_TEMPLATES = {
    "habit": [
        {
            "title": "Tägliches 5-Minuten Standup",
            "description": "Ein kurzes tägliches Standup-Meeting fördert die Kommunikation und Transparenz im Team. Es hilft, Blocker früh zu erkennen und den Teamzusammenhalt zu stärken.",
            "steps": [
                "Zeitslot festlegen (z.B. 9:00 Uhr)",
                "Feste 3 Fragen einführen: Was habe ich gestern erreicht? Was mache ich heute? Was blockiert mich?",
                "Timekeeper bestimmen (rotierend)",
                "Nach 2 Wochen Feedback einholen und anpassen",
            ],
        },
        {
            "title": "Wöchentliche Erfolgs-Reflexion",
            "description": "Teams reflektieren wöchentlich ihre Erfolge und Fortschritte. Dies stärkt die positive Wahrnehmung des Changes und motiviert das Team.",
            "steps": [
                "Freitags 15 Minuten einplanen",
                "Jedes Teammitglied teilt einen Erfolg der Woche",
                "Erfolge visuell festhalten (z.B. Erfolgsboard)",
                "Monatlich größte Erfolge feiern",
            ],
        },
    ],
    "communication": [
        {
            "title": "Transparenz-Newsletter",
            "description": "Ein regelmäßiger Newsletter informiert alle Betroffenen über Fortschritte, Entscheidungen und nächste Schritte. Dies reduziert Gerüchte und stärkt das Vertrauen.",
            "steps": [
                "Redaktionsteam bestimmen",
                "Erscheinungsrhythmus festlegen (z.B. alle 2 Wochen)",
                "Feste Rubriken definieren: Highlights, Entscheidungen, FAQ, Termine",
                "Feedback-Kanal einrichten",
            ],
        },
        {
            "title": "Führungskräfte-Briefing etablieren",
            "description": "Regelmäßige Briefings für Führungskräfte stellen sicher, dass diese die Botschaften korrekt in ihre Teams tragen können.",
            "steps": [
                "Wöchentliches 30-Minuten-Format",
                "Talking Points vorbereiten",
                "Q&A-Runde einplanen",
                "Feedback aus den Teams sammeln",
            ],
        },
    ],
    "workshop": [
        {
            "title": "Change-Fitness Training",
            "description": "Ein Workshop zur Stärkung der individuellen Veränderungskompetenz. Teilnehmende lernen, mit Unsicherheit umzugehen und Veränderungen aktiv zu gestalten.",
            "steps": [
                "Externe Trainer identifizieren",
                "Pilotgruppe auswählen",
                "Halbtages-Format planen",
                "Transferaufgaben definieren",
                "Follow-up Session nach 4 Wochen",
            ],
        },
        {
            "title": "Stakeholder-Alignment Workshop",
            "description": "Ein moderierter Workshop zur Abstimmung der Erwartungen und Ziele zwischen verschiedenen Stakeholder-Gruppen.",
            "steps": [
                "Schlüssel-Stakeholder identifizieren",
                "Vorbereitende Interviews führen",
                "Ganztages-Workshop planen",
                "Gemeinsame Roadmap entwickeln",
                "Commitment dokumentieren",
            ],
        },
    ],
    "process": [
        {
            "title": "Feedback-Loops etablieren",
            "description": "Systematische Feedback-Prozesse ermöglichen schnelles Lernen und Anpassen. Betroffene werden zu Mitgestaltern.",
            "steps": [
                "Feedback-Kanäle definieren (digital + analog)",
                "Schnelle Reaktionszeiten zusagen (<48h)",
                "Feedback-Dashboard einrichten",
                "Monatliche Feedback-Auswertung",
            ],
        },
        {
            "title": "Entscheidungs-Delegation Matrix",
            "description": "Klare Definition, welche Entscheidungen auf welcher Ebene getroffen werden. Dies beschleunigt Prozesse und stärkt Empowerment.",
            "steps": [
                "Entscheidungskategorien identifizieren",
                "Delegation Levels festlegen",
                "Matrix visualisieren und kommunizieren",
                "Quartalsweise Review",
            ],
        },
    ],
    "campaign": [
        {
            "title": "Quick-Win Kampagne",
            "description": "Fokussierte Kampagne zur Erzielung schneller, sichtbarer Erfolge. Diese stärken das Vertrauen in den Change-Prozess.",
            "steps": [
                "3-5 Quick Wins identifizieren",
                "Verantwortliche benennen",
                "4-Wochen-Sprint planen",
                "Erfolge prominent kommunizieren",
            ],
        },
        {
            "title": "Change-Botschafter Programm",
            "description": "Ausbildung und Aktivierung von Change-Botschaftern in allen Bereichen, die als Multiplikatoren und Ansprechpartner fungieren.",
            "steps": [
                "Freiwillige Botschafter rekrutieren",
                "Schulungsprogramm entwickeln",
                "Regelmäßige Botschafter-Treffen",
                "Ressourcen und Tools bereitstellen",
                "Erfolge der Botschafter würdigen",
            ],
        },
    ],
}

# Rejection reasons in German
REJECTION_REASONS = [
    "Zu hoher Zeitaufwand für aktuelles Projektphase",
    "Budget nicht ausreichend",
    "Andere Prioritäten im aktuellen Sprint",
    "Stakeholder-Akzeptanz fraglich",
    "Ähnliche Initiative bereits in Planung",
    "Ressourcen nicht verfügbar",
    "Nicht passend für unsere Unternehmenskultur",
    "Zeitpunkt ungünstig - nach Jahresabschluss erneut prüfen",
]


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
        rec_type = recommendation_type or random.choice(list(RECOMMENDATION_TEMPLATES.keys()))
        templates = RECOMMENDATION_TEMPLATES.get(rec_type, RECOMMENDATION_TEMPLATES["habit"])
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
            rejection_reason = random.choice(REJECTION_REASONS)

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

        for status, count in status_counts.items():
            for _ in range(count):
                days_ago = random.randint(min_days, max_days)

                # Try to pick unused template
                rec_type = random.choice(list(RECOMMENDATION_TEMPLATES.keys()))
                templates = RECOMMENDATION_TEMPLATES[rec_type]

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
