"""Screenshot capture — Wayland-compatible using spectacle (KDE) + Pillow crop."""

import logging
import subprocess
import tempfile
import os
import sys
from PIL import Image

logger = logging.getLogger(__name__)

# Monitor geometry from kscreen-doctor
# Updated at startup or hardcoded per system
MONITORS = None


def _detect_monitors():
    """Detect monitor layout from kscreen-doctor."""
    global MONITORS
    if MONITORS is not None:
        return MONITORS

    MONITORS = []
    try:
        result = subprocess.run(
            ["kscreen-doctor", "-o"],
            capture_output=True, text=True, timeout=5,
        )
        lines = result.stdout.split("\n")
        current = {}
        for line in lines:
            stripped = line.strip()
            # Remove ANSI codes
            import re
            clean = re.sub(r'\x1b\[[0-9;]*m', '', stripped)

            if clean.startswith("Output:"):
                if current:
                    MONITORS.append(current)
                parts = clean.split()
                current = {"index": int(parts[1]) if len(parts) > 1 else 0,
                           "name": parts[2] if len(parts) > 2 else "unknown"}
            elif "Geometry:" in clean:
                geo = clean.split("Geometry:")[1].strip()
                # Format: "x,y widthxheight"
                pos, size = geo.split()
                x, y = pos.split(",")
                w, h = size.split("x")
                current["x"] = int(x)
                current["y"] = int(y)
                current["width"] = int(w)
                current["height"] = int(h)

        if current:
            MONITORS.append(current)

        for m in MONITORS:
            logger.info(f"Monitor {m.get('index')}: {m.get('name')} "
                        f"{m.get('width')}x{m.get('height')} at ({m.get('x')},{m.get('y')})")
    except Exception as e:
        logger.error(f"Failed to detect monitors: {e}")
        # Fallback: single monitor
        MONITORS = [{"index": 1, "name": "default", "x": 0, "y": 0, "width": 1920, "height": 1080}]

    return MONITORS


def list_monitors():
    """List available monitors."""
    return _detect_monitors()


def capture_monitor(monitor_index: int = 2, save_path: str | None = None) -> str:
    """Capture a specific monitor on Wayland using spectacle + crop.

    Args:
        monitor_index: Which monitor (1-based, matches kscreen-doctor output index)
        save_path: Where to save. If None, uses temp file.

    Returns:
        Path to the saved PNG.
    """
    if save_path is None:
        save_path = os.path.join(tempfile.gettempdir(), "meetai_screenshot.png")

    monitors = _detect_monitors()

    # Find the target monitor
    target = None
    for m in monitors:
        if m.get("index") == monitor_index:
            target = m
            break

    if target is None:
        # Fallback: use the landscape monitor (widest one)
        target = max(monitors, key=lambda m: m.get("width", 0)) if monitors else None

    if target is None:
        raise RuntimeError("No monitors detected")

    try:
        # Step 1: Capture full desktop with spectacle
        full_path = os.path.join(tempfile.gettempdir(), "meetai_full.png")

        # Remove old file so we can detect when new one is written
        if os.path.exists(full_path):
            os.remove(full_path)

        result = subprocess.run(
            ["spectacle", "-f", "-b", "-n", "-o", full_path],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            raise RuntimeError(f"spectacle failed: {result.stderr}")

        # Wait for file to appear (spectacle is async)
        import time
        for _ in range(20):
            if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                break
            time.sleep(0.1)
        else:
            raise RuntimeError("spectacle did not produce output file")

        # Step 2: Crop to target monitor region
        img = Image.open(full_path)
        x, y = target["x"], target["y"]
        w, h = target["width"], target["height"]

        cropped = img.crop((x, y, x + w, y + h))
        cropped.save(save_path, "PNG")

        logger.info(f"Screenshot: {target['name']} ({w}x{h}) saved to {save_path}")
        return save_path

    except Exception as e:
        logger.error(f"Screenshot failed: {e}")
        raise
