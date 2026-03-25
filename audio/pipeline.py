"""Audio processing pipeline: capture → VAD → transcription → event bus."""

import logging
import threading

from audio.capture import AudioCapture, find_monitor_source
from audio.vad import VoiceActivityDetector
from audio.transcriber import Transcriber
from core.event_bus import event_bus

logger = logging.getLogger(__name__)


class AudioPipeline:
    """Manages the full audio processing pipeline in background threads."""

    def __init__(self, config):
        self.config = config
        audio_cfg = config.section("audio")
        trans_cfg = config.section("transcription")

        self.sample_rate = audio_cfg.get("sample_rate", 16000)

        # Find audio device
        source = audio_cfg.get("source", "auto")
        device_id = None if source == "auto" else int(source)

        self.capture = AudioCapture(
            device_id=device_id,
            sample_rate=self.sample_rate,
        )
        self.vad = VoiceActivityDetector(
            threshold=audio_cfg.get("vad_threshold", 0.5),
            sample_rate=self.sample_rate,
            silence_duration_ms=audio_cfg.get("silence_duration_ms", 1500),
        )
        self.transcriber = Transcriber(
            model_size=trans_cfg.get("model", "large-v3"),
            device=trans_cfg.get("device", "cuda"),
            language=trans_cfg.get("language", "en"),
            compute_type=trans_cfg.get("compute_type", "float16"),
            gpu_device_index=trans_cfg.get("gpu_device_index", 0),
        )

        self._running = False
        self._thread = None

    def start(self):
        """Start the audio pipeline."""
        if self._running:
            return

        if not self.capture.start():
            event_bus.error_occurred.emit("audio", "Failed to start audio capture")
            return

        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        event_bus.recording_started.emit()
        logger.info("Audio pipeline started")

    def stop(self):
        """Stop the audio pipeline."""
        self._running = False
        self.capture.stop()
        self.vad.reset()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        event_bus.recording_stopped.emit()
        logger.info("Audio pipeline stopped")

    def _process_loop(self):
        """Main processing loop: read audio → VAD → transcribe."""
        while self._running:
            chunk = self.capture.get_chunk(timeout=0.1)
            if chunk is None:
                continue

            # Run VAD
            speech_ended, speech_audio = self.vad.process_chunk(chunk)

            if speech_ended and speech_audio is not None:
                # Transcribe the speech segment
                text = self.transcriber.transcribe(speech_audio, self.sample_rate)
                if text:
                    event_bus.transcript_updated.emit(text)

    @property
    def is_running(self):
        return self._running
