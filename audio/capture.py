"""Cross-platform audio capture using sounddevice."""

import logging
import threading
import queue
import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)


def list_audio_devices():
    """List all available audio input devices."""
    devices = sd.query_devices()
    inputs = []
    for i, dev in enumerate(devices):
        if dev["max_input_channels"] > 0:
            inputs.append({"id": i, "name": dev["name"], "channels": dev["max_input_channels"],
                           "sample_rate": dev["default_samplerate"]})
    return inputs


def find_monitor_source():
    """Find the system audio monitor source (for capturing what others say in meetings).

    On Linux/PipeWire: looks for a .monitor source.
    On Windows: looks for a loopback device.
    On macOS: returns default input (user needs BlackHole or similar).
    """
    import sys
    devices = sd.query_devices()

    if sys.platform.startswith("linux"):
        # PipeWire/PulseAudio: monitor sources capture system output
        for i, dev in enumerate(devices):
            name = dev["name"].lower()
            if "monitor" in name and dev["max_input_channels"] > 0:
                logger.info(f"Found monitor source: [{i}] {dev['name']}")
                return i

    elif sys.platform == "win32":
        # Windows: look for WASAPI loopback
        for i, dev in enumerate(devices):
            name = dev["name"].lower()
            if "loopback" in name and dev["max_input_channels"] > 0:
                logger.info(f"Found loopback device: [{i}] {dev['name']}")
                return i

    # Fallback: default input device
    default = sd.default.device[0]
    if default is not None:
        logger.info(f"Using default input device: [{default}] {devices[default]['name']}")
        return default

    logger.warning("No suitable audio input device found")
    return None


class AudioCapture:
    """Captures audio from a specified device and pushes chunks to a queue."""

    def __init__(self, device_id=None, sample_rate=16000, chunk_duration_ms=30):
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration_ms / 1000)
        self.device_id = device_id
        self.audio_queue = queue.Queue(maxsize=500)
        self._stream = None
        self._running = False

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio status: {status}")
        if self._running:
            # Convert to mono float32 if needed
            audio = indata[:, 0].copy() if indata.ndim > 1 else indata.copy()
            try:
                self.audio_queue.put_nowait(audio.flatten())
            except queue.Full:
                pass  # Drop oldest if queue full

    def start(self):
        """Start capturing audio."""
        if self.device_id is None:
            self.device_id = find_monitor_source()
            if self.device_id is None:
                logger.error("No audio device available")
                return False

        try:
            self._running = True
            self._stream = sd.InputStream(
                device=self.device_id,
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=self.chunk_size,
                callback=self._audio_callback,
            )
            self._stream.start()
            logger.info(f"Audio capture started (device={self.device_id}, rate={self.sample_rate})")
            return True
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            self._running = False
            return False

    def stop(self):
        """Stop capturing audio."""
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Audio capture stopped")

    def get_chunk(self, timeout=0.1):
        """Get the next audio chunk from the queue."""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    @property
    def is_running(self):
        return self._running
