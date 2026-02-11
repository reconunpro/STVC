"""STVC main application — ties all components together."""

import logging
import signal
import sys
import threading
import time

from stvc.config import load_config, load_dictionary, ensure_config_dir
from stvc.audio import AudioRecorder
from stvc.transcriber import Transcriber
from stvc.postprocess import process as postprocess
from stvc.injector import inject_text
from stvc.hotkey import HotkeyListener
from stvc.tray import TrayIcon, TrayState

log = logging.getLogger(__name__)


class STVCApp:
    """Main STVC application orchestrator.

    Coordinates: hotkey -> audio capture -> transcription -> post-processing -> injection.
    """

    def __init__(self):
        self._config = load_config()
        self._shutdown = threading.Event()

        # Components (initialized in start())
        self._recorder: AudioRecorder | None = None
        self._transcriber: Transcriber | None = None
        self._hotkey: HotkeyListener | None = None
        self._tray: TrayIcon | None = None
        self._processing_lock = threading.Lock()

    def _on_ptt_press(self):
        """Called when push-to-talk hotkey is pressed — start recording."""
        if not self._processing_lock.acquire(blocking=False):
            log.debug("Already processing, ignoring press.")
            return

        try:
            log.info("PTT pressed — recording.")
            if self._tray:
                self._tray.set_state(TrayState.LISTENING)
            self._recorder.start()
        except Exception:
            self._processing_lock.release()
            raise

    def _on_ptt_release(self):
        """Called when push-to-talk hotkey is released — transcribe and inject."""
        try:
            log.info("PTT released — transcribing.")
            self._recorder.stop()

            if self._tray:
                self._tray.set_state(TrayState.TRANSCRIBING)

            audio = self._recorder.get_audio()
            if audio.size == 0:
                log.info("No audio captured.")
                return

            # Transcribe
            text = self._transcriber.transcribe(audio)
            if not text:
                log.info("No speech detected.")
                return

            # Post-process
            pp_config = self._config.get("post_processing", {})
            text = postprocess(
                text,
                fix_questions=pp_config.get("fix_question_marks", True),
                remove_fillers=pp_config.get("remove_filler_words", True),
            )

            if not text:
                log.info("Text empty after post-processing.")
                return

            # Inject into focused window
            log.info("Injecting: %s", text[:80])
            inject_text(text)

        except Exception:
            log.exception("Error during transcription/injection.")
        finally:
            if self._tray:
                self._tray.set_state(TrayState.IDLE)
            self._processing_lock.release()

    def start(self):
        """Initialize all components and start STVC."""
        ensure_config_dir()

        model_cfg = self._config.get("model", {})
        dict_path = self._config.get("dictionary", {}).get("path")
        hotkey_cfg = self._config.get("hotkey", {})

        # Audio recorder
        self._recorder = AudioRecorder()

        # Transcription engine
        initial_prompt = load_dictionary(dict_path)
        self._transcriber = Transcriber(
            model_name=model_cfg.get("name", "large-v3-turbo"),
            device=model_cfg.get("device", "cuda"),
            compute_type=model_cfg.get("compute_type", "float16"),
            beam_size=model_cfg.get("beam_size", 5),
            language=self._config.get("general", {}).get("language", "en"),
            initial_prompt=initial_prompt,
        )

        # Warm up model (loads into GPU)
        log.info("Warming up transcription model...")
        self._transcriber.warmup()

        # System tray icon
        self._tray = TrayIcon(on_quit=self.stop)
        self._tray.start()

        # Hotkey listener
        self._hotkey = HotkeyListener(
            hotkey_str=hotkey_cfg.get("push_to_talk", "alt+e"),
            on_press=self._on_ptt_press,
            on_release=self._on_ptt_release,
        )
        self._hotkey.start()

        log.info("STVC is running. Press %s to dictate. Ctrl+C to exit.", hotkey_cfg.get("push_to_talk", "alt+e"))

    def stop(self):
        """Shut down all components."""
        log.info("Shutting down STVC...")
        self._shutdown.set()

        if self._hotkey:
            self._hotkey.stop()
        if self._tray:
            self._tray.stop()

        log.info("STVC stopped.")

    def wait(self):
        """Block until shutdown is requested."""
        try:
            while not self._shutdown.is_set():
                self._shutdown.wait(timeout=1.0)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


def main():
    """Entry point for STVC."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    app = STVCApp()
    signal.signal(signal.SIGINT, lambda *_: app.stop())

    app.start()
    app.wait()


if __name__ == "__main__":
    main()
