"""Global push-to-talk hotkey listener using pynput."""

import logging
import threading
from typing import Callable

from pynput import keyboard

log = logging.getLogger(__name__)


def parse_hotkey(hotkey_str: str) -> tuple[set[str], str]:
    """Parse a hotkey string like 'alt+e' into modifier set and key.

    Args:
        hotkey_str: Hotkey string, e.g. 'alt+e', 'ctrl+shift+r'.

    Returns:
        Tuple of (modifier_keys, main_key).
    """
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    main_key = parts[-1]
    modifiers = set(parts[:-1])
    return modifiers, main_key


MODIFIER_MAP = {
    "alt": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r},
    "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
}


class HotkeyListener:
    """Listens for a push-to-talk hotkey combination.

    Calls on_press when the hotkey is pressed, on_release when released.
    Uses pynput's low-level keyboard hook (no admin required).
    """

    def __init__(
        self,
        hotkey_str: str = "alt+e",
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
    ):
        self._modifiers, self._key = parse_hotkey(hotkey_str)
        self._on_press = on_press
        self._on_release = on_release
        self._pressed_modifiers: set[keyboard.Key] = set()
        self._hotkey_active = False
        self._listener: keyboard.Listener | None = None

    def _modifier_match(self) -> bool:
        """Check if all required modifiers are currently pressed."""
        for mod_name in self._modifiers:
            mod_keys = MODIFIER_MAP.get(mod_name, set())
            if not self._pressed_modifiers & mod_keys:
                return False
        return True

    def _get_key_char(self, key) -> str | None:
        """Extract the character from a key event."""
        try:
            return key.char.lower() if key.char else None
        except AttributeError:
            return None

    def _handle_press(self, key):
        """Handle key press events."""
        # Track modifier state
        for mod_keys in MODIFIER_MAP.values():
            if key in mod_keys:
                self._pressed_modifiers.add(key)
                return

        # Check if main key matches with all modifiers held
        char = self._get_key_char(key)
        if char == self._key and self._modifier_match() and not self._hotkey_active:
            self._hotkey_active = True
            log.debug("PTT hotkey pressed.")
            if self._on_press:
                self._on_press()

    def _handle_release(self, key):
        """Handle key release events."""
        # Track modifier release
        for mod_keys in MODIFIER_MAP.values():
            if key in mod_keys:
                self._pressed_modifiers.discard(key)
                # If a required modifier is released while hotkey active, trigger release
                if self._hotkey_active and not self._modifier_match():
                    self._hotkey_active = False
                    log.debug("PTT modifier released.")
                    if self._on_release:
                        self._on_release()
                return

        # Check if main key released
        char = self._get_key_char(key)
        if char == self._key and self._hotkey_active:
            self._hotkey_active = False
            log.debug("PTT hotkey released.")
            if self._on_release:
                self._on_release()

    def start(self):
        """Start listening for the hotkey in a background thread."""
        self._listener = keyboard.Listener(
            on_press=self._handle_press,
            on_release=self._handle_release,
        )
        self._listener.start()
        log.info("Hotkey listener started (hotkey: %s+%s).", "+".join(self._modifiers), self._key)

    def stop(self):
        """Stop the hotkey listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        log.info("Hotkey listener stopped.")
