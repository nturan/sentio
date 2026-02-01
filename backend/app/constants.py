"""
Fixed indicators (Bewertungsfaktoren) for change management projects.
These are predefined for ALL projects and not user-created.

All text is loaded from localized YAML files based on the LOCALE environment variable.
"""

from typing import Dict, List, TypedDict
from .prompts import load_constants


class IndicatorDefinition(TypedDict):
    key: str
    name: str
    description: str


def _load_indicators() -> tuple[List[IndicatorDefinition], List[IndicatorDefinition]]:
    """Load core and fuehrungskraefte indicators from localized constants."""
    core = load_constants("core_indicators")
    fuehrungskraefte = load_constants("fuehrungskraefte_indicators")
    return core, fuehrungskraefte


def _load_stakeholder_group_types(core_indicators, fuehrungskraefte_indicators) -> Dict:
    """Load stakeholder group types from localized constants."""
    types_data = load_constants("stakeholder_group_types")

    # Build the full structure with indicator references
    return {
        "fuehrungskraefte": {
            "name": types_data["fuehrungskraefte"]["name"],
            "description": types_data["fuehrungskraefte"]["description"],
            "indicators": fuehrungskraefte_indicators
        },
        "multiplikatoren": {
            "name": types_data["multiplikatoren"]["name"],
            "description": types_data["multiplikatoren"]["description"],
            "indicators": core_indicators
        },
        "mitarbeitende": {
            "name": types_data["mitarbeitende"]["name"],
            "description": types_data["mitarbeitende"]["description"],
            "indicators": core_indicators
        }
    }


def _load_mendelow_quadrants() -> Dict:
    """Load Mendelow quadrants from localized constants."""
    quadrants_data = load_constants("mendelow_quadrants")

    # Convert from YAML keys (high_high) to tuple keys (("high", "high"))
    return {
        ("high", "high"): quadrants_data["high_high"],
        ("high", "low"): quadrants_data["high_low"],
        ("low", "high"): quadrants_data["low_high"],
        ("low", "low"): quadrants_data["low_low"],
    }


# Load all constants from localized YAML files
CORE_INDICATORS, FUEHRUNGSKRAEFTE_INDICATORS = _load_indicators()
STAKEHOLDER_GROUP_TYPES = _load_stakeholder_group_types(CORE_INDICATORS, FUEHRUNGSKRAEFTE_INDICATORS)
MENDELOW_QUADRANTS = _load_mendelow_quadrants()


def get_indicators_for_group_type(group_type: str) -> List[IndicatorDefinition]:
    """Get the list of indicators for a given stakeholder group type."""
    if group_type not in STAKEHOLDER_GROUP_TYPES:
        return CORE_INDICATORS
    return STAKEHOLDER_GROUP_TYPES[group_type]["indicators"]


def get_all_indicator_keys() -> List[str]:
    """Get all unique indicator keys."""
    all_keys = set()
    for indicator in CORE_INDICATORS:
        all_keys.add(indicator["key"])
    for indicator in FUEHRUNGSKRAEFTE_INDICATORS:
        all_keys.add(indicator["key"])
    return list(all_keys)


def get_indicator_by_key(key: str) -> IndicatorDefinition | None:
    """Get an indicator definition by its key."""
    for indicator in CORE_INDICATORS:
        if indicator["key"] == key:
            return indicator
    for indicator in FUEHRUNGSKRAEFTE_INDICATORS:
        if indicator["key"] == key:
            return indicator
    return None
