"""Global push-to-talk hotkey listener using pynput."""

import logging
from typing import Callable

from pynput import keyboard

log = logging.getLogger(__name__)

MODIFIER_MAP = {
    "alt": {keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r},
    "ctrl": {keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r},
    "shift": {keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r},
}

# Map special key names to pynput Key objects
SPECIAL_KEY_MAP = {
    "f1": keyboard.Key.f1, "f2": keyboard.Key.f2, "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4, "f5": keyboard.Key.f5, "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7, "f8": keyboard.Key.f8, "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10, "f11": keyboard.Key.f11, "f12": keyboard.Key.f12,
    "space": keyboard.Key.space,
    "tab": keyboard.Key.tab,
    "enter": keyboard.Key.enter,
}

# F13-F24 don't have pynput Key constants — match by virtual key code
# F13=0x7C(124), F14=0x7D(125), ..., F24=0x87(135)
SPECIAL_VK_MAP = {f"f{i}": 0x7C + (i - 13) for i in range(13, 25)}


def parse_hotkey(hotkey_str: str) -> tuple[set[str], str]:
    """Parse a hotkey string like 'ctrl+f13' into modifier set and key.

    Returns:
        Tuple of (modifier_keys, main_key).
    """
    parts = [p.strip().lower() for p in hotkey_str.split("+")]
    main_key = parts[-1]
    modifiers = set(parts[:-1])
    return modifiers, main_key


class HotkeyListener:
    """Listens for a push-to-talk hotkey combination.

    Calls on_press when the hotkey is pressed, on_release when released.
    Uses pynput's low-level keyboard hook (no admin required).
    """

    def __init__(
        self,
        hotkey_str: str = "ctrl+f13",
        on_press: Callable[[], None] | None = None,
        on_release: Callable[[], None] | None = None,
    ):
        self._modifiers, self._key = parse_hotkey(hotkey_str)
        self._on_press = on_press
        self._on_release = on_release
        self._pressed_modifiers: set[keyboard.Key] = set()
        self._hotkey_active = False
        self._listener: keyboard.Listener | None = None

        # Resolve the main key to a pynput Key or vk code
        self._special_key = SPECIAL_KEY_MAP.get(self._key)
        self._special_vk = SPECIAL_VK_MAP.get(self._key)

    def _modifier_match(self) -> bool:
        """Check if all required modifiers are currently pressed."""
        for mod_name in self._modifiers:
            mod_keys = MODIFIER_MAP.get(mod_name, set())
            if not self._pressed_modifiers & mod_keys:
                return False
        return True

    def _key_matches(self, key) -> bool:
        """Check if the pressed key matches our target main key."""
        # Match pynput Key enum (F1-F12, space, etc.)
        if self._special_key is not None:
            return key == self._special_key

        # Match by virtual key code (F13-F24)
        if self._special_vk is not None:
            vk = getattr(key, 'vk', None) or getattr(key, '_scan', None)
            if vk is None:
                try:
                    vk = key.value.vk if hasattr(key, 'value') else None
                except Exception:
                    pass
            return vk == self._special_vk

        # Match character key
        try:
            return key.char and key.char.lower() == self._key
        except AttributeError:
            return False

    def _handle_press(self, key):
        """Handle key press events."""
        # Track modifier state
        for mod_keys in MODIFIER_MAP.values():
            if key in mod_keys:
                self._pressed_modifiers.add(key)
                return

        # Check if main key matches with all modifiers held
        if self._key_matches(key) and self._modifier_match() and not self._hotkey_active:
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
                if self._hotkey_active and not self._modifier_match():
                    self._hotkey_active = False
                    log.debug("PTT modifier released.")
                    if self._on_release:
                        self._on_release()
                return

        # Check if main key released
        if self._key_matches(key) and self._hotkey_active:
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
        log.info("Hotkey listener started (hotkey: %s).",
                 "+".join(list(self._modifiers) + [self._key]))

    def stop(self):
        """Stop the hotkey listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        log.info("Hotkey listener stopped.")
