"""Text injection via SendInput Unicode — no clipboard, no focus stealing."""

import ctypes
from ctypes import wintypes

# Windows constants
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

# Windows structures
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]

    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT),
    ]


_SendInput = ctypes.windll.user32.SendInput
_SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
_SendInput.restype = wintypes.UINT


def _make_unicode_key(char: str, flags: int) -> INPUT:
    """Create an INPUT structure for a single Unicode character event."""
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp._input.ki.wVk = 0
    inp._input.ki.wScan = ord(char)
    inp._input.ki.dwFlags = flags
    inp._input.ki.time = 0
    inp._input.ki.dwExtraInfo = None
    return inp


def inject_text(text: str) -> int:
    """Inject text into the focused window via SendInput KEYEVENTF_UNICODE.

    Each character is sent as a key-down + key-up pair using the Unicode
    scan code. This goes directly to the focused window without touching
    the clipboard or calling SetForegroundWindow.

    Args:
        text: The text to inject.

    Returns:
        Number of input events successfully injected.
    """
    if not text:
        return 0

    events = []
    for char in text:
        # Key down
        events.append(_make_unicode_key(char, KEYEVENTF_UNICODE))
        # Key up
        events.append(_make_unicode_key(char, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP))

    array = (INPUT * len(events))(*events)
    return _SendInput(len(events), array, ctypes.sizeof(INPUT))
