"""STVC main application — ties all components together."""

import logging
import signal
import sys
import threading
import time
import tkinter as tk

from stvc.config import load_config, load_dictionary, ensure_config_dir
from stvc.audio import AudioRecorder
from stvc.transcriber import Transcriber
from stvc.postprocess import process as postprocess
from stvc.injector import inject_text
from stvc.hotkey import HotkeyListener
from stvc.tray import TrayIcon, TrayState
from stvc.settings import SettingsWindow
from stvc.context.window_detect import get_active_window, detect_app_type
from stvc.context.extractors import get_extractor
from stvc.context.term_parser import extract_terms
from stvc.context.merger import build_prompt

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

        # Tkinter root for settings window (hidden)
        self._tk_root: tk.Tk | None = None
        self._settings_window: SettingsWindow | None = None

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

            # Context-aware prompt building
            context_enabled = self._config.get("context", {}).get("enabled", True)
            merged_prompt = None

            if context_enabled:
                try:
                    # Get active window
                    window_info = get_active_window()
                    app_type = detect_app_type(window_info)
                    log.debug(f"Active window: {app_type} - {window_info.title}")

                    # Extract content
                    extractor = get_extractor(app_type)
                    content = extractor.extract(window_info)

                    if content:
                        # Extract terms
                        context_terms = extract_terms(content, max_terms=50)
                        log.debug(f"Extracted {len(context_terms)} context terms: {context_terms[:10]}")

                        # Build merged prompt
                        base_prompt = self._transcriber.initial_prompt
                        merged_prompt = build_prompt(base_prompt, context_terms, max_tokens=224)
                    else:
                        log.debug("No content extracted from active window")

                except Exception as e:
                    log.debug(f"Context extraction failed, using base dictionary: {e}")

            # Transcribe with context-aware prompt or base prompt
            text = self._transcriber.transcribe(audio, initial_prompt=merged_prompt)
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

    def _on_settings(self):
        """Open settings window (called from tray thread, schedule on main thread)."""
        log.info("Settings requested, scheduling on main thread.")
        # Schedule window creation on main thread (tkinter requirement)
        if self._tk_root:
            self._tk_root.after(0, self._open_settings_window)

    def _open_settings_window(self):
        """Open settings window (runs on main thread)."""
        log.info("Opening settings window.")
        if self._settings_window is None:
            self._settings_window = SettingsWindow(
                parent=self._tk_root,
                config=self._config,
                on_hotkey_change=self._on_hotkey_changed,
                on_device_change=self._on_device_changed,
                on_dictionary_change=self._on_dictionary_changed,
            )
        self._settings_window.show()

    def _on_hotkey_changed(self, new_hotkey: str):
        """Handle hotkey change from settings."""
        log.info(f"Hotkey changed to: {new_hotkey}")
        if self._hotkey:
            self._hotkey.update_hotkey(new_hotkey)

    def _on_device_changed(self, new_device: str):
        """Handle audio device change from settings."""
        log.info(f"Audio device changed to: {new_device}")
        # Recreate recorder with new device
        if self._recorder:
            self._recorder = AudioRecorder(device=int(new_device))

    def _on_dictionary_changed(self, new_dict: str):
        """Handle dictionary change from settings."""
        log.info("Dictionary changed, updating transcriber prompt.")
        if self._transcriber:
            self._transcriber.update_base_prompt(new_dict)

    def start(self):
        """Initialize all components and start STVC."""
        ensure_config_dir()

        model_cfg = self._config.get("model", {})
        dict_path = self._config.get("dictionary", {}).get("path")
        hotkey_cfg = self._config.get("hotkey", {})
        audio_cfg = self._config.get("audio", {})

        # Create hidden Tkinter root for settings window
        self._tk_root = tk.Tk()
        self._tk_root.withdraw()  # Hide the root window

        # Audio recorder
        device_index = audio_cfg.get("device")
        if device_index:
            self._recorder = AudioRecorder(device=int(device_index))
        else:
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

        # System tray icon with settings callback
        self._tray = TrayIcon(on_quit=self.stop, on_settings=self._on_settings)
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
        if self._tk_root:
            try:
                self._tk_root.quit()
                self._tk_root.destroy()
            except Exception:
                pass

        log.info("STVC stopped.")

    def wait(self):
        """Block until shutdown is requested."""
        try:
            while not self._shutdown.is_set():
                # Pump tkinter event loop to handle settings window
                if self._tk_root:
                    try:
                        self._tk_root.update()
                    except Exception:
                        pass
                self._shutdown.wait(timeout=0.1)
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
