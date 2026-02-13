"""STVC configuration loader."""

import os
import json
import logging
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

try:
    import tomli_w
except ImportError:
    tomli_w = None

STVC_DIR = Path(os.path.expanduser("~/.stvc"))
CONFIG_PATH = STVC_DIR / "config.toml"
DICTIONARY_PATH = STVC_DIR / "dictionary.json"

DEFAULTS = {
    "general": {
        "language": "en",
    },
    "model": {
        "name": "large-v3-turbo",
        "device": "cuda",
        "compute_type": "float16",
        "beam_size": 5,
    },
    "audio": {
        "device": "",
    },
    "hotkey": {
        "push_to_talk": "ctrl+f13",
    },
    "injection": {
        "method": "sendinput",
    },
    "post_processing": {
        "remove_filler_words": True,
        "fix_question_marks": True,
    },
    "dictionary": {
        "path": str(DICTIONARY_PATH),
    },
    "context": {
        "enabled": True,
    },
}

DEFAULT_DICTIONARY = {
    "version": 1,
    "description": "Custom vocabulary for STVC speech recognition",
    "categories": {
        "ai_tools": [
            "Claude Code", "Claude", "Anthropic", "MCP",
            "Model Context Protocol", "Copilot", "ChatGPT"
        ],
        "languages": [
            "TypeScript", "JavaScript", "Python", "Rust", "Go"
        ],
        "frameworks": [
            "React", "Next.js", "FastAPI", "Express", "Node.js",
            "Django", "Flask", "Svelte", "Vue"
        ],
        "tools": [
            "Docker", "Kubernetes", "PostgreSQL", "MongoDB",
            "Redis", "npm", "pip", "git", "GitHub", "VS Code"
        ],
        "protocols": [
            "REST", "GraphQL", "WebSocket", "JSON", "API",
            "OAuth", "JWT", "HTTPS", "SSH"
        ],
        "programming": [
            "async", "await", "boolean", "refactor", "middleware",
            "endpoint", "schema", "mutation", "resolver"
        ],
        "custom": [],
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base, preserving nested structure."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config() -> dict:
    """Load config from ~/.stvc/config.toml, falling back to defaults."""
    config = DEFAULTS.copy()

    if CONFIG_PATH.exists() and tomllib is not None:
        with open(CONFIG_PATH, "rb") as f:
            user_config = tomllib.load(f)
        config = _deep_merge(config, user_config)

    return config


def load_dictionary(path: str | None = None) -> str:
    """Load dictionary terms and return as comma-separated string for initial_prompt."""
    dict_path = Path(os.path.expanduser(path or str(DICTIONARY_PATH)))

    if not dict_path.exists():
        # Create default dictionary
        STVC_DIR.mkdir(parents=True, exist_ok=True)
        with open(dict_path, "w") as f:
            json.dump(DEFAULT_DICTIONARY, f, indent=2)

    with open(dict_path) as f:
        data = json.load(f)

    terms = []
    for category_terms in data.get("categories", {}).values():
        terms.extend(category_terms)

    return ", ".join(terms)


def ensure_config_dir():
    """Create ~/.stvc/ directory and default config if they don't exist."""
    STVC_DIR.mkdir(parents=True, exist_ok=True)

    if not DICTIONARY_PATH.exists():
        with open(DICTIONARY_PATH, "w") as f:
            json.dump(DEFAULT_DICTIONARY, f, indent=2)


def save_config(config: dict) -> None:
    """Save config dict to ~/.stvc/config.toml.

    Args:
        config: Configuration dictionary to serialize

    Raises:
        ImportError: If tomli_w is not installed
    """
    if tomli_w is None:
        logging.error("tomli_w not installed, cannot save config")
        raise ImportError("tomli_w is required for saving config. Install with: pip install tomli-w")

    try:
        STVC_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, "wb") as f:
            tomli_w.dump(config, f)
        logging.info(f"Config saved to {CONFIG_PATH}")
    except Exception as e:
        logging.warning(f"Failed to save config to {CONFIG_PATH}: {e}")


def save_dictionary(data: dict) -> None:
    """Save dictionary data to ~/.stvc/dictionary.json.

    Args:
        data: Dictionary data structure with categories
    """
    try:
        STVC_DIR.mkdir(parents=True, exist_ok=True)
        with open(DICTIONARY_PATH, "w") as f:
            json.dump(data, f, indent=2)
        logging.info(f"Dictionary saved to {DICTIONARY_PATH}")
    except Exception as e:
        logging.warning(f"Failed to save dictionary to {DICTIONARY_PATH}: {e}")


def load_dictionary_raw(path: str | None = None) -> dict:
    """Load dictionary as raw dict structure for editor UI.

    Args:
        path: Optional path to dictionary file, defaults to ~/.stvc/dictionary.json

    Returns:
        Dictionary data structure with version, description, and categories
    """
    dict_path = Path(os.path.expanduser(path or str(DICTIONARY_PATH)))

    if not dict_path.exists():
        # Create default dictionary
        STVC_DIR.mkdir(parents=True, exist_ok=True)
        with open(dict_path, "w") as f:
            json.dump(DEFAULT_DICTIONARY, f, indent=2)
        return DEFAULT_DICTIONARY.copy()

    try:
        with open(dict_path) as f:
            return json.load(f)
    except Exception as e:
        logging.warning(f"Failed to load dictionary from {dict_path}: {e}")
        return DEFAULT_DICTIONARY.copy()
