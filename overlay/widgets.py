"""Overlay UI widgets: transcript panel, AI response panel, controls."""

import os
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QComboBox, QApplication,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QTextCursor

from core.event_bus import event_bus


class TranscriptPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QHBoxLayout()
        label = QLabel("LIVE TRANSCRIPT")
        label.setObjectName("section_label")
        header.addWidget(label)
        header.addStretch()

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setObjectName("control_btn")
        self.clear_btn.setFixedWidth(50)
        self.clear_btn.clicked.connect(self.clear)
        header.addWidget(self.clear_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.setObjectName("control_btn")
        self.export_btn.setFixedWidth(55)
        self.export_btn.clicked.connect(self._export)
        header.addWidget(self.export_btn)

        layout.addLayout(header)

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("transcript_panel")
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("Press Alt+R to start recording...")
        layout.addWidget(self.text_edit)

        event_bus.transcript_updated.connect(self.append_text)
        event_bus.transcript_cleared.connect(self.clear)

    def append_text(self, text: str):
        self.text_edit.append(text)
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def clear(self):
        self.text_edit.clear()

    def get_text(self) -> str:
        return self.text_edit.toPlainText()

    def _export(self):
        """Export transcript to markdown file."""
        text = self.get_text()
        if not text:
            event_bus.status_update.emit("No transcript to export")
            return
        ts = time.strftime("%Y%m%d_%H%M%S")
        path = os.path.expanduser(f"~/Desktop/meetai_transcript_{ts}.md")
        with open(path, "w") as f:
            f.write(f"# Meeting Transcript - {time.strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(text)
        event_bus.status_update.emit(f"Transcript exported to {path}")


class AIResponsePanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        header = QHBoxLayout()
        label = QLabel("AI SUGGESTION")
        label.setObjectName("section_label")
        header.addWidget(label)

        self.status_label = QLabel("")
        self.status_label.setObjectName("status_label")
        header.addStretch()
        header.addWidget(self.status_label)

        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("control_btn")
        self.copy_btn.setFixedWidth(48)
        self.copy_btn.clicked.connect(self._copy_response)
        header.addWidget(self.copy_btn)

        layout.addLayout(header)

        self.text_edit = QTextEdit()
        self.text_edit.setObjectName("ai_panel")
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlaceholderText("AI suggestions will appear here...")
        layout.addWidget(self.text_edit)

        self._response_text = ""

        event_bus.ai_response_started.connect(self._on_started)
        event_bus.ai_response_chunk.connect(self._on_chunk)
        event_bus.ai_response_complete.connect(self._on_complete)
        event_bus.ai_error.connect(self._on_error)
        event_bus.screenshot_analyzing.connect(self._on_analyzing)

    def _on_started(self):
        self._response_text = ""
        self.text_edit.clear()
        self.status_label.setText("thinking...")
        self.status_label.setStyleSheet("color: rgba(255, 200, 50, 0.9);")

    def _on_analyzing(self):
        self._response_text = ""
        self.text_edit.clear()
        self.status_label.setText("analyzing screenshot...")
        self.status_label.setStyleSheet("color: rgba(100, 180, 255, 0.9);")

    def _on_chunk(self, chunk: str):
        self._response_text += chunk
        self.text_edit.setPlainText(self._response_text)
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)

    def _on_complete(self, full_response: str):
        self._response_text = full_response
        self.text_edit.setPlainText(full_response)
        self.text_edit.moveCursor(QTextCursor.MoveOperation.End)
        self.status_label.setText("done")
        self.status_label.setStyleSheet("color: rgba(120, 200, 120, 0.9);")

    def _on_error(self, error: str):
        self.status_label.setText("error")
        self.status_label.setStyleSheet("color: rgba(255, 100, 100, 0.9);")
        self.text_edit.setPlainText(f"Error: {error}")

    def _copy_response(self):
        """Copy AI response to clipboard."""
        if self._response_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(self._response_text)
            self.status_label.setText("copied!")
            self.status_label.setStyleSheet("color: rgba(120, 200, 120, 0.9);")


class ControlBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Row 1: main controls
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        self.screenshot_btn = QPushButton("Screenshot (Alt+/)")
        self.screenshot_btn.setObjectName("control_btn")

        self.record_btn = QPushButton("Record (Alt+R)")
        self.record_btn.setObjectName("control_btn")
        self._recording = False

        self.ask_btn = QPushButton("Ask AI (Alt+A)")
        self.ask_btn.setObjectName("control_btn")

        row1.addWidget(self.screenshot_btn)
        row1.addWidget(self.record_btn)
        row1.addWidget(self.ask_btn)
        layout.addLayout(row1)

        # Row 2: provider, profile, auto-suggest
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        provider_label = QLabel("AI:")
        provider_label.setObjectName("section_label")
        provider_label.setFixedWidth(18)
        row2.addWidget(provider_label)

        self.provider_select = QComboBox()
        self.provider_select.setObjectName("provider_select")
        self.provider_select.addItems(["claude", "codex", "gemini"])
        self.provider_select.setFixedWidth(80)
        row2.addWidget(self.provider_select)

        profile_label = QLabel("Profile:")
        profile_label.setObjectName("section_label")
        profile_label.setFixedWidth(40)
        row2.addWidget(profile_label)

        self.profile_select = QComboBox()
        self.profile_select.setObjectName("provider_select")
        self.profile_select.addItems(["sde", "ml", "devops", "ai_automation", "java_fullstack", "general"])
        self.profile_select.setFixedWidth(100)
        row2.addWidget(self.profile_select)

        row2.addStretch()

        self.auto_suggest_btn = QPushButton("Auto: ON")
        self.auto_suggest_btn.setObjectName("control_btn")
        self.auto_suggest_btn.setFixedWidth(70)
        row2.addWidget(self.auto_suggest_btn)

        layout.addLayout(row2)

        event_bus.recording_started.connect(self._on_recording_started)
        event_bus.recording_stopped.connect(self._on_recording_stopped)

    def _on_recording_started(self):
        self._recording = True
        self.record_btn.setText("Stop (Alt+R)")
        self.record_btn.setObjectName("control_btn_active")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)

    def _on_recording_stopped(self):
        self._recording = False
        self.record_btn.setText("Record (Alt+R)")
        self.record_btn.setObjectName("control_btn")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)

    @property
    def is_recording(self):
        return self._recording

    @property
    def selected_provider(self):
        return self.provider_select.currentText()

    @property
    def selected_profile(self):
        return self.profile_select.currentText()
