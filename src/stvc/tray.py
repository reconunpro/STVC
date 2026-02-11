"""System tray icon for STVC status indication."""

import logging
import threading
from enum import Enum

from PIL import Image, ImageDraw
import pystray

log = logging.getLogger(__name__)


class TrayState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    TRANSCRIBING = "transcribing"


# Colors for each state (RGB)
STATE_COLORS = {
    TrayState.IDLE: (128, 128, 128),        # Gray
    TrayState.LISTENING: (0, 200, 0),        # Green
    TrayState.TRANSCRIBING: (255, 200, 0),   # Yellow
}


def _create_icon_image(color: tuple[int, int, int], size: int = 64) -> Image.Image:
    """Create a colored circle icon."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    margin = 4
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(*color, 255),
    )
    return image


class TrayIcon:
    """System tray icon that shows STVC state."""

    def __init__(self, on_quit=None):
        self._on_quit = on_quit
        self._state = TrayState.IDLE
        self._icon: pystray.Icon | None = None
        self._thread: threading.Thread | None = None

    def _build_menu(self) -> pystray.Menu:
        return pystray.Menu(
            pystray.MenuItem(
                lambda item: f"STVC — {self._state.value}",
                None,
                enabled=False,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._handle_quit),
        )

    def _handle_quit(self, icon, item):
        log.info("Quit requested from tray.")
        icon.stop()
        if self._on_quit:
            self._on_quit()

    def start(self):
        """Start the system tray icon in a background thread."""
        image = _create_icon_image(STATE_COLORS[TrayState.IDLE])
        self._icon = pystray.Icon(
            name="STVC",
            icon=image,
            title="STVC — idle",
            menu=self._build_menu(),
        )

        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        log.info("Tray icon started.")

    def set_state(self, state: TrayState):
        """Update the tray icon color to reflect current state."""
        self._state = state
        if self._icon is not None:
            self._icon.icon = _create_icon_image(STATE_COLORS[state])
            self._icon.title = f"STVC — {state.value}"

    def stop(self):
        """Stop the tray icon."""
        if self._icon is not None:
            self._icon.stop()
            self._icon = None
        log.info("Tray icon stopped.")
