"""macOS platform support: hide overlay from screen capture via NSWindow sharing type."""

import logging

logger = logging.getLogger(__name__)


def hide_from_capture(window):
    """Hide a PyQt6 QWidget from screen capture on macOS using NSWindowSharingNone."""
    try:
        from AppKit import NSApplication, NSWindowSharingNone
        nswindow = None
        # Get the native NSWindow from the PyQt6 window
        wid = int(window.winId())
        for w in NSApplication.sharedApplication().windows():
            if w.windowNumber() == wid:
                nswindow = w
                break
        if nswindow:
            nswindow.setSharingType_(NSWindowSharingNone)
            logger.info("Window hidden from screen capture (NSWindowSharingNone)")
        else:
            logger.warning("Could not find NSWindow for the given QWidget")
    except ImportError:
        logger.warning("pyobjc not installed — cannot hide window from capture on macOS. "
                       "Install with: pip install pyobjc-framework-Cocoa")
    except Exception as e:
        logger.error(f"Failed to hide window from capture: {e}")


def list_audio_sources():
    """List available audio sources on macOS."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        sources = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                sources.append({"id": i, "name": dev["name"], "channels": dev["max_input_channels"]})
        return sources
    except Exception as e:
        logger.error(f"Failed to list audio sources: {e}")
        return []
