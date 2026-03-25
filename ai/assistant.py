"""AI meeting assistant: auto-detects questions and suggests responses."""

import re
import logging
import threading
import time

from ai.cli_provider import CLIProvider
from ai.context import load_context
from ai import prompts
from core.event_bus import event_bus
from core.state import AppState

logger = logging.getLogger(__name__)

# Patterns that indicate a question directed at the user
QUESTION_PATTERNS = [
    r'\?$',
    r'what do you think',
    r'can you (explain|tell|share|describe|walk)',
    r'how (would|did|do) you',
    r'tell (us|me) about',
    r'your (thoughts|opinion|experience|take)',
    r'have you (ever|worked|used|tried)',
    r'are you familiar',
    r'do you have (any|experience)',
    r'what\'?s your',
    r'could you',
    r'would you',
]

QUESTION_RE = re.compile('|'.join(QUESTION_PATTERNS), re.IGNORECASE)


def looks_like_question(text: str) -> bool:
    """Check if text appears to contain a question."""
    return bool(QUESTION_RE.search(text))


class MeetingAssistant:
    """Monitors transcript and auto-suggests responses when questions are detected."""

    def __init__(self, config, state: AppState):
        self.config = config
        self.state = state
        self._context = None
        self._last_suggestion_time = 0
        self._cooldown = 15  # seconds between auto-suggestions
        self._auto_suggest = True
        self._running = False

        # Connect to transcript updates
        event_bus.transcript_updated.connect(self._on_transcript)

    def _ensure_context(self):
        if self._context is None:
            profile = self.config.get("ai", "resume_profile", "sde")
            self._context = load_context(profile)

    def _get_provider(self, task: str = "general") -> CLIProvider:
        """Get the appropriate CLI provider for a task type."""
        if task == "vision":
            tool = self.config.get("ai", "vision_provider", "claude")
        elif task == "code":
            tool = self.config.get("ai", "code_provider", "codex")
        else:
            tool = self.config.get("ai", "default_provider", "claude")
        return CLIProvider(tool=tool)

    def _on_transcript(self, text: str):
        """Called when new transcript text arrives."""
        if not self._auto_suggest:
            return

        # Check cooldown
        now = time.time()
        if now - self._last_suggestion_time < self._cooldown:
            return

        # Check if the transcript contains a question
        if looks_like_question(text):
            self._last_suggestion_time = now
            logger.info(f"Question detected: {text[:80]}...")
            threading.Thread(target=self._auto_respond, daemon=True).start()

    def _auto_respond(self):
        """Generate an automatic response suggestion."""
        self._ensure_context()

        transcript = self.state.get_recent_transcript(minutes=5)
        if not transcript:
            return

        prompt = prompts.MEETING_ASSISTANT.format(
            name="Harsha",
            context=self._context,
            transcript=transcript,
        )

        provider = self._get_provider("general")
        event_bus.ai_response_started.emit()

        def on_chunk(chunk):
            event_bus.ai_response_chunk.emit(chunk)

        result = provider.stream_response(prompt, callback=on_chunk)
        if not result or result.startswith("Error:"):
            result = provider.get_response(prompt)
        event_bus.ai_response_complete.emit(result)

    def ask_about_transcript(self):
        """Manually ask AI about the current transcript."""
        threading.Thread(target=self._manual_ask, daemon=True).start()

    def _manual_ask(self):
        self._ensure_context()

        transcript = self.state.get_recent_transcript()
        if not transcript:
            event_bus.ai_error.emit("No transcript available. Start recording first (Alt+R).")
            return

        prompt = prompts.ASK_AI.format(
            name="Harsha",
            context=self._context,
            transcript=transcript,
        )

        provider = self._get_provider("general")
        event_bus.ai_response_started.emit()

        def on_chunk(chunk):
            event_bus.ai_response_chunk.emit(chunk)

        result = provider.stream_response(prompt, callback=on_chunk)
        if not result or result.startswith("Error:"):
            result = provider.get_response(prompt)
        event_bus.ai_response_complete.emit(result)

    def toggle_auto_suggest(self):
        self._auto_suggest = not self._auto_suggest
        state = "enabled" if self._auto_suggest else "disabled"
        logger.info(f"Auto-suggest {state}")
        event_bus.status_update.emit(f"Auto-suggest {state}")

    @property
    def auto_suggest_enabled(self):
        return self._auto_suggest
