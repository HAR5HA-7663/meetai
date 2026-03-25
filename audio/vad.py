"""Voice Activity Detection using Silero VAD."""

import logging
import numpy as np
import torch

logger = logging.getLogger(__name__)


class VoiceActivityDetector:
    """Detects speech in audio chunks using Silero VAD model."""

    def __init__(self, threshold=0.5, sample_rate=16000, silence_duration_ms=1500):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.silence_chunks = int(silence_duration_ms / 30)  # chunks of ~30ms
        self._model = None
        self._silent_count = 0
        self._speech_buffer = []
        self._is_speaking = False

    def _load_model(self):
        if self._model is None:
            logger.info("Loading Silero VAD model...")
            self._model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                trust_repo=True,
            )
            self._model.eval()
            logger.info("Silero VAD model loaded")

    def process_chunk(self, audio_chunk: np.ndarray) -> tuple[bool, np.ndarray | None]:
        """Process an audio chunk and detect speech.

        Args:
            audio_chunk: float32 audio data at 16kHz

        Returns:
            (speech_ended, speech_audio):
                speech_ended=True when a complete speech segment is ready.
                speech_audio contains the accumulated audio, or None.
        """
        self._load_model()

        # Silero VAD expects 512 samples at 16kHz (32ms)
        tensor = torch.from_numpy(audio_chunk).float()
        if len(tensor) < 512:
            # Pad short chunks
            tensor = torch.nn.functional.pad(tensor, (0, 512 - len(tensor)))

        # Run VAD
        with torch.no_grad():
            speech_prob = self._model(tensor[:512], self.sample_rate).item()

        is_speech = speech_prob >= self.threshold

        if is_speech:
            self._silent_count = 0
            self._speech_buffer.append(audio_chunk)
            if not self._is_speaking:
                self._is_speaking = True
                logger.debug("Speech started")
            return False, None
        else:
            if self._is_speaking:
                self._silent_count += 1
                self._speech_buffer.append(audio_chunk)  # Include trailing silence

                if self._silent_count >= self.silence_chunks:
                    # Speech segment complete
                    self._is_speaking = False
                    self._silent_count = 0
                    speech_audio = np.concatenate(self._speech_buffer)
                    self._speech_buffer = []
                    logger.debug(f"Speech ended ({len(speech_audio) / self.sample_rate:.1f}s)")
                    return True, speech_audio
            return False, None

    def reset(self):
        """Reset VAD state."""
        self._silent_count = 0
        self._speech_buffer = []
        self._is_speaking = False
        if self._model is not None:
            self._model.reset_states()
