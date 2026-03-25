"""Linux platform support: Wayland overlay is naturally excluded from screen sharing."""

import subprocess
import logging

logger = logging.getLogger(__name__)


def hide_from_capture(window):
    """On Wayland/KDE, the overlay is naturally excluded from the screen share window picker.
    No API call needed — the user simply doesn't select the overlay window."""
    logger.info("Linux/Wayland: overlay is naturally excluded from screen sharing window picker")


def list_audio_sources():
    """List available PipeWire/PulseAudio audio sources."""
    sources = []
    try:
        result = subprocess.run(
            ["pactl", "list", "short", "sources"],
            capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                sources.append({"id": parts[0], "name": parts[1], "type": "monitor" if ".monitor" in parts[1] else "input"})
    except Exception as e:
        logger.error(f"Failed to list audio sources: {e}")
    return sources


def get_monitor_source():
    """Get the default monitor source for capturing system audio output."""
    try:
        # Get the default sink name
        result = subprocess.run(
            ["pactl", "get-default-sink"],
            capture_output=True, text=True, timeout=5,
        )
        default_sink = result.stdout.strip()
        if default_sink:
            return f"{default_sink}.monitor"

        # Fallback: find any monitor source
        sources = list_audio_sources()
        for s in sources:
            if s["type"] == "monitor":
                return s["name"]
    except Exception as e:
        logger.error(f"Failed to get monitor source: {e}")
    return None
