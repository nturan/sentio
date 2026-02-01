"""
MCP Tools for Sentio.

Each module provides tools for a specific entity type:
- projects: Project CRUD operations
- stakeholders: Stakeholder group management
- assessments: Stakeholder assessments and impulse history
- recommendations: AI-generated recommendations
- sessions: Chat session management
- surveys: Survey generation context
- documents: Document management
- workflow: Workflow state and dashboard data
"""

from . import projects
from . import stakeholders
from . import assessments
from . import recommendations
from . import sessions
from . import surveys
from . import documents
from . import workflow

__all__ = [
    "projects",
    "stakeholders",
    "assessments",
    "recommendations",
    "sessions",
    "surveys",
    "documents",
    "workflow",
]
