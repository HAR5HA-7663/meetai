"""Speech-to-text transcription using faster-whisper on GPU."""

import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)


class Transcriber:
    """Real-time speech-to-text using faster-whisper with GPU acceleration.

    With 2x RTX 3090 (24GB VRAM each), we run large-v3 on GPU 0
    with float16 precision for best quality at real-time speed.
    """

    def __init__(self, model_size="large-v3", device="cuda", language="en",
                 compute_type="float16", gpu_device_index=0):
        self.model_size = model_size
        self.language = language
        self.compute_type = compute_type
        self.gpu_device_index = gpu_device_index
        self._model = None

        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Fall back to int8 on CPU
        if self.device == "cpu":
            self.compute_type = "int8"

        if self.device == "cuda":
            gpu_count = torch.cuda.device_count()
            gpu_name = torch.cuda.get_device_name(self.gpu_device_index)
            vram = torch.cuda.get_device_properties(self.gpu_device_index).total_memory / (1024**3)
            logger.info(f"GPU {self.gpu_device_index}: {gpu_name} ({vram:.1f}GB VRAM), {gpu_count} GPU(s) total")

    def _load_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            logger.info(f"Loading faster-whisper '{self.model_size}' on {self.device}:{self.gpu_device_index} ({self.compute_type})...")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                device_index=self.gpu_device_index,
                compute_type=self.compute_type,
            )
            logger.info(f"Whisper model '{self.model_size}' loaded and ready")

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
                logger.debug(f"Transcribed ({len(audio)/sample_rate:.1f}s): {result[:100]}...")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
