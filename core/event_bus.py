"""Central event bus using PyQt6 signals for decoupled module communication."""

from PyQt6.QtCore import QObject, pyqtSignal


class EventBus(QObject):
    # Transcript events
    transcript_interim = pyqtSignal(str)           # live partial text (updates in-place)
    transcript_final = pyqtSignal(str)             # finalized segment (appended)
    transcript_updated = pyqtSignal(str)           # alias for final (backward compat)
    transcript_cleared = pyqtSignal()

    # Speech turn events
    speech_turn_ended = pyqtSignal(str)            # full text from one speaker turn → triggers AI

    # AI response events
    ai_response_started = pyqtSignal()
    ai_response_chunk = pyqtSignal(str)            # streaming token/line
    ai_response_complete = pyqtSignal(str)         # full response
    ai_error = pyqtSignal(str)                     # error message

    # Screenshot events
    screenshot_taken = pyqtSignal(str)             # path to screenshot file
    screenshot_analyzing = pyqtSignal()
    screenshot_error = pyqtSignal(str)

    # Recording events
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    # Overlay events
    overlay_toggle = pyqtSignal()
    overlay_minimize = pyqtSignal()

    # Status events
    status_update = pyqtSignal(str)                # status message for UI
    error_occurred = pyqtSignal(str, str)          # component, message


# Global singleton
event_bus = EventBus()
