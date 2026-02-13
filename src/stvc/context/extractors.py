"""Content extraction strategies for different application types."""

import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

from .window_detect import WindowInfo

try:
    import comtypes.client
    COMTYPES_AVAILABLE = True
except ImportError:
    COMTYPES_AVAILABLE = False

log = logging.getLogger(__name__)


class BaseExtractor(ABC):
    """Abstract base class for content extractors."""

    @abstractmethod
    def extract(self, window_info: WindowInfo) -> str:
        """Extract text content from the application window.

        Args:
            window_info: Information about the active window

        Returns:
            Extracted text content, or empty string if extraction fails
        """
        pass


class FileBasedExtractor(BaseExtractor):
    """Extractor for editors that display file paths in window title.

    Works with VS Code, Notepad++, and similar editors that show
    the active file path in the window title bar.
    """

    def __init__(self, max_bytes: int = 50000):
        """Initialize file-based extractor.

        Args:
            max_bytes: Maximum bytes to read from file (default 50KB)
        """
        self.max_bytes = max_bytes

    def extract(self, window_info: WindowInfo) -> str:
        """Extract content by reading the file from disk.

        Parses the file path from the window title and reads the file.

        Args:
            window_info: Window information with title containing file path

        Returns:
            File content (up to max_bytes), or empty string on failure
        """
        try:
            file_path = self._parse_file_path(window_info.title)
            if not file_path:
                log.debug("No file path found in window title")
                return ""

            path = Path(file_path)
            if not path.exists() or not path.is_file():
                log.debug(f"File does not exist: {file_path}")
                return ""

            # Read up to max_bytes
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(self.max_bytes)

            log.debug(f"Extracted {len(content)} chars from {file_path}")
            return content

        except Exception as e:
            log.debug(f"Failed to extract file content: {e}")
            return ""

    def _parse_file_path(self, title: str) -> str:
        """Parse file path from window title.

        Handles common editor title formats:
        - VS Code: "filename - folder - Visual Studio Code"
        - Notepad++: "filename - Notepad++"
        - Generic: looks for path-like strings

        Args:
            title: Window title text

        Returns:
            File path if found, empty string otherwise
        """
        if not title:
            return ""

        # VS Code format: "filename - folder - Visual Studio Code"
        # Try to extract the full path by looking for drive letter patterns
        # Pattern: C:\path\to\file.ext or similar
        drive_pattern = r'[A-Za-z]:\\[^"<>|?*\n]+'
        matches = re.findall(drive_pattern, title)
        if matches:
            # Return the longest match (most likely the full path)
            return max(matches, key=len)

        # Notepad++ format: "filename - Notepad++"
        # Check if there's a path-like string before " - Notepad++"
        if " - Notepad++" in title:
            path_part = title.split(" - Notepad++")[0].strip()
            if Path(path_part).exists():
                return path_part

        # VS Code might just show filename without path in title
        # In this case, we can't reliably extract content
        log.debug(f"Could not parse file path from title: {title}")
        return ""


class TerminalExtractor(BaseExtractor):
    """Extractor for terminal windows using UI Automation.

    Uses Windows UI Automation to read visible text from terminal buffers.
    Works with Windows Terminal, cmd, PowerShell, etc.
    """

    def extract(self, window_info: WindowInfo) -> str:
        """Extract visible text from terminal using UI Automation.

        Args:
            window_info: Window information with terminal hwnd

        Returns:
            Visible terminal text, or empty string on failure
        """
        if not COMTYPES_AVAILABLE:
            log.debug("comtypes not available, cannot extract terminal content")
            return ""

        try:
            # Initialize UI Automation
            from comtypes.gen import UIAutomationClient

            automation = comtypes.client.CreateObject(
                "{ff48dba4-60ef-4201-aa87-54103eef594e}",
                interface=UIAutomationClient.IUIAutomation
            )

            # Get element from window handle
            element = automation.ElementFromHandle(window_info.hwnd)
            if not element:
                log.debug("Could not get UI element from window handle")
                return ""

            # Try to get text pattern
            try:
                text_pattern = element.GetCurrentPattern(UIAutomationClient.UIA_TextPatternId)
                text_range = text_pattern.DocumentRange
                text = text_range.GetText(-1)  # -1 means get all text
                log.debug(f"Extracted {len(text)} chars from terminal")
                return text
            except Exception:
                # Text pattern not available, try Value pattern
                try:
                    value_pattern = element.GetCurrentPattern(UIAutomationClient.UIA_ValuePatternId)
                    text = value_pattern.CurrentValue
                    log.debug(f"Extracted {len(text)} chars from terminal (Value pattern)")
                    return text
                except Exception:
                    log.debug("No text or value pattern available for terminal")
                    return ""

        except Exception as e:
            log.debug(f"Failed to extract terminal content: {e}")
            return ""


class GenericExtractor(BaseExtractor):
    """Fallback extractor for unknown application types.

    Returns empty string since we don't have a reliable extraction
    method for arbitrary applications.
    """

    def extract(self, window_info: WindowInfo) -> str:
        """Return empty string for unknown applications.

        Args:
            window_info: Window information (unused)

        Returns:
            Empty string
        """
        log.debug("Using generic extractor, no content extraction")
        return ""


def get_extractor(app_type: str) -> BaseExtractor:
    """Factory function to get the appropriate extractor for an app type.

    Args:
        app_type: Application type from detect_app_type()
                 ("vscode", "notepadpp", "terminal", "unknown")

    Returns:
        Appropriate BaseExtractor instance
    """
    if app_type in ("vscode", "notepadpp"):
        return FileBasedExtractor()
    elif app_type == "terminal":
        return TerminalExtractor()
    else:
        return GenericExtractor()
