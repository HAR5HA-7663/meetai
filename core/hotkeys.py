"""Cross-platform global hotkey listener using pynput."""

import logging
import threading
from pynput import keyboard

logger = logging.getLogger(__name__)


class HotkeyManager:
    """Manages global hotkeys across platforms."""

    def __init__(self):
        self._callbacks = {}
        self._listener = None
        self._current_keys = set()

    def register(self, hotkey_str: str, callback):
        """Register a callback for a hotkey combination.

        Format: '<alt>+/', '<alt>+r', '<ctrl>+<shift>+s', etc.
        """
        keys = self._parse_hotkey(hotkey_str)
        self._callbacks[keys] = callback
        logger.info(f"Registered hotkey: {hotkey_str}")

    def _parse_hotkey(self, hotkey_str: str) -> frozenset:
        """Parse hotkey string into a frozenset of key identifiers."""
        parts = hotkey_str.lower().split("+")
        keys = set()
        for part in parts:
            part = part.strip()
            if part == "<alt>":
                keys.add("alt")
            elif part == "<ctrl>":
                keys.add("ctrl")
            elif part == "<shift>":
                keys.add("shift")
            elif part == "<cmd>" or part == "<super>":
                keys.add("cmd")
            elif part == "/":
                keys.add("/")
            elif len(part) == 1:
                keys.add(part)
            else:
                keys.add(part)
        return frozenset(keys)

    def _key_to_str(self, key) -> str | None:
        """Convert a pynput key to a string identifier."""
        try:
            if hasattr(key, 'char') and key.char is not None:
                return key.char.lower()
            elif key == keyboard.Key.alt or key == keyboard.Key.alt_l or key == keyboard.Key.alt_r:
                return "alt"
            elif key == keyboard.Key.ctrl or key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                return "ctrl"
            elif key == keyboard.Key.shift or key == keyboard.Key.shift_l or key == keyboard.Key.shift_r:
                return "shift"
            elif key == keyboard.Key.cmd or key == keyboard.Key.cmd_l or key == keyboard.Key.cmd_r:
                return "cmd"
            elif key == keyboard.Key.esc:
                return "esc"
            else:
                return str(key).replace("Key.", "").lower()
        except Exception:
            return None

    def _on_press(self, key):
        key_str = self._key_to_str(key)
        if key_str:
            self._current_keys.add(key_str)
            frozen = frozenset(self._current_keys)
            for combo, callback in self._callbacks.items():
                if combo.issubset(frozen):
                    logger.debug(f"Hotkey triggered: {combo}")
                    # Run callback in a thread to avoid blocking the listener
                    threading.Thread(target=callback, daemon=True).start()

    def _on_release(self, key):
        key_str = self._key_to_str(key)
        if key_str:
            self._current_keys.discard(key_str)

    def start(self):
        """Start listening for global hotkeys."""
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._listener.daemon = True
        self._listener.start()
        logger.info("Global hotkey listener started")

    def stop(self):
        """Stop the hotkey listener."""
        if self._listener:
            self._listener.stop()
            logger.info("Global hotkey listener stopped")
