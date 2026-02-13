"""Context-aware transcription modules for STVC."""

from .window_detect import WindowInfo, get_active_window, detect_app_type

__all__ = ["WindowInfo", "get_active_window", "detect_app_type"]
