#!/usr/bin/env python3
"""MeetAI - Cross-platform AI Meeting Assistant with Invisible Overlay."""

import sys
import os
import signal

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from config import Config
from overlay.window import OverlayWindow
from overlay.tray import TrayIcon
from utils.logger import setup_logging
from core.event_bus import event_bus
from core.hotkeys import HotkeyManager
from core.state import AppState
from vision.analyzer import ScreenshotAnalyzer
from ai.cli_provider import CLIProvider
from ai.context import load_context
from ai import prompts

import logging
logger = logging.getLogger(__name__)


class MeetAI:
    """Main application controller."""

    def __init__(self):
        self.config = Config()
        self.state = AppState(
            context_window_minutes=self.config.get("ai", "context_window_minutes", 10)
        )
        self.screenshot_analyzer = ScreenshotAnalyzer(self.config)
        self.hotkeys = HotkeyManager()
        self._context = None

    def _load_context(self):
        if self._context is None:
            profile = self.config.get("ai", "resume_profile", "sde")
            self._context = load_context(profile)
        return self._context

    def _on_screenshot(self):
        """Hotkey: capture screenshot and analyze."""
        logger.info("Screenshot hotkey triggered")
        self.screenshot_analyzer.analyze(mode="meeting")

    def _on_toggle_recording(self):
        """Hotkey: toggle audio recording."""
        if self.state.is_recording:
            self.state.is_recording = False
            event_bus.recording_stopped.emit()
            event_bus.status_update.emit("Recording stopped")
            logger.info("Recording stopped")
        else:
            self.state.is_recording = True
            event_bus.recording_started.emit()
            event_bus.status_update.emit("Recording started")
            logger.info("Recording started")
            # Audio capture will be started in Phase 3

    def _on_ask_ai(self):
        """Hotkey: ask AI about current transcript."""
        logger.info("Ask AI hotkey triggered")
        import threading
        threading.Thread(target=self._ask_ai_async, daemon=True).start()

    def _ask_ai_async(self):
        transcript = self.state.get_recent_transcript()
        if not transcript:
            event_bus.ai_error.emit("No transcript available. Start recording first.")
            return

        context = self._load_context()
        prompt = prompts.ASK_AI.format(
            name="Harsha",
            context=context,
            transcript=transcript,
        )

        tool = self.config.get("ai", "default_provider", "claude")
        provider = CLIProvider(tool=tool)

        event_bus.ai_response_started.emit()

        def on_chunk(chunk):
            event_bus.ai_response_chunk.emit(chunk)

        result = provider.stream_response(prompt, callback=on_chunk)
        if not result or result.startswith("Error:"):
            result = provider.get_response(prompt)
        event_bus.ai_response_complete.emit(result)

    def _on_toggle_overlay(self):
        """Hotkey: toggle overlay visibility."""
        event_bus.overlay_toggle.emit()

    def setup_hotkeys(self):
        hotkey_config = self.config.section("hotkeys")
        self.hotkeys.register(hotkey_config.get("screenshot_analyze", "<alt>+/"), self._on_screenshot)
        self.hotkeys.register(hotkey_config.get("toggle_recording", "<alt>+r"), self._on_toggle_recording)
        self.hotkeys.register(hotkey_config.get("ask_ai", "<alt>+a"), self._on_ask_ai)
        self.hotkeys.register(hotkey_config.get("toggle_overlay", "<alt>+h"), self._on_toggle_overlay)
        self.hotkeys.start()

    def connect_ui(self, overlay):
        """Connect overlay UI buttons to actions."""
        overlay.control_bar.screenshot_btn.clicked.connect(self._on_screenshot)
        overlay.control_bar.record_btn.clicked.connect(self._on_toggle_recording)
        overlay.control_bar.ask_btn.clicked.connect(self._on_ask_ai)


def main():
    setup_logging()
    logger.info("Starting MeetAI...")

    app = QApplication(sys.argv)
    app.setApplicationName("MeetAI")
    app.setQuitOnLastWindowClosed(False)

    # Allow Ctrl+C to quit
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    # Initialize app controller
    meetai = MeetAI()

    # Create overlay
    overlay = OverlayWindow(meetai.config)
    overlay.show()

    # Connect UI buttons
    meetai.connect_ui(overlay)

    # Setup global hotkeys
    meetai.setup_hotkeys()

    # Create tray icon
    tray = TrayIcon(app, overlay)
    tray.show()

    logger.info("MeetAI is running!")
    logger.info("  Alt+/  Screenshot + AI analysis")
    logger.info("  Alt+R  Toggle recording")
    logger.info("  Alt+A  Ask AI about transcript")
    logger.info("  Alt+H  Toggle overlay visibility")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
