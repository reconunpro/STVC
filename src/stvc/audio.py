"""Microphone audio capture using sounddevice."""

import logging
import threading
import numpy as np
import sounddevice as sd

log = logging.getLogger(__name__)

SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = "float32"


def list_audio_devices() -> list[dict]:
    """List all available audio input devices.

    Returns:
        List of dicts with keys: index, name, channels, sample_rate.
        Only includes devices that support input (have input channels > 0).
    """
    devices = []
    try:
        device_list = sd.query_devices()
        for idx, device in enumerate(device_list):
            # Only include devices with input channels
            if device.get('max_input_channels', 0) > 0:
                devices.append({
                    'index': idx,
                    'name': device.get('name', 'Unknown'),
                    'channels': device.get('max_input_channels', 0),
                    'sample_rate': device.get('default_samplerate', 16000),
                })
    except Exception as e:
        log.warning(f"Failed to query audio devices: {e}")

    return devices


class AudioRecorder:
    """Records audio from the microphone into a buffer.

    Usage:
        recorder = AudioRecorder()
        recorder.start()
        # ... user speaks ...
        recorder.stop()
        audio = recorder.get_audio()  # numpy float32 array, 16kHz mono
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS, device: int | str | None = None):
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self._buffer: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None
        self._lock = threading.Lock()
        self._recording = False

    def _callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Called by sounddevice for each audio chunk."""
        if status:
            log.warning("Audio callback status: %s", status)
        with self._lock:
            if self._recording:
                self._buffer.append(indata.copy())

    def start(self):
        """Start recording audio from the configured microphone device."""
        with self._lock:
            self._buffer.clear()
            self._recording = True

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=DTYPE,
            callback=self._callback,
            device=self.device,
        )
        self._stream.start()
        log.info("Recording started (device=%s).", self.device if self.device is not None else "default")

    def stop(self):
        """Stop recording and close the audio stream."""
        with self._lock:
            self._recording = False

        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        log.info("Recording stopped.")

    def get_audio(self) -> np.ndarray:
        """Return recorded audio as a 1-D float32 numpy array.

        Returns:
            Audio samples as float32 numpy array (16kHz mono).
            Empty array if nothing was recorded.
        """
        with self._lock:
            if not self._buffer:
                return np.array([], dtype=np.float32)
            audio = np.concatenate(self._buffer, axis=0).flatten()
        return audio
