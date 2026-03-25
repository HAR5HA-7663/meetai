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

import logging
logger = logging.getLogger(__name__)


def main():
    setup_logging()
    logger.info("Starting MeetAI...")

    config = Config()

    app = QApplication(sys.argv)
    app.setApplicationName("MeetAI")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray

    # Allow Ctrl+C to quit
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    # Timer to process Python signals
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    # Create overlay
    overlay = OverlayWindow(config)
    overlay.show()

    # Create tray icon
    tray = TrayIcon(app, overlay)
    tray.show()

    logger.info("MeetAI overlay is running. Press Alt+H to toggle visibility.")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
