"""Overlay UI widgets: transcript panel, AI response panel, controls."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QPushButton, QComboBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QTextCursor

from core.event_bus import event_bus


class TranscriptPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        label = QLabel("LIVE TRANSCRIPT")
        label.setObjectName("section_label")
        layout.addWidget(label)

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


class ControlBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.screenshot_btn = QPushButton("Screenshot (Alt+/)")
        self.screenshot_btn.setObjectName("control_btn")

        self.record_btn = QPushButton("Record (Alt+R)")
        self.record_btn.setObjectName("control_btn")
        self._recording = False

        self.ask_btn = QPushButton("Ask AI (Alt+A)")
        self.ask_btn.setObjectName("control_btn")

        self.provider_select = QComboBox()
        self.provider_select.setObjectName("provider_select")
        self.provider_select.addItems(["claude", "codex", "gemini"])
        self.provider_select.setFixedWidth(80)

        layout.addWidget(self.screenshot_btn)
        layout.addWidget(self.record_btn)
        layout.addWidget(self.ask_btn)
        layout.addStretch()
        layout.addWidget(self.provider_select)

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
