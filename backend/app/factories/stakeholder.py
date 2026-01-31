"""
Stakeholder factories for generating stakeholder groups and assessments.
"""

import random
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseFactory
from ..constants import (
    get_indicators_for_group_type,
    CORE_INDICATORS,
    FUEHRUNGSKRAEFTE_INDICATORS,
)


# German stakeholder group names by type
GROUP_NAMES = {
    "fuehrungskraefte": [
        "Bereichsleitung Vertrieb",
        "Teamleitung IT",
        "Abteilungsleitung Finanzen",
        "Bereichsleitung Produktion",
        "Teamleitung Personal",
        "Abteilungsleitung Marketing",
    ],
    "multiplikatoren": [
        "Change-Agenten Team A",
        "Kommunikationsteam",
        "Projektkoordinatoren",
        "Key User Gruppe",
        "Change Champions",
        "Botschafter-Netzwerk",
    ],
    "mitarbeitende": [
        "Vertriebsmitarbeiter Innendienst",
        "Sachbearbeitung Buchhaltung",
        "Kundenberater Callcenter",
        "Produktionsmitarbeiter Werk 1",
        "Verwaltungsangestellte",
        "Technischer Support",
    ],
}

# Sample notes for assessments per indicator
ASSESSMENT_NOTES = {
    "orientierung_sinn": [
        "Vision wurde im Townhall vorgestellt, noch Fragen offen",
        "Klare Kommunikation der Ziele, aber Umsetzung unklar",
        "Mitarbeiter verstehen den Nutzen, aber sehen Risiken",
        "Positive Resonanz nach Workshop zur Zielvermittlung",
    ],
    "psychologische_sicherheit": [
        "Team traut sich noch nicht, Bedenken zu äußern",
        "Erste positive Zeichen nach offener Fehlerkultur-Initiative",
        "Vertrauen wächst langsam durch regelmäßige Retrospektiven",
        "Noch Zurückhaltung bei kritischem Feedback",
    ],
    "empowerment": [
        "Entscheidungsbefugnisse noch nicht klar definiert",
        "Erste Pilotteams mit erweiterter Autonomie zeigen gute Ergebnisse",
        "Ressourcen werden zunehmend bereitgestellt",
        "Schulungen zur eigenverantwortlichen Arbeit laufen",
    ],
    "partizipation": [
        "Feedback-Runden wurden eingeführt",
        "Mitarbeitende wünschen sich mehr Einbindung",
        "Ideenworkshops zeigen hohe Beteiligung",
        "Transparenz bei Entscheidungen verbessert",
    ],
    "wertschaetzung": [
        "Anerkennung für Projektbeiträge wurde verstärkt",
        "Individuelle Bedürfnisse werden besser berücksichtigt",
        "Regelmäßiges Lob im Team-Meeting etabliert",
        "Mitarbeiter-Events zur Würdigung geplant",
    ],
    "ressourcenfreigabe": [
        "Budget wurde genehmigt, Personal noch knapp",
        "Beste Leute werden abgestellt",
        "Zeitliche Freistellung für Projektarbeit gewährleistet",
        "Ressourcenkonflikte mit Tagesgeschäft",
    ],
    "aktive_kommunikation": [
        "Führungskräfte übersetzen Ziele in ihre Abteilung",
        "Regelmäßige Updates an Teams",
        "Kommunikationsqualität variiert stark",
        "Kaskadenkommunikation funktioniert besser",
    ],
    "widerstandsmanagement": [
        "Bedenken werden früh aufgegriffen",
        "Konfliktlösung proaktiv angegangen",
        "Noch Eskalationen an Projektteam",
        "Training für Umgang mit Widerstand durchgeführt",
    ],
    "vorbildfunktion": [
        "Führungskräfte nutzen neue Tools aktiv",
        "Vorleben der neuen Verhaltensweisen sichtbar",
        "Noch nicht alle Führungskräfte an Bord",
        "Early Adopter unter den Teamleitern",
    ],
}


class StakeholderGroupFactory(BaseFactory):
    """Factory for creating stakeholder group entities."""

    @classmethod
    def build(
        cls,
        project_id: str,
        group_type: Optional[str] = None,
        name: Optional[str] = None,
        power_level: Optional[str] = None,
        interest_level: Optional[str] = None,
        notes: Optional[str] = None,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a stakeholder group dict without persisting."""
        group_type = group_type or random.choice(list(GROUP_NAMES.keys()))
        name = name or random.choice(GROUP_NAMES.get(group_type, ["Unbekannte Gruppe"]))

        return {
            "id": cls.generate_id(),
            "project_id": project_id,
            "group_type": group_type,
            "name": name,
            "power_level": power_level or random.choice(["high", "low"]),
            "interest_level": interest_level or random.choice(["high", "low"]),
            "notes": notes,
            "created_at": created_at or cls.generate_timestamp(),
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        group_type: Optional[str] = None,
        name: Optional[str] = None,
        power_level: Optional[str] = None,
        interest_level: Optional[str] = None,
        notes: Optional[str] = None,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist a stakeholder group."""
        data = cls.build(
            project_id=project_id,
            group_type=group_type,
            name=name,
            power_level=power_level,
            interest_level=interest_level,
            notes=notes,
            created_at=created_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO stakeholder_groups
            (id, project_id, group_type, name, power_level, interest_level, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["project_id"],
                data["group_type"],
                data["name"],
                data["power_level"],
                data["interest_level"],
                data["notes"],
                data["created_at"],
            )
        )

        return data

    @classmethod
    def create_standard_set(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        created_at: Optional[str] = None,
        mendelow_positions: Optional[Dict[str, tuple]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create a standard set of stakeholder groups (one of each type).

        Args:
            conn: Database connection
            project_id: Project ID to associate with
            created_at: Creation timestamp
            mendelow_positions: Optional dict mapping group_type to (power, interest) tuple

        Returns:
            List of created stakeholder groups
        """
        # Default Mendelow positions
        default_positions = {
            "fuehrungskraefte": ("high", "high"),  # Key Players
            "multiplikatoren": ("low", "high"),    # Keep Informed
            "mitarbeitende": ("low", "low"),       # Monitor
        }
        positions = mendelow_positions or default_positions

        groups = []
        for group_type in ["fuehrungskraefte", "multiplikatoren", "mitarbeitende"]:
            power, interest = positions.get(group_type, ("low", "low"))
            group = cls.create(
                conn,
                project_id=project_id,
                group_type=group_type,
                power_level=power,
                interest_level=interest,
                created_at=created_at,
            )
            groups.append(group)

        return groups


class StakeholderAssessmentFactory(BaseFactory):
    """Factory for creating stakeholder assessment entities."""

    @classmethod
    def build(
        cls,
        stakeholder_group_id: str,
        indicator_key: str,
        rating: Optional[int] = None,
        notes: Optional[str] = None,
        assessed_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build an assessment dict without persisting."""
        # Get a random note for this indicator if not provided
        if notes is None and indicator_key in ASSESSMENT_NOTES:
            notes = random.choice(ASSESSMENT_NOTES[indicator_key])

        return {
            "id": cls.generate_id(),
            "stakeholder_group_id": stakeholder_group_id,
            "indicator_key": indicator_key,
            "rating": rating if rating is not None else random.randint(4, 8),
            "notes": notes,
            "assessed_at": assessed_at or cls.generate_timestamp(),
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        stakeholder_group_id: str,
        indicator_key: str,
        rating: Optional[int] = None,
        notes: Optional[str] = None,
        assessed_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist an assessment."""
        data = cls.build(
            stakeholder_group_id=stakeholder_group_id,
            indicator_key=indicator_key,
            rating=rating,
            notes=notes,
            assessed_at=assessed_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO stakeholder_assessments
            (id, stakeholder_group_id, indicator_key, rating, notes, assessed_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["stakeholder_group_id"],
                data["indicator_key"],
                data["rating"],
                data["notes"],
                data["assessed_at"],
            )
        )

        return data

    @classmethod
    def create_full_assessment(
        cls,
        conn: sqlite3.Connection,
        stakeholder_group_id: str,
        group_type: str,
        assessed_at: Optional[str] = None,
        ratings: Optional[Dict[str, int]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create a full assessment (all indicators) for a stakeholder group.

        Args:
            conn: Database connection
            stakeholder_group_id: The stakeholder group ID
            group_type: The group type (determines which indicators)
            assessed_at: Assessment timestamp
            ratings: Optional dict of indicator_key -> rating

        Returns:
            List of created assessments
        """
        indicators = get_indicators_for_group_type(group_type)
        ratings = ratings or {}

        assessments = []
        for indicator in indicators:
            key = indicator["key"]
            rating = ratings.get(key)  # Will use random if None
            assessment = cls.create(
                conn,
                stakeholder_group_id=stakeholder_group_id,
                indicator_key=key,
                rating=rating,
                assessed_at=assessed_at,
            )
            assessments.append(assessment)

        return assessments

    @classmethod
    def create_impulse_history(
        cls,
        conn: sqlite3.Connection,
        stakeholder_group_id: str,
        group_type: str,
        num_impulses: int,
        start_days_ago: int,
        rating_history: Dict[str, List[float]],
    ) -> List[List[Dict[str, Any]]]:
        """
        Create a complete impulse history for a stakeholder group.

        Args:
            conn: Database connection
            stakeholder_group_id: The stakeholder group ID
            group_type: The group type
            num_impulses: Number of impulses to create
            start_days_ago: How many days ago the first impulse was
            rating_history: Dict of indicator_key -> list of ratings over time

        Returns:
            List of impulse sets (each impulse is a list of assessments)
        """
        base_date = cls.get_base_date(start_days_ago)

        # Calculate days between impulses (bi-weekly = 14 days)
        if num_impulses > 1:
            days_between = start_days_ago / (num_impulses - 1)
        else:
            days_between = 0

        impulses = []
        for i in range(num_impulses):
            # Calculate date for this impulse
            days_offset = int(i * days_between)
            impulse_date = cls.generate_timestamp_from_base(base_date, days_offset)

            # Get ratings for this impulse
            impulse_ratings = {}
            for key, ratings in rating_history.items():
                if i < len(ratings):
                    impulse_ratings[key] = int(round(ratings[i]))

            # Create the full assessment for this date
            assessments = cls.create_full_assessment(
                conn,
                stakeholder_group_id=stakeholder_group_id,
                group_type=group_type,
                assessed_at=impulse_date,
                ratings=impulse_ratings,
            )
            impulses.append(assessments)

        return impulses
