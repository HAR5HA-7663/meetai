"""Linux platform support: Wayland overlay is naturally excluded from screen sharing."""

import subprocess
import logging

logger = logging.getLogger(__name__)


def hide_from_capture(window):
    """On Wayland/KDE, the overlay is naturally excluded from the screen share window picker.
    No API call needed — the user simply doesn't select the overlay window."""
    logger.info("Linux/Wayland: overlay is naturally excluded from screen sharing window picker")
    _set_kwin_keep_above()


def _set_kwin_keep_above():
    """Load a KWin script that forces MeetAI to stay above all windows."""
    import os
    script_path = os.path.join(os.path.dirname(__file__), "kwin_above.js")
    if not os.path.exists(script_path):
        logger.warning(f"KWin script not found: {script_path}")
        return
    try:
        # Unload previous instance if any
        subprocess.run(
            ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.unloadScript", "meetai_above"],
            capture_output=True, timeout=3,
        )
        # Load and start the script
        result = subprocess.run(
            ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.loadScript", script_path, "meetai_above"],
            capture_output=True, text=True, timeout=3,
        )
        subprocess.run(
            ["qdbus6", "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting.start"],
            capture_output=True, timeout=3,
        )
        logger.info(f"KWin keep-above script loaded: {result.stdout.strip()}")
    except Exception as e:
        logger.warning(f"Could not load KWin script: {e}")


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
