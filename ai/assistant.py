"""AI meeting assistant: auto-sends transcript to Claude when the other person stops speaking."""

import logging
import threading
import time

from ai.cli_provider import CLIProvider
from ai.context import load_context
from ai import prompts
from core.event_bus import event_bus
from core.state import AppState

logger = logging.getLogger(__name__)


class MeetingAssistant:
    """When the other person stops speaking, sends the transcript to Claude for an answer."""

    def __init__(self, config, state: AppState):
        self.config = config
        self.state = state
        self._context = None
        self._auto_suggest = True
        self._last_trigger_time = 0
        self._cooldown = 5  # min seconds between AI calls
        self._ai_busy = False

        # This is the key connection: when a speech turn ends → auto-respond
        event_bus.speech_turn_ended.connect(self._on_speech_turn_ended)

    def _ensure_context(self):
        if self._context is None:
            profile = self.config.get("ai", "resume_profile", "sde")
            self._context = load_context(profile)

    def _get_provider(self, task: str = "general") -> CLIProvider:
        if task == "vision":
            tool = self.config.get("ai", "vision_provider", "claude")
        elif task == "code":
            tool = self.config.get("ai", "code_provider", "codex")
        else:
            tool = self.config.get("ai", "default_provider", "claude")
        return CLIProvider(tool=tool)

    def _on_speech_turn_ended(self, last_utterance: str):
        """Called when the other person stops speaking. Auto-send to Claude."""
        if not self._auto_suggest:
            return
        if self._ai_busy:
            logger.debug("AI is busy, skipping auto-respond")
            return

        now = time.time()
        if now - self._last_trigger_time < self._cooldown:
            return

        self._last_trigger_time = now
        logger.info(f"Speech turn ended, triggering AI: \"{last_utterance[:80]}...\"")
        threading.Thread(target=self._auto_respond, args=(last_utterance,), daemon=True).start()

    def _auto_respond(self, last_utterance: str):
        """Send the last speech turn + recent transcript to Claude for an answer."""
        self._ai_busy = True
        try:
            self._ensure_context()
            transcript = self.state.get_recent_transcript(minutes=5)

            prompt = prompts.build_auto_respond(
                name="Harsha",
                context=self._context,
                last_utterance=last_utterance,
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
        except Exception as e:
            logger.error(f"Auto-respond failed: {e}")
            event_bus.ai_error.emit(str(e))
        finally:
            self._ai_busy = False

    def ask_about_transcript(self):
        """Manual: user presses Alt+A."""
        threading.Thread(target=self._manual_ask, daemon=True).start()

    def _manual_ask(self):
        self._ai_busy = True
        try:
            self._ensure_context()
            transcript = self.state.get_recent_transcript()
            if not transcript:
                event_bus.ai_error.emit("No transcript yet. Start recording first (Alt+R).")
                return

            prompt = prompts.build_ask_ai(
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
        except Exception as e:
            logger.error(f"Ask AI failed: {e}")
            event_bus.ai_error.emit(str(e))
        finally:
            self._ai_busy = False

    def toggle_auto_suggest(self):
        self._auto_suggest = not self._auto_suggest
        state = "enabled" if self._auto_suggest else "disabled"
        logger.info(f"Auto-respond {state}")
        event_bus.status_update.emit(f"Auto-respond {state}")

    @property
    def auto_suggest_enabled(self):
        return self._auto_suggest
