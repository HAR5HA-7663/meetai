"""Application state management."""

import time
import threading
import logging

logger = logging.getLogger(__name__)


class AppState:
    """Manages application state: transcript buffer, recording state, etc."""

    def __init__(self, context_window_minutes: int = 10):
        self._lock = threading.Lock()
        self._transcript_entries = []  # list of (timestamp, text)
        self._recording = False
        self._context_window = context_window_minutes * 60  # in seconds

    @property
    def is_recording(self) -> bool:
        return self._recording

    @is_recording.setter
    def is_recording(self, value: bool):
        self._recording = value

    def add_transcript(self, text: str):
        """Add a transcript entry with current timestamp."""
        with self._lock:
            self._transcript_entries.append((time.time(), text))
            self._prune()

    def get_recent_transcript(self, minutes: int | None = None) -> str:
        """Get transcript from the last N minutes (or context window)."""
        window = (minutes * 60) if minutes else self._context_window
        cutoff = time.time() - window
        with self._lock:
            entries = [text for ts, text in self._transcript_entries if ts >= cutoff]
        return "\n".join(entries)

    def clear_transcript(self):
        with self._lock:
            self._transcript_entries.clear()

    def _prune(self):
        """Remove entries older than the context window."""
        cutoff = time.time() - self._context_window
        self._transcript_entries = [
            (ts, text) for ts, text in self._transcript_entries if ts >= cutoff
        ]
