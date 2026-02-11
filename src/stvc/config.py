"""STVC configuration loader."""

import os
import json
from pathlib import Path

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None

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
    "hotkey": {
        "push_to_talk": "alt+e",
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
