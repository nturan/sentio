"""
Development seed router for generating test/demo data.

WARNING: This router should only be enabled in development environments.
"""

from fastapi import APIRouter, HTTPException
from typing import List

from ..database import get_connection
from ..generators.scenarios import (
    SCENARIO_REGISTRY,
    get_scenario_class,
    list_scenarios,
)
from ..factories.base import BaseFactory

router = APIRouter(prefix="/api/dev", tags=["development"])


@router.get("/scenarios")
async def list_available_scenarios():
    """List all available scenarios with their descriptions."""
    scenarios = []
    for name, scenario_class in SCENARIO_REGISTRY.items():
        scenarios.append({
            "name": name,
            "description": scenario_class.SCENARIO_DESCRIPTION,
            "project_age_days": scenario_class.PROJECT_AGE_DAYS,
            "num_impulses": scenario_class.NUM_IMPULSES,
            "num_recommendations": scenario_class.NUM_RECOMMENDATIONS,
            "num_sessions": scenario_class.NUM_SESSIONS,
        })
    return {"scenarios": scenarios}


@router.post("/seed/{scenario_name}")
async def seed_scenario(scenario_name: str):
    """
    Generate a single scenario.

    Available scenarios:
    - new: Fresh project (3 days old, no history)
    - 3month: 3-month project with initial impulses and recommendations
    - 6month: 6-month project with substantial history
    - 10month: 10-month project with rich history and active crisis
    """
    scenario_class = get_scenario_class(scenario_name)

    if not scenario_class:
        available = list_scenarios()
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{scenario_name}'. Available: {', '.join(available)}"
        )

    try:
        # Reset sequence counters for clean generation
        BaseFactory.reset_sequences()

        with get_connection() as conn:
            result = scenario_class.generate(conn)

        return {
            "success": True,
            "message": f"Scenario '{scenario_name}' created successfully",
            "summary": result.get("summary", {}),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate scenario: {str(e)}"
        )


@router.post("/seed/all")
async def seed_all_scenarios():
    """Generate all 4 scenarios at once."""
    results = []
    errors = []

    # Reset sequence counters once at start
    BaseFactory.reset_sequences()

    for name in list_scenarios():
        scenario_class = get_scenario_class(name)
        try:
            with get_connection() as conn:
                result = scenario_class.generate(conn)
                results.append({
                    "scenario": name,
                    "success": True,
                    "summary": result.get("summary", {}),
                })
        except Exception as e:
            errors.append({
                "scenario": name,
                "success": False,
                "error": str(e),
            })

    return {
        "success": len(errors) == 0,
        "message": f"Created {len(results)} scenarios, {len(errors)} failed",
        "results": results,
        "errors": errors,
    }


@router.delete("/clear")
async def clear_all_data():
    """
    Clear ALL data from the database.

    WARNING: This will delete all projects, sessions, messages,
    stakeholder groups, assessments, and recommendations.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Delete in order respecting foreign keys
            # (children first, then parents)
            tables_to_clear = [
                "messages",
                "chat_sessions",
                "stakeholder_assessments",
                "stakeholder_groups",
                "surveys",
                "recommendations",
                "action_items",
                "assessments",
                "assessment_rounds",
                "indicators",
                "workflow_state",
                "documents",
                "projects",
            ]

            deleted_counts = {}
            for table in tables_to_clear:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                cursor.execute(f"DELETE FROM {table}")
                deleted_counts[table] = count

        # Reset factory sequences
        BaseFactory.reset_sequences()

        return {
            "success": True,
            "message": "All data cleared successfully",
            "deleted": deleted_counts,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear data: {str(e)}"
        )


@router.delete("/clear/{project_id}")
async def clear_project(project_id: str):
    """Delete a single project and all its related data."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if project exists
            cursor.execute("SELECT id, name FROM projects WHERE id = ?", (project_id,))
            project = cursor.fetchone()

            if not project:
                raise HTTPException(status_code=404, detail="Project not found")

            project_name = project["name"]

            # Delete the project (cascades will handle related data)
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))

        return {
            "success": True,
            "message": f"Project '{project_name}' deleted successfully",
            "project_id": project_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete project: {str(e)}"
        )
