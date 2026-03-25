"""Screenshot analyzer: captures screen and sends to AI for analysis."""

import logging
import threading
from vision.screenshot import capture_monitor
from ai.cli_provider import CLIProvider
from ai.prompts import SCREENSHOT_ANALYSIS, CODING_INTERVIEW
from ai.context import load_context
from core.event_bus import event_bus

logger = logging.getLogger(__name__)


class ScreenshotAnalyzer:
    """Captures a monitor screenshot and analyzes it with AI."""

    def __init__(self, config):
        self.config = config
        self.monitor_index = config.get("screenshot", "capture_monitor", 2)
        self.save_path = config.get("screenshot", "save_path", "/tmp/meetai_screenshot.png")
        self._context = None
        self._provider = None

    def _ensure_loaded(self):
        if self._context is None:
            profile = self.config.get("ai", "resume_profile", "sde")
            self._context = load_context(profile)
        if self._provider is None:
            tool = self.config.get("ai", "vision_provider", "claude")
            self._provider = CLIProvider(tool=tool)

    def analyze(self, mode: str = "meeting"):
        """Capture screenshot and analyze in a background thread."""
        threading.Thread(target=self._analyze_async, args=(mode,), daemon=True).start()

    def _analyze_async(self, mode: str):
        self._ensure_loaded()

        try:
            # Capture screenshot
            event_bus.screenshot_analyzing.emit()
            event_bus.status_update.emit("Capturing screenshot...")

            path = capture_monitor(
                monitor_index=self.monitor_index,
                save_path=self.save_path,
            )
            event_bus.screenshot_taken.emit(path)

            # Build prompt
            name = "Harsha"
            if mode == "coding":
                prompt = CODING_INTERVIEW.format(name=name, context=self._context)
            else:
                prompt = SCREENSHOT_ANALYSIS.format(name=name, context=self._context)

            event_bus.status_update.emit("Analyzing screenshot with AI...")
            event_bus.ai_response_started.emit()

            # Stream response
            def on_chunk(chunk):
                event_bus.ai_response_chunk.emit(chunk)

            full_response = self._provider.stream_response(
                prompt=f"Analyze this screenshot at: {path}",
                context=self._context + "\n\n" + prompt,
                callback=on_chunk,
            )

            # If streaming didn't produce output, try non-streaming
            if not full_response or full_response.startswith("Error:"):
                full_response = self._provider.analyze_image(path, prompt, self._context)
                event_bus.ai_response_complete.emit(full_response)
            else:
                event_bus.ai_response_complete.emit(full_response)

        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            event_bus.ai_error.emit(str(e))
