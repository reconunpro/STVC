"""Faster-whisper transcription engine wrapper."""

import logging
import numpy as np

log = logging.getLogger(__name__)


class Transcriber:
    """Wraps faster-whisper for batch transcription on GPU."""

    def __init__(
        self,
        model_name: str = "large-v3-turbo",
        device: str = "cuda",
        compute_type: str = "float16",
        beam_size: int = 5,
        language: str = "en",
        initial_prompt: str = "",
    ):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.language = language
        self.initial_prompt = initial_prompt
        self._model = None

    def _load_model(self):
        """Lazily load the faster-whisper model."""
        if self._model is not None:
            return

        log.info(
            "Loading model '%s' on %s (%s)...",
            self.model_name, self.device, self.compute_type,
        )
        from faster_whisper import WhisperModel

        self._model = WhisperModel(
            self.model_name,
            device=self.device,
            compute_type=self.compute_type,
        )
        log.info("Model loaded.")

    def warmup(self):
        """Load model and run a dummy transcription to warm up GPU kernels."""
        self._load_model()
        dummy = np.zeros(16000, dtype=np.float32)  # 1s of silence
        segments, _ = self._model.transcribe(
            dummy,
            beam_size=1,
            language=self.language,
        )
        # Consume the generator to actually run inference
        for _ in segments:
            pass
        log.info("Warmup complete.")

    def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe a numpy audio array (16kHz float32 mono) to text.

        Args:
            audio: Audio samples as float32 numpy array, 16kHz sample rate.

        Returns:
            Transcribed text string.
        """
        self._load_model()

        if audio.size == 0:
            return ""

        kwargs = {
            "beam_size": self.beam_size,
            "language": self.language,
            "vad_filter": True,
        }
        if self.initial_prompt:
            kwargs["initial_prompt"] = self.initial_prompt

        segments, info = self._model.transcribe(audio, **kwargs)

        text_parts = []
        for segment in segments:
            text_parts.append(segment.text.strip())

        result = " ".join(text_parts).strip()
        log.debug("Transcribed: %s", result)
        return result
