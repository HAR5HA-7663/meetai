"""Screenshot analyzer: captures screen and sends to AI for analysis."""

import logging
import threading
from vision.screenshot import capture_monitor
from ai.cli_provider import get_provider
from ai import prompts
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
            self._provider = get_provider(tool=tool)

    def analyze(self, mode: str = "meeting"):
        """Capture screenshot and analyze in a background thread."""
        threading.Thread(target=self._analyze_async, args=(mode,), daemon=True).start()

    def _analyze_async(self, mode: str):
        self._ensure_loaded()

        try:
            event_bus.screenshot_analyzing.emit()
            event_bus.status_update.emit("Capturing screenshot...")

            path = capture_monitor(
                monitor_index=self.monitor_index,
                save_path=self.save_path,
            )
            event_bus.screenshot_taken.emit(path)

            # Build the proper system-aware prompt
            if mode == "coding":
                prompt = prompts.build_coding(name="Harsha", context=self._context)
            else:
                prompt = prompts.build_screenshot(name="Harsha", context=self._context)

            event_bus.status_update.emit("Analyzing screenshot with AI...")
            event_bus.ai_response_started.emit()

            # Use image analysis (Claude can see the screenshot)
            full_response = self._provider.analyze_image(path, prompt)
            event_bus.ai_response_complete.emit(full_response)

        except Exception as e:
            logger.error(f"Screenshot analysis failed: {e}")
            event_bus.ai_error.emit(str(e))
