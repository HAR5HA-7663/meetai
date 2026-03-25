"""Cross-platform screenshot capture using mss."""

import logging
import tempfile
import os
import mss
import mss.tools

logger = logging.getLogger(__name__)


def list_monitors() -> list[dict]:
    """List available monitors with their geometry."""
    with mss.mss() as sct:
        monitors = []
        for i, mon in enumerate(sct.monitors):
            monitors.append({
                "index": i,
                "left": mon["left"],
                "top": mon["top"],
                "width": mon["width"],
                "height": mon["height"],
                "label": "All monitors" if i == 0 else f"Monitor {i}",
            })
        return monitors


def capture_monitor(monitor_index: int = 2, save_path: str | None = None) -> str:
    """Capture a specific monitor and save as PNG.

    Args:
        monitor_index: Which monitor to capture (0=all, 1=first, 2=second, etc.)
        save_path: Where to save the PNG. If None, uses a temp file.

    Returns:
        Path to the saved PNG file.
    """
    if save_path is None:
        save_path = os.path.join(tempfile.gettempdir(), "meetai_screenshot.png")

    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            if monitor_index >= len(monitors):
                logger.warning(f"Monitor {monitor_index} not found, using monitor 1")
                monitor_index = 1

            monitor = monitors[monitor_index]
            logger.info(f"Capturing monitor {monitor_index}: {monitor['width']}x{monitor['height']} at ({monitor['left']},{monitor['top']})")

            screenshot = sct.grab(monitor)
            mss.tools.to_png(screenshot.rgb, screenshot.size, output=save_path)

            logger.info(f"Screenshot saved to {save_path}")
            return save_path

    except Exception as e:
        logger.error(f"Screenshot capture failed: {e}")
        raise
