"""
Prompt loader utility for internationalized agent prompts.

Loads prompts and constants from YAML files based on the LOCALE environment variable.
"""
import os
import yaml
from pathlib import Path
from functools import lru_cache
from typing import Any
from dotenv import load_dotenv

# Load .env from project root (in case this module is imported before main.py)
root_env = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(root_env)

# Get locale from environment variable, default to English
LOCALE = os.getenv("LOCALE", "en")

# Base path for prompt files
PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=32)
def load_prompt(agent: str, key: str = "system") -> str:
    """
    Load a prompt from a YAML file based on the current locale.

    Args:
        agent: The agent name (e.g., 'chat', 'survey', 'recommendations')
        key: The prompt key within the YAML file (default: 'system')

    Returns:
        The prompt string

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
        KeyError: If the key doesn't exist in the prompt file
    """
    path = PROMPTS_DIR / LOCALE / f"{agent}.yaml"

    # Fall back to English if locale file doesn't exist
    if not path.exists():
        path = PROMPTS_DIR / "en" / f"{agent}.yaml"

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if key not in data:
        raise KeyError(f"Key '{key}' not found in {path}")

    return data[key]


@lru_cache(maxsize=32)
def load_constants(key: str) -> Any:
    """
    Load localized constants from the constants.yaml file.

    Args:
        key: The constants key (e.g., 'core_indicators', 'stakeholder_group_types')

    Returns:
        The constants data (list or dict depending on the key)
    """
    path = PROMPTS_DIR / LOCALE / "constants.yaml"

    # Fall back to English if locale file doesn't exist
    if not path.exists():
        path = PROMPTS_DIR / "en" / "constants.yaml"

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if key not in data:
        raise KeyError(f"Key '{key}' not found in constants.yaml")

    return data[key]


def get_locale() -> str:
    """Return the current locale."""
    return LOCALE


def clear_cache():
    """Clear the prompt cache. Useful for testing or locale changes."""
    load_prompt.cache_clear()
    load_constants.cache_clear()
