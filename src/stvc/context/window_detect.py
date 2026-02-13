"""Active window detection for context-aware transcription."""

import logging
from dataclasses import dataclass

try:
    import win32gui
    import win32process
    import psutil
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False

log = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    """Information about the active foreground window.

    Attributes:
        hwnd: Window handle (integer)
        title: Window title text
        process_name: Process executable name (e.g., "Code.exe")
        exe_path: Full path to the process executable
    """
    hwnd: int
    title: str
    process_name: str
    exe_path: str


def get_active_window() -> WindowInfo:
    """Get information about the currently active foreground window.

    Uses Windows API (win32gui) to detect the foreground window and
    retrieves process information via psutil.

    Returns:
        WindowInfo with hwnd, title, process_name, and exe_path.
        Returns empty strings for fields that cannot be retrieved.

    Raises:
        RuntimeError: If win32gui/win32process/psutil are not available.
    """
    if not WIN32_AVAILABLE:
        log.error("win32gui, win32process, or psutil not available")
        raise RuntimeError("Window detection requires pywin32 and psutil")

    try:
        # Get foreground window handle
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            log.warning("No foreground window detected")
            return WindowInfo(hwnd=0, title="", process_name="", exe_path="")

        # Get window title
        title = win32gui.GetWindowText(hwnd)

        # Get process ID from window
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        # Get process information
        process_name = ""
        exe_path = ""
        try:
            proc = psutil.Process(pid)
            process_name = proc.name()
            exe_path = proc.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            log.debug(f"Could not get process info for PID {pid}: {e}")

        log.debug(f"Active window: hwnd={hwnd}, title='{title}', process='{process_name}'")
        return WindowInfo(
            hwnd=hwnd,
            title=title,
            process_name=process_name,
            exe_path=exe_path
        )

    except Exception as e:
        log.warning(f"Failed to get active window info: {e}")
        return WindowInfo(hwnd=0, title="", process_name="", exe_path="")


def detect_app_type(info: WindowInfo) -> str:
    """Detect the type of application based on window information.

    Args:
        info: WindowInfo containing process name and window title

    Returns:
        One of: "vscode", "notepadpp", "terminal", "unknown"
    """
    process_lower = info.process_name.lower()
    title_lower = info.title.lower()

    # VS Code detection
    if "code.exe" in process_lower or "vscode" in process_lower:
        return "vscode"
    if "visual studio code" in title_lower:
        return "vscode"

    # Notepad++ detection
    if "notepad++.exe" in process_lower:
        return "notepadpp"
    if "notepad++" in title_lower:
        return "notepadpp"

    # Terminal detection (Windows Terminal, cmd, PowerShell)
    terminal_processes = [
        "windowsterminal.exe",
        "cmd.exe",
        "powershell.exe",
        "pwsh.exe",
        "conhost.exe"
    ]
    if any(term in process_lower for term in terminal_processes):
        return "terminal"
    if "windows powershell" in title_lower or "command prompt" in title_lower:
        return "terminal"

    log.debug(f"Unknown app type: process='{info.process_name}', title='{info.title}'")
    return "unknown"
