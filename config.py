import tomllib
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "general": {
        "theme": "dark",
        "overlay_opacity": 0.92,
        "overlay_position": "top-right",
        "overlay_width": 420,
        "overlay_height": 600,
    },
    "audio": {
        "source": "auto",
        "sample_rate": 16000,
        "vad_threshold": 0.5,
        "silence_duration_ms": 1500,
    },
    "transcription": {
        "engine": "faster-whisper",
        "model": "large-v3",
        "language": "en",
        "device": "cuda",
        "compute_type": "float16",
        "gpu_device_index": 0,
    },
    "ai": {
        "default_provider": "claude",
        "vision_provider": "claude",
        "code_provider": "codex",
        "general_provider": "gemini",
        "context_window_minutes": 10,
        "resume_profile": "sde",
    },
    "screenshot": {
        "capture_monitor": 2,
        "save_path": "/tmp/meetai_screenshot.png",
    },
    "hotkeys": {
        "screenshot_analyze": "<alt>+/",
        "toggle_recording": "<alt>+r",
        "ask_ai": "<alt>+a",
        "toggle_overlay": "<alt>+h",
        "quit": "<alt>+q",
    },
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "config.toml")
        self._path = Path(config_path)
        self._data = DEFAULT_CONFIG.copy()
        self._load()

    def _load(self):
        if self._path.exists():
            with open(self._path, "rb") as f:
                user_config = tomllib.load(f)
            self._data = _deep_merge(self._data, user_config)

    def get(self, section: str, key: str, default=None):
        return self._data.get(section, {}).get(key, default)

    def section(self, name: str) -> dict:
        return self._data.get(name, {})

    @property
    def data(self) -> dict:
        return self._data
