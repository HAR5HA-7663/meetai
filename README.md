# MeetAI

Cross-platform AI meeting assistant with an invisible overlay. Like Cluely/Parakeet AI, but open-source and built for privacy.

## Features

- **Invisible overlay** — frameless, transparent, always-on-top window hidden from screen capture
  - Windows: `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)`
  - macOS: `NSWindow.setSharingType(NSWindowSharingNone)`
  - Linux/Wayland: naturally excluded from screen share window picker
- **Screenshot analysis** — capture monitor on hotkey, AI analyzes content
- **Live transcription** — real-time speech-to-text via faster-whisper (GPU accelerated)
- **AI suggestions** — auto-detects questions, suggests personalized responses
- **Personal context** — loads your resume/background for tailored answers
- **Multi-provider** — uses your existing CLI tools (claude, codex, gemini)

## Quick Start

```bash
# Clone
git clone https://github.com/HAR5HA-7663/meetai.git
cd meetai

# Setup (requires uv)
uv venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
uv pip install -r requirements.txt

# For GPU transcription (NVIDIA)
uv pip install torch faster-whisper

# Run
python main.py
```

## Hotkeys

| Hotkey | Action |
|--------|--------|
| `Alt+/` | Screenshot + AI analysis |
| `Alt+R` | Toggle recording + transcription |
| `Alt+A` | Ask AI about current transcript |
| `Alt+H` | Toggle overlay visibility |

## Configuration

Edit `config.toml`:

```toml
[screenshot]
capture_monitor = 2        # Which monitor to capture

[ai]
default_provider = "claude" # claude, codex, or gemini
resume_profile = "sde"      # sde, ml, devops, ai_automation, java_fullstack

[hotkeys]
screenshot_analyze = "<alt>+/"
toggle_recording = "<alt>+r"
```

## Requirements

- Python 3.12+
- PyQt6
- CLI tools: `claude`, `codex`, or `gemini` (at least one)
- For transcription: NVIDIA GPU recommended (RTX 3060+ for large-v3 model)
