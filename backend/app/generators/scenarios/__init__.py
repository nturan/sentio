"""
Scenario generators for different project stages.
"""

from .new_project import NewProjectScenario
from .three_month import ThreeMonthScenario
from .six_month import SixMonthScenario
from .ten_month import TenMonthScenario

__all__ = [
    "NewProjectScenario",
    "ThreeMonthScenario",
    "SixMonthScenario",
    "TenMonthScenario",
]

# Registry of all scenarios
SCENARIO_REGISTRY = {
    "new": NewProjectScenario,
    "3month": ThreeMonthScenario,
    "6month": SixMonthScenario,
    "10month": TenMonthScenario,
}


def get_scenario_class(name: str):
    """Get a scenario class by name."""
    return SCENARIO_REGISTRY.get(name)


def list_scenarios():
    """List all available scenario names."""
    return list(SCENARIO_REGISTRY.keys())
