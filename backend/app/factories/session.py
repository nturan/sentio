"""
Session and Message factories for generating test chat data.
"""

import random
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseFactory


# German chat session titles
SESSION_TITLES = [
    "Stakeholder-Analyse",
    "Projektplanung",
    "Widerstandsmanagement",
    "Kommunikationsstrategie",
    "Impulsbewertung",
    "Quick-Win Ideen",
    "Führungskräfte-Engagement",
    "Mitarbeiter-Feedback",
]

# German conversation templates (user/assistant exchanges)
GERMAN_CONVERSATIONS = [
    # Conversation 1: Stakeholder analysis
    [
        ("user", "Wie kann ich die Stakeholder-Akzeptanz für unser Change-Projekt verbessern?"),
        ("assistant", "Um die Stakeholder-Akzeptanz zu verbessern, empfehle ich einen dreistufigen Ansatz:\n\n1. **Stakeholder-Mapping**: Identifizieren Sie zunächst alle relevanten Stakeholder und ordnen Sie diese in der Mendelow-Matrix ein (Macht vs. Interesse).\n\n2. **Individuelle Ansprache**: Entwickeln Sie für jede Stakeholder-Gruppe eine maßgeschneiderte Kommunikationsstrategie.\n\n3. **Frühe Einbindung**: Binden Sie kritische Stakeholder frühzeitig in Entscheidungsprozesse ein.\n\nMöchten Sie, dass ich einen konkreten Aktionsplan für eine bestimmte Stakeholder-Gruppe erstelle?"),
        ("user", "Ja, bitte für die Führungskräfte im mittleren Management."),
        ("assistant", "Für Führungskräfte im mittleren Management empfehle ich folgende Maßnahmen:\n\n**Kurzfristig (diese Woche):**\n- Persönliche Gespräche mit Schlüssel-Führungskräften führen\n- Bedenken und Erwartungen aktiv erfragen\n\n**Mittelfristig (2-4 Wochen):**\n- Führungskräfte-Workshop zur Rollenklärung\n- Klare Kommunikation der Vorteile für ihre Teams\n- Regelmäßige Briefings einrichten\n\n**Langfristig:**\n- Führungskräfte als Change-Botschafter einsetzen\n- Erfolge sichtbar machen und würdigen\n\nSoll ich zu einem dieser Punkte ins Detail gehen?"),
    ],
    # Conversation 2: Resistance management
    [
        ("user", "Wir haben starken Widerstand bei den Mitarbeitenden. Was können wir tun?"),
        ("assistant", "Widerstand ist ein normaler Teil jedes Veränderungsprozesses und oft ein Zeichen dafür, dass die Veränderung als relevant wahrgenommen wird. Hier sind bewährte Strategien:\n\n**1. Widerstand verstehen:**\n- Anonyme Umfragen durchführen\n- Einzelgespräche suchen\n- Die Ursachen identifizieren (Angst, Unsicherheit, Kontrollverlust?)\n\n**2. Aktiv kommunizieren:**\n- Das 'Warum' klar erklären\n- Ehrlich über Herausforderungen sprechen\n- Regelmäßige Updates geben\n\n**3. Partizipation ermöglichen:**\n- Betroffene in Entscheidungen einbinden\n- Feedback-Kanäle etablieren\n- Quick Wins schaffen\n\nWas ist Ihrer Einschätzung nach der Hauptgrund für den Widerstand?"),
        ("user", "Die Mitarbeiter haben Angst vor Jobverlust durch die Digitalisierung."),
        ("assistant", "Das ist eine sehr häufige und nachvollziehbare Sorge. Hier sind konkrete Empfehlungen:\n\n**Sofortmaßnahmen:**\n1. **Klares Commitment der Geschäftsführung** zu Arbeitsplatzgarantien (wenn möglich)\n2. **Townhall-Meeting** mit Q&A-Session zu diesem Thema\n\n**Qualifizierungsoffensive:**\n1. **Kompetenzanalyse** durchführen: Welche Skills werden künftig gebraucht?\n2. **Schulungsprogramme** entwickeln und ankündigen\n3. **Karrierepfade** aufzeigen - wie verändert sich die Arbeit, nicht ob sie verschwindet\n\n**Kommunikation:**\n- Erfolgsgeschichten teilen von Mitarbeitenden, die sich weiterentwickelt haben\n- Transparent über neue Rollen und Aufgaben informieren\n\nMöchten Sie, dass ich einen Kommunikationsplan für dieses Thema erstelle?"),
    ],
    # Conversation 3: Quick wins
    [
        ("user", "Wir brauchen schnelle Erfolge, um das Momentum aufrechtzuerhalten."),
        ("assistant", "Quick Wins sind entscheidend für die Motivation. Hier einige bewährte Ideen:\n\n**Sofort umsetzbar (1-2 Wochen):**\n- Erste Pilotgruppe mit neuen Tools starten\n- Erfolgsgeschichte intern kommunizieren\n- Kleines Danke-Event für engagierte Mitarbeiter\n\n**Kurzfristig (2-4 Wochen):**\n- Ein konkretes Problem lösen, das viele betrifft\n- Verbesserungsvorschlag eines Mitarbeiters umsetzen\n- Positives Feedback von Kunden teilen\n\nWichtig: Quick Wins sollten **sichtbar** und **relevant** für die Betroffenen sein.\n\nWelchen Bereich möchten Sie priorisieren?"),
    ],
    # Conversation 4: Assessment discussion
    [
        ("user", "Die letzten Impulsbewertungen zeigen einen Rückgang bei Psychologischer Sicherheit. Was bedeutet das?"),
        ("assistant", "Ein Rückgang bei der Psychologischen Sicherheit ist ein wichtiges Warnsignal, das auf mehrere Ursachen hindeuten kann:\n\n**Mögliche Ursachen:**\n- Erhöhter Druck durch Projektmeilensteine\n- Kritik wurde negativ aufgenommen\n- Fehler wurden öffentlich thematisiert\n- Unsicherheit über die Zukunft\n\n**Empfohlene Maßnahmen:**\n1. **Ursachenforschung**: Vertrauliche Gespräche mit Teammitgliedern führen\n2. **Führungskräfte sensibilisieren**: Training zur psychologischen Sicherheit\n3. **Fehlerkultur stärken**: 'Lessons Learned' statt Schuldzuweisungen\n4. **Retrospektiven einführen**: Sichere Räume für offenes Feedback\n\nSoll ich einen detaillierten Maßnahmenplan für Ihr Team erstellen?"),
        ("user", "Ja bitte, und wie messen wir den Erfolg?"),
        ("assistant", "**Maßnahmenplan Psychologische Sicherheit:**\n\n**Woche 1-2:**\n- Vertrauliche 1:1-Gespräche (Führungskraft mit jedem Teammitglied)\n- Team-Retrospektive mit externem Moderator\n\n**Woche 3-4:**\n- Führungskräfte-Workshop 'Psychologische Sicherheit'\n- Einführung anonymer Feedback-Tool\n\n**Fortlaufend:**\n- Wöchentliche 'Fail Forward'-Runde im Team\n- Monatliche Check-ins\n\n**Erfolgsmessung:**\n1. **Quantitativ:**\n   - Impulsbewertung alle 2 Wochen\n   - Ziel: Steigerung um 1-2 Punkte in 8 Wochen\n   - Teilnahme an Team-Events\n\n2. **Qualitativ:**\n   - Anzahl eingebrachter Ideen/Bedenken in Meetings\n   - Offenheit bei Retrospektiven\n   - Feedback in 1:1s\n\nMöchten Sie die erste Retrospektive planen?"),
    ],
]


class SessionFactory(BaseFactory):
    """Factory for creating chat session entities."""

    @classmethod
    def build(
        cls,
        project_id: str,
        title: Optional[str] = None,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a session dict without persisting."""
        return {
            "id": cls.generate_id(),
            "project_id": project_id,
            "title": title or random.choice(SESSION_TITLES),
            "created_at": created_at or cls.generate_timestamp(),
            "updated_at": created_at or cls.generate_timestamp(),
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        title: Optional[str] = None,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist a session."""
        data = cls.build(
            project_id=project_id,
            title=title,
            created_at=created_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO chat_sessions (id, project_id, title, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["project_id"],
                data["title"],
                data["created_at"],
                data["updated_at"],
            )
        )

        return data


class MessageFactory(BaseFactory):
    """Factory for creating chat message entities."""

    @classmethod
    def build(
        cls,
        session_id: str,
        role: str,
        content: str,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Build a message dict without persisting."""
        return {
            "id": cls.generate_id(),
            "session_id": session_id,
            "role": role,
            "content": content,
            "created_at": created_at or cls.generate_timestamp(),
        }

    @classmethod
    def create(
        cls,
        conn: sqlite3.Connection,
        session_id: str,
        role: str,
        content: str,
        created_at: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create and persist a message."""
        data = cls.build(
            session_id=session_id,
            role=role,
            content=content,
            created_at=created_at,
            **kwargs
        )

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (id, session_id, role, content, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data["id"],
                data["session_id"],
                data["role"],
                data["content"],
                data["created_at"],
            )
        )

        return data

    @classmethod
    def create_conversation(
        cls,
        conn: sqlite3.Connection,
        session_id: str,
        conversation: Optional[List[tuple]] = None,
        base_timestamp: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Create a full conversation in a session.

        Args:
            conn: Database connection
            session_id: Session ID
            conversation: List of (role, content) tuples. If None, picks random.
            base_timestamp: Base timestamp for first message

        Returns:
            List of created messages
        """
        if conversation is None:
            conversation = random.choice(GERMAN_CONVERSATIONS)

        if base_timestamp is None:
            base_date = cls.get_base_date(random.randint(1, 30))
        else:
            base_date = datetime.fromisoformat(base_timestamp.replace('Z', '+00:00'))

        messages = []
        for i, (role, content) in enumerate(conversation):
            # Add 1-5 minutes between messages
            message_time = base_date + timedelta(minutes=i * random.randint(1, 5))
            msg = cls.create(
                conn,
                session_id=session_id,
                role=role,
                content=content,
                created_at=message_time.isoformat(),
            )
            messages.append(msg)

        return messages

    @classmethod
    def create_sessions_with_conversations(
        cls,
        conn: sqlite3.Connection,
        project_id: str,
        num_sessions: int,
        days_range: tuple = (1, 60),
    ) -> List[Dict[str, Any]]:
        """
        Create multiple sessions with German conversations.

        Args:
            conn: Database connection
            project_id: Project ID
            num_sessions: Number of sessions to create
            days_range: Tuple of (min_days_ago, max_days_ago) for session creation

        Returns:
            List of created sessions with their messages
        """
        min_days, max_days = days_range
        sessions = []

        # Shuffle conversations to vary content
        available_conversations = GERMAN_CONVERSATIONS.copy()
        random.shuffle(available_conversations)

        for i in range(num_sessions):
            days_ago = random.randint(min_days, max_days)
            base_date = cls.get_base_date(days_ago)

            # Create session
            session = SessionFactory.create(
                conn,
                project_id=project_id,
                created_at=base_date.isoformat(),
            )

            # Pick a conversation (cycle through if more sessions than conversations)
            conv_idx = i % len(available_conversations)
            conversation = available_conversations[conv_idx]

            # Create messages
            messages = cls.create_conversation(
                conn,
                session_id=session["id"],
                conversation=conversation,
                base_timestamp=base_date.isoformat(),
            )

            session["messages"] = messages
            sessions.append(session)

        return sessions
