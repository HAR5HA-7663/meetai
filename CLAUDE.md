# CLAUDE.md — MeetAI Recursive Learning & Session Tracker

This file serves as a persistent learning document for Claude Code when working on MeetAI. It tracks decisions, mistakes, corrections, and patterns to ensure continuous improvement across sessions.

---

## Project Overview

**MeetAI** is a cross-platform (Windows/Linux/macOS) AI-powered meeting assistant with an invisible overlay. It captures meeting audio, transcribes it in real-time, takes screenshots on hotkey, and uses AI to generate personalized answers.

**Tech Stack:** Python + PyQt6, sounddevice, faster-whisper, mss, pynput, CLI LLM tools (claude/codex/gemini)

**User:** Harsha Vardhan Yellela
**Primary Systems:** Arch Linux (KDE Plasma, Wayland, 2x RTX 3090), Windows
**Personal Context Source:** `~/Desktop/resume/` repo (HTML resumes with skills, experience, projects)

---

## Key Architecture Decisions

1. **Python + PyQt6** over Electron/Tauri — native to KDE/Qt6 stack, lighter, cross-platform
2. **CLI LLM tools** (claude -p, codex exec, gemini -p) instead of Python SDKs — no API key management, uses user's existing auth
3. **mss** for screenshots — cross-platform, captures specific monitors, no external tools
4. **pynput** for hotkeys — cross-platform global hotkey listener
5. **faster-whisper** for STT — local, private, GPU-accelerated on RTX 3090
6. **Platform-specific overlay hiding:**
   - Windows: `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)` via ctypes
   - macOS: `NSWindow.setSharingType_(NSWindowSharingNone)` via pyobjc
   - Linux/Wayland: naturally excluded from screen share window picker

---

## User Preferences & Work Style

- Types quickly with typos — understand intent without asking for clarification
- Prefers **autonomous action** — don't ask unnecessary questions, just do it
- Wants concise responses, not verbose explanations
- Uses tables and structured summaries
- Email: harsha.yellela@gmail.com
- GitHub: HAR5HA-7663

---

## Mistakes & Corrections Log

> This section tracks mistakes Claude made and corrections from the user.
> Each entry helps prevent repeating the same mistake.

### Session 1 (2026-03-25)

| # | Mistake | Correction | Rule |
|---|---------|-----------|------|
| 1 | Tried to use `pip` / `pip3` to install packages | Arch Linux uses `pacman` for system packages or `uv` for venv management. User has `uv` installed. | **Always check for `uv` first on this system.** Use `uv venv` + `uv pip install` for Python deps. Never use bare `pip`. |
| 2 | Used `grim`/`slurp` for screenshots (Linux-only) | User wants cross-platform support (Windows + Linux + macOS). Use `mss` library instead. | **Always think cross-platform.** User uses both Windows and Linux. |
| 3 | Used KDE D-Bus for hotkeys (Linux-only) | Use `pynput` for cross-platform global hotkeys. | **Same as above — cross-platform first.** |
| 4 | Proposed region selection with slurp | User wants instant full-monitor capture on hotkey (Alt+/), no selection UI. Capture the MSI monitor (monitor 2). | **Screenshot = instant capture of configured monitor. No user interaction.** |
| 5 | Proposed Anthropic/OpenAI Python SDKs for AI | User wants to use existing CLI tools: `claude -p`, `codex exec`, `gemini -p`. No SDK needed. | **Use CLI tools for AI, not Python SDKs. The CLI tools handle auth.** |
| 6 | Named package directory `platform/` | Shadows Python stdlib `platform` module, breaks pynput. Renamed to `meetai_platform/`. | **Never name packages after stdlib modules (platform, os, sys, etc.)** |
| 7 | Overlay was not draggable on Wayland | Regular Qt `move()` is blocked by Wayland. Need `BypassWindowManagerHint` flag to allow free positioning. | **On Wayland: always use BypassWindowManagerHint for draggable overlay windows.** |
| 8 | Overlay was too big, blocked the screen | Made it a big 420x600 panel. Cluely is a TINY bar that expands only when needed. | **Start collapsed (thin bar), auto-expand only on speech/AI events. Don't block the user's view.** |
| 9 | Didn't install torchaudio | Silero VAD depends on torchaudio. | **Always install torchaudio alongside torch for audio ML tasks.** |

---

## Session Progress Tracker

### Session 1 (2026-03-25) — Initial Build

**Status:** All 5 phases complete. App is functional.

- [x] Research Parakeet AI, Cluely AI, open-source clones
- [x] Evaluate Pluely, Natively, OpenCluely as base references
- [x] Design architecture and write implementation plan
- [x] Phase 1: Project structure, config, platform modules, overlay window, theme, tray
- [x] Phase 2: Screenshot (mss), hotkeys (pynput), CLI AI provider, personal context loader
- [x] Phase 3: Audio capture (sounddevice), Silero VAD, faster-whisper transcription (CUDA)
- [x] Phase 4: MeetingAssistant with auto-suggest, question detection, context-aware responses
- [x] Phase 5: Copy to clipboard, transcript export, profile selector, auto-suggest toggle, README

---

## File Reference

| File | Purpose |
|------|---------|
| `main.py` | Entry point, initializes app |
| `config.py` | TOML config loader with defaults |
| `config.toml` | User settings |
| `core/event_bus.py` | PyQt6 signal-based pub/sub |
| `core/hotkeys.py` | Global hotkeys via pynput |
| `core/state.py` | App state (transcript buffer, recording state) |
| `audio/capture.py` | Cross-platform audio capture |
| `audio/vad.py` | Silero VAD wrapper |
| `audio/transcriber.py` | faster-whisper STT |
| `vision/screenshot.py` | Monitor capture via mss |
| `vision/analyzer.py` | Send screenshot to AI |
| `ai/provider.py` | Abstract AI provider interface |
| `ai/cli_provider.py` | Runs claude/codex/gemini CLI tools |
| `ai/context.py` | Loads personal context from resume repo |
| `ai/prompts.py` | System prompts for meeting scenarios |
| `overlay/window.py` | Frameless transparent always-on-top window |
| `overlay/widgets.py` | Transcript + AI panels + controls |
| `overlay/theme.py` | Dark glass-morphism stylesheet |
| `overlay/tray.py` | System tray icon |
| `platform/windows.py` | SetWindowDisplayAffinity |
| `platform/macos.py` | NSWindowSharingNone |
| `platform/linux.py` | Wayland/PipeWire helpers |

---

## Rules for Claude

1. **Cross-platform first** — every feature must work on Windows, Linux, and macOS
2. **Use `uv`** for Python dependency management on this system, never bare `pip`
3. **CLI tools for AI** — `claude -p`, `codex exec`, `gemini -p` — no Python SDKs
4. **Instant screenshot** — capture configured monitor on hotkey, no region selection
5. **Personal context** — always load resume data and include in AI prompts
6. **Be autonomous** — don't ask unnecessary questions, just do the work
7. **Keep this file updated** — log mistakes, progress, and decisions after each session
