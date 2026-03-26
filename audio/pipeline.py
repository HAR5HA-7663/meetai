"""Audio processing pipeline: capture → VAD → live transcription → AI trigger.

Two-stage transcription:
1. While someone is speaking: transcribe every ~2s of accumulated audio → show live interim text
2. When they stop speaking: transcribe the full segment → emit final text + trigger AI
"""

import logging
import threading
import time
import numpy as np

from audio.capture import AudioCapture
from audio.vad import VoiceActivityDetector
from audio.transcriber import Transcriber
from core.event_bus import event_bus

logger = logging.getLogger(__name__)

# How often to do interim transcription while speech is ongoing (seconds)
INTERIM_INTERVAL = 1.5


class AudioPipeline:
    """Manages the full audio pipeline with live streaming transcription."""

    def __init__(self, config):
        self.config = config
        audio_cfg = config.section("audio")
        trans_cfg = config.section("transcription")

        self.sample_rate = audio_cfg.get("sample_rate", 16000)

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
        if self._running:
            return
        if not self.capture.start():
            event_bus.error_occurred.emit("audio", "Failed to start audio capture")
            return
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
        event_bus.recording_started.emit()
        logger.info("Audio pipeline started (live streaming mode)")

    def stop(self):
        self._running = False
        self.capture.stop()
        self.vad.reset()
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        event_bus.recording_stopped.emit()
        logger.info("Audio pipeline stopped")

    def _process_loop(self):
        """Main loop: collect audio, do VAD, live-transcribe during speech, final on silence."""
        speech_buffer = []          # all chunks for current speech turn
        last_interim_time = 0       # when we last did an interim transcription
        interim_offset = 0          # how many samples we already transcribed as interim

        while self._running:
            chunk = self.capture.get_chunk(timeout=0.1)
            if chunk is None:
                continue

            # Run VAD on this chunk
            speech_ended, full_speech = self.vad.process_chunk(chunk)

            if self.vad._is_speaking:
                # Speech is ongoing — accumulate and do interim transcription
                speech_buffer.append(chunk)
                now = time.time()

                if now - last_interim_time >= INTERIM_INTERVAL and len(speech_buffer) > 0:
                    # Do interim transcription on accumulated audio so far
                    all_audio = np.concatenate(speech_buffer)
                    if len(all_audio) > self.sample_rate * 0.5:  # at least 0.5s
                        interim_text = self.transcriber.transcribe(all_audio, self.sample_rate)
                        if interim_text:
                            event_bus.transcript_interim.emit(interim_text)
                            logger.debug(f"Interim: {interim_text[:80]}...")
                    last_interim_time = now

            if speech_ended and full_speech is not None:
                # Speaker stopped — do final transcription on the full segment
                final_text = self.transcriber.transcribe(full_speech, self.sample_rate)
                if final_text:
                    # Emit final transcript (replaces interim) and trigger AI
                    event_bus.transcript_final.emit(final_text)
                    event_bus.transcript_updated.emit(final_text)
                    event_bus.speech_turn_ended.emit(final_text)
                    logger.info(f"Final: {final_text[:100]}...")

                # Reset for next speech turn
                speech_buffer = []
                last_interim_time = 0
                interim_offset = 0

    @property
    def is_running(self):
        return self._running
