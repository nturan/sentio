"""
Fixed indicators (Bewertungsfaktoren) for change management projects.
These are predefined for ALL projects and not user-created.
"""

from typing import Dict, List, TypedDict


class IndicatorDefinition(TypedDict):
    key: str
    name: str
    description: str


# 5 Core Bewertungsfaktoren - apply to all stakeholder groups
CORE_INDICATORS: List[IndicatorDefinition] = [
    {
        "key": "orientierung_sinn",
        "name": "Orientierung & Sinn",
        "description": "Eine klare Projektvision stiftet Orientierung und foerdert die intrinsische Motivation, indem sie den tieferen Nutzen der Arbeit aufzeigt."
    },
    {
        "key": "psychologische_sicherheit",
        "name": "Psychologische Sicherheit",
        "description": "Eine offene Fehlerkultur und der Mut zu abweichenden Meinungen bilden die Basis fuer Vertrauen und Hoechstleistung im Team."
    },
    {
        "key": "empowerment",
        "name": "Empowerment",
        "description": "Wahre Befaehigung delegiert nicht nur Aufgaben, sondern uebertraegt echte Entscheidungsbefugnisse, Zeit und Autonomie an die Experten im Team."
    },
    {
        "key": "partizipation",
        "name": "Partizipation",
        "description": "Durch Transparenz und aktive Einbindung werden Betroffene zu Mitgestaltern, was Widerstaende reduziert und die Akzeptanz erhoeht."
    },
    {
        "key": "wertschaetzung",
        "name": "Wertschaetzung",
        "description": "Ein empathischer Umgang mit individuellen Beduerfnissen und gezielte Anerkennung staerken die Bindung und den Rueckhalt im Veraenderungsprozess."
    }
]

# 4 Additional indicators for Fuehrungskraefte (manually assessed)
FUEHRUNGSKRAEFTE_INDICATORS: List[IndicatorDefinition] = [
    {
        "key": "ressourcenfreigabe",
        "name": "Ressourcenfreigabe",
        "description": "Sie stellen ihre besten Leute fuer das Projekt ab, nicht nur diejenigen, die gerade 'uebrig' sind."
    },
    {
        "key": "aktive_kommunikation",
        "name": "Aktive Kommunikation",
        "description": "Die Fuehrungskraefte uebersetzen die Projektziele in die Sprache ihrer eigenen Abteilung."
    },
    {
        "key": "widerstandsmanagement",
        "name": "Widerstandsmanagement",
        "description": "Sie fangen Bedenken ihrer Mitarbeitenden ab und loesen Konflikte proaktiv, statt sie an das Projektteam zu delegieren."
    },
    {
        "key": "vorbildfunktion",
        "name": "Vorbildfunktion",
        "description": "Sie nutzen neue Tools oder Prozesse als Erste (Early Adopters)."
    }
]

# Stakeholder group types
STAKEHOLDER_GROUP_TYPES = {
    "fuehrungskraefte": {
        "name": "Fuehrungskraefte (Middle Management)",
        "description": "Fuehrungskraefte werden anhand von 4 spezifischen Indikatoren bewertet.",
        "indicators": FUEHRUNGSKRAEFTE_INDICATORS
    },
    "multiplikatoren": {
        "name": "Multiplikatoren (Change Manager/Stab)",
        "description": "Change Manager und Stabsmitarbeiter, die den Wandel aktiv vorantreiben.",
        "indicators": CORE_INDICATORS
    },
    "mitarbeitende": {
        "name": "Mitarbeitende (Die Betroffenen)",
        "description": "Mitarbeitende werden ueber Umfragen bewertet (coming soon).",
        "indicators": CORE_INDICATORS
    }
}

# Mendelow Matrix quadrants
MENDELOW_QUADRANTS = {
    ("high", "high"): {
        "name": "Key Players",
        "strategy": "Eng einbinden und aktiv managen"
    },
    ("high", "low"): {
        "name": "Keep Satisfied",
        "strategy": "Zufrieden halten, regelmaessig informieren"
    },
    ("low", "high"): {
        "name": "Keep Informed",
        "strategy": "Gut informiert halten"
    },
    ("low", "low"): {
        "name": "Monitor",
        "strategy": "Beobachten mit minimalem Aufwand"
    }
}


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
