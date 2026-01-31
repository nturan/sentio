from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

from ..database import get_connection, dict_from_row

router = APIRouter(prefix="/api", tags=["projects"])


class ProjectCreate(BaseModel):
    name: str
    icon: Optional[str] = "🚀"
    goal: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    goal: Optional[str] = None


class Project(BaseModel):
    id: str
    name: str
    icon: str
    goal: Optional[str]
    created_at: str
    updated_at: str


@router.get("/projects", response_model=List[Project])
async def list_projects():
    """List all projects."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, icon, goal, created_at, updated_at
            FROM projects
            ORDER BY updated_at DESC
            """
        )
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]


@router.post("/projects", response_model=Project)
async def create_project(project: ProjectCreate):
    """Create a new project."""
    project_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO projects (id, name, icon, goal, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (project_id, project.name, project.icon or "🚀", project.goal, now, now)
        )

        return {
            "id": project_id,
            "name": project.name,
            "icon": project.icon or "🚀",
            "goal": project.goal,
            "created_at": now,
            "updated_at": now
        }


@router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str):
    """Get a project by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, name, icon, goal, created_at, updated_at
            FROM projects
            WHERE id = ?
            """,
            (project_id,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        return dict_from_row(row)


@router.patch("/projects/{project_id}", response_model=Project)
async def update_project(project_id: str, project: ProjectUpdate):
    """Update a project."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if project exists
        cursor.execute(
            "SELECT id, name, icon, goal, created_at FROM projects WHERE id = ?",
            (project_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")

        current = dict_from_row(row)
        now = datetime.utcnow().isoformat()

        # Update only provided fields
        new_name = project.name if project.name is not None else current["name"]
        new_icon = project.icon if project.icon is not None else current["icon"]
        new_goal = project.goal if project.goal is not None else current["goal"]

        cursor.execute(
            """
            UPDATE projects
            SET name = ?, icon = ?, goal = ?, updated_at = ?
            WHERE id = ?
            """,
            (new_name, new_icon, new_goal, now, project_id)
        )

        return {
            "id": project_id,
            "name": new_name,
            "icon": new_icon,
            "goal": new_goal,
            "created_at": current["created_at"],
            "updated_at": now
        }


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its sessions."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Check if project exists
        cursor.execute(
            "SELECT id FROM projects WHERE id = ?",
            (project_id,)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")

        # Delete project (sessions will cascade delete)
        cursor.execute(
            "DELETE FROM projects WHERE id = ?",
            (project_id,)
        )

        return {"message": "Project deleted"}
