"""Speech-to-text transcription using faster-whisper."""

import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)


class Transcriber:
    """Real-time speech-to-text using faster-whisper."""

    def __init__(self, model_size="base.en", device="auto", language="en"):
        self.model_size = model_size
        self.language = language
        self._model = None

        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.compute_type = "float16" if self.device == "cuda" else "int8"

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Loading faster-whisper model '{self.model_size}' on {self.device} ({self.compute_type})...")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            logger.info("Whisper model loaded")

    def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> str:
        """Transcribe audio data to text.

        Args:
            audio: float32 audio array
            sample_rate: audio sample rate (should be 16000)

        Returns:
            Transcribed text string.
        """
        self._load_model()

        if len(audio) < sample_rate * 0.5:
            # Skip very short segments (<0.5s)
            return ""

        try:
            segments, info = self._model.transcribe(
                audio,
                language=self.language if not self.model_size.endswith(".en") else None,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=200,
                ),
            )

            text_parts = []
            for segment in segments:
                text = segment.text.strip()
                if text:
                    text_parts.append(text)

            result = " ".join(text_parts)
            if result:
                logger.debug(f"Transcribed: {result[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
