import sqlite3
import os
from contextlib import contextmanager
from typing import Generator

# Database file path - store in backend directory
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'sentio.db')

def get_db_path() -> str:
    """Get the absolute path to the database file."""
    return os.path.abspath(DB_PATH)

@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_database():
    """Initialize the database schema."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Create projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                icon TEXT DEFAULT '🚀',
                goal TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create chat_sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Create messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            )
        """)

        # Create documents table for tracking uploaded files
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER,
                content_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Create workflow_state table - tracks workflow progress per project
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflow_state (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL UNIQUE,
                current_stage TEXT NOT NULL DEFAULT 'define_indicators',
                stage_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Create indicators table - success indicators (KPIs) for each project
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS indicators (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                target_value TEXT,
                current_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Create assessment_rounds table - each periodic assessment session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessment_rounds (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Create assessments table - individual ratings within a round
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assessments (
                id TEXT PRIMARY KEY,
                round_id TEXT NOT NULL,
                indicator_id TEXT NOT NULL,
                assessment_type TEXT NOT NULL CHECK(assessment_type IN ('self_rating', 'ai_interview')),
                rating INTEGER CHECK(rating >= 1 AND rating <= 10),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (round_id) REFERENCES assessment_rounds(id) ON DELETE CASCADE,
                FOREIGN KEY (indicator_id) REFERENCES indicators(id) ON DELETE CASCADE
            )
        """)

        # Create action_items table - replaces mock data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_items (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                assignee TEXT,
                due_date TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'open',
                source TEXT DEFAULT 'ai_generated',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Create stakeholder_groups table - stakeholder management
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stakeholder_groups (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                group_type TEXT NOT NULL CHECK(group_type IN ('fuehrungskraefte', 'multiplikatoren', 'mitarbeitende')),
                name TEXT,
                power_level TEXT NOT NULL CHECK(power_level IN ('high', 'low')),
                interest_level TEXT NOT NULL CHECK(interest_level IN ('high', 'low')),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            )
        """)

        # Create stakeholder_assessments table - assessments for stakeholder groups
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stakeholder_assessments (
                id TEXT PRIMARY KEY,
                stakeholder_group_id TEXT NOT NULL,
                indicator_key TEXT NOT NULL,
                rating INTEGER CHECK(rating >= 1 AND rating <= 10),
                notes TEXT,
                assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (stakeholder_group_id) REFERENCES stakeholder_groups(id) ON DELETE CASCADE
            )
        """)

        # Create surveys table - tracks generated surveys
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS surveys (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                stakeholder_group_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
                FOREIGN KEY (stakeholder_group_id) REFERENCES stakeholder_groups(id) ON DELETE CASCADE
            )
        """)

        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_project_id
            ON chat_sessions(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session_id
            ON messages(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_project_id
            ON documents(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_workflow_state_project_id
            ON workflow_state(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_indicators_project_id
            ON indicators(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessment_rounds_project_id
            ON assessment_rounds(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessments_round_id
            ON assessments(round_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_assessments_indicator_id
            ON assessments(indicator_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_items_project_id
            ON action_items(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stakeholder_groups_project_id
            ON stakeholder_groups(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_stakeholder_assessments_group_id
            ON stakeholder_assessments(stakeholder_group_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_surveys_project_id
            ON surveys(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_surveys_stakeholder_group_id
            ON surveys(stakeholder_group_id)
        """)

        conn.commit()

def dict_from_row(row: sqlite3.Row) -> dict:
    """Convert a sqlite3.Row to a dictionary."""
    return dict(row)
