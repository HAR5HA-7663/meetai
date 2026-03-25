"""Windows platform support: hide overlay from screen capture via SetWindowDisplayAffinity."""

import ctypes
import ctypes.wintypes
import logging

logger = logging.getLogger(__name__)

WDA_EXCLUDEFROMCAPTURE = 0x00000011


def hide_from_capture(window):
    """Hide a PyQt6 QWidget from screen capture on Windows."""
    try:
        hwnd = int(window.winId())
        user32 = ctypes.windll.user32
        result = user32.SetWindowDisplayAffinity(
            ctypes.wintypes.HWND(hwnd), ctypes.wintypes.DWORD(WDA_EXCLUDEFROMCAPTURE)
        )
        if result:
            logger.info("Window hidden from screen capture (SetWindowDisplayAffinity)")
        else:
            error = ctypes.get_last_error()
            logger.warning(f"SetWindowDisplayAffinity failed, error code: {error}")
    except Exception as e:
        logger.error(f"Failed to hide window from capture: {e}")


def list_audio_sources():
    """List available audio sources on Windows."""
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


def get_loopback_device():
    """Get the WASAPI loopback device for system audio capture."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0 and "loopback" in dev["name"].lower():
                return i
        # Fallback: try to find any WASAPI output device we can use
        for i, dev in enumerate(devices):
            if "wasapi" in str(dev.get("hostapi", "")).lower() and dev["max_output_channels"] > 0:
                return i
    except Exception:
        pass
    return None
