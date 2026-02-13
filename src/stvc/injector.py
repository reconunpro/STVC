"""Text injection via SendInput Unicode — no clipboard, no focus stealing."""

import ctypes
import ctypes.wintypes as w
import logging

log = logging.getLogger(__name__)

# Windows constants
INPUT_KEYBOARD = 1
KEYEVENTF_UNICODE = 0x0004
KEYEVENTF_KEYUP = 0x0002

# ULONG_PTR is pointer-sized (8 bytes on 64-bit)
ULONG_PTR = ctypes.POINTER(ctypes.c_ulong)


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", w.WORD),
        ("wScan", w.WORD),
        ("dwFlags", w.DWORD),
        ("time", w.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", w.LONG),
        ("dy", w.LONG),
        ("mouseData", w.DWORD),
        ("dwFlags", w.DWORD),
        ("time", w.DWORD),
        ("dwExtraInfo", ULONG_PTR),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", w.DWORD),
        ("wParamL", w.WORD),
        ("wParamH", w.WORD),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", w.DWORD),
        ("union", _INPUT_UNION),
    ]


_SendInput = ctypes.windll.user32.SendInput
_SendInput.argtypes = [w.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
_SendInput.restype = w.UINT


def _make_unicode_key(char: str, flags: int) -> INPUT:
    """Create an INPUT structure for a single Unicode character event."""
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = 0
    inp.union.ki.wScan = ord(char)
    inp.union.ki.dwFlags = flags
    inp.union.ki.time = 0
    inp.union.ki.dwExtraInfo = None
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

    n = len(events)
    array = (INPUT * n)(*events)
    size = ctypes.sizeof(INPUT)

    sent = _SendInput(n, array, size)
    if sent != n:
        log.warning("SendInput: sent %d/%d events (sizeof(INPUT)=%d)", sent, n, size)
    else:
        log.debug("SendInput: injected %d events OK", sent)

    return sent
