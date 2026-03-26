"""Cluely-style floating overlay: minimal bar that expands to show transcript + AI."""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QApplication, QSizePolicy,
)
from PyQt6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QSize, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QTextCursor, QFont

from overlay.theme import DARK_THEME
from core.event_bus import event_bus

import logging
logger = logging.getLogger(__name__)


class OverlayWindow(QWidget):
    """Cluely-style floating overlay — compact bar that expands."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._expanded = True
        self._drag_pos = None

        self._setup_window()
        self._build_ui()
        self.setStyleSheet(DARK_THEME)
        self._hide_from_capture()
        self._position_window()

    # ── Window setup ──────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMinimumWidth(380)
        self.setMaximumWidth(460)

    def _hide_from_capture(self):
        try:
            if sys.platform == "win32":
                from meetai_platform.windows import hide_from_capture
            elif sys.platform == "darwin":
                from meetai_platform.macos import hide_from_capture
            else:
                from meetai_platform.linux import hide_from_capture
            hide_from_capture(self)
        except Exception as e:
            logger.warning(f"Could not hide from capture: {e}")

    def _position_window(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        geo = screen.availableGeometry()
        x = geo.right() - self.width() - 24
        y = geo.top() + 60
        self.move(x, y)

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Container for rounded background
        self.container = QWidget()
        self.container.setObjectName("overlay_main")
        self.c_layout = QVBoxLayout(self.container)
        self.c_layout.setContentsMargins(14, 10, 14, 10)
        self.c_layout.setSpacing(0)

        # ── Top bar (always visible) ──
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)

        # Status dot
        self.status_dot = QLabel("\u25cf")
        self.status_dot.setObjectName("status_dot")
        self.status_dot.setStyleSheet("color: rgba(80, 80, 80, 0.8);")
        self.status_dot.setFixedWidth(12)
        top_bar.addWidget(self.status_dot)

        # App title
        title = QLabel("MEETAI")
        title.setObjectName("app_title")
        top_bar.addWidget(title)

        # Status text
        self.status_text = QLabel("ready")
        self.status_text.setObjectName("status_text")
        top_bar.addWidget(self.status_text)

        top_bar.addStretch()

        # Hotkey hints
        hint = QLabel("Alt+/ \u00b7 Alt+R \u00b7 Alt+H")
        hint.setObjectName("hotkey_hint")
        top_bar.addWidget(hint)

        # Expand/collapse
        self.expand_btn = QPushButton("\u25bc")
        self.expand_btn.setObjectName("expand_btn")
        self.expand_btn.setFixedSize(20, 20)
        self.expand_btn.clicked.connect(self.toggle_expand)
        top_bar.addWidget(self.expand_btn)

        # Close
        close_btn = QPushButton("\u00d7")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(20, 20)
        close_btn.clicked.connect(self.hide)
        top_bar.addWidget(close_btn)

        self.c_layout.addLayout(top_bar)

        # ── Expandable content ──
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 10, 0, 0)
        self.content_layout.setSpacing(8)

        # Transcript section
        t_header = QHBoxLayout()
        t_label = QLabel("TRANSCRIPT")
        t_label.setObjectName("section_header")
        t_header.addWidget(t_label)

        self.speaking_indicator = QLabel("")
        self.speaking_indicator.setObjectName("ai_status")
        self.speaking_indicator.setStyleSheet("color: rgba(255, 200, 50, 0.8);")
        t_header.addStretch()
        t_header.addWidget(self.speaking_indicator)
        self.content_layout.addLayout(t_header)

        self.transcript = QTextEdit()
        self.transcript.setObjectName("transcript_area")
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("Press Alt+R to start listening...")
        self.transcript.setFixedHeight(120)
        self.content_layout.addWidget(self.transcript)

        # AI response section
        a_header = QHBoxLayout()
        a_label = QLabel("AI RESPONSE")
        a_label.setObjectName("section_header")
        a_header.addWidget(a_label)

        self.ai_status = QLabel("")
        self.ai_status.setObjectName("ai_status")
        a_header.addStretch()
        a_header.addWidget(self.ai_status)

        self.copy_btn = QPushButton("copy")
        self.copy_btn.setObjectName("icon_btn")
        self.copy_btn.setFixedHeight(22)
        self.copy_btn.clicked.connect(self._copy_response)
        a_header.addWidget(self.copy_btn)

        self.content_layout.addLayout(a_header)

        self.ai_response = QTextEdit()
        self.ai_response.setObjectName("ai_area")
        self.ai_response.setReadOnly(True)
        self.ai_response.setPlaceholderText("AI suggestions appear here...")
        self.ai_response.setFixedHeight(160)
        self.content_layout.addWidget(self.ai_response)

        # Bottom controls
        controls = QHBoxLayout()
        controls.setSpacing(6)

        self.record_btn = QPushButton("REC")
        self.record_btn.setObjectName("icon_btn")
        self.record_btn.setFixedHeight(26)
        controls.addWidget(self.record_btn)

        self.screenshot_btn = QPushButton("SNAP")
        self.screenshot_btn.setObjectName("icon_btn")
        self.screenshot_btn.setFixedHeight(26)
        controls.addWidget(self.screenshot_btn)

        self.ask_btn = QPushButton("ASK")
        self.ask_btn.setObjectName("icon_btn")
        self.ask_btn.setFixedHeight(26)
        controls.addWidget(self.ask_btn)

        controls.addStretch()

        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("provider_combo")
        self.provider_combo.addItems(["claude", "codex", "gemini"])
        self.provider_combo.setFixedWidth(75)
        self.provider_combo.setFixedHeight(24)
        controls.addWidget(self.provider_combo)

        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("provider_combo")
        self.profile_combo.addItems(["sde", "ml", "devops", "ai_automation", "java_fullstack"])
        self.profile_combo.setFixedWidth(85)
        self.profile_combo.setFixedHeight(24)
        controls.addWidget(self.profile_combo)

        self.content_layout.addLayout(controls)

        self.c_layout.addWidget(self.content)
        self.main_layout.addWidget(self.container)

        # ── Connect events ──
        event_bus.overlay_toggle.connect(self.toggle_visibility)
        event_bus.transcript_interim.connect(self._on_interim)
        event_bus.transcript_final.connect(self._on_final)
        event_bus.transcript_updated.connect(self._on_transcript_updated)
        event_bus.ai_response_started.connect(self._on_ai_started)
        event_bus.ai_response_chunk.connect(self._on_ai_chunk)
        event_bus.ai_response_complete.connect(self._on_ai_complete)
        event_bus.ai_error.connect(self._on_ai_error)
        event_bus.screenshot_analyzing.connect(self._on_screenshot)
        event_bus.recording_started.connect(self._on_rec_started)
        event_bus.recording_stopped.connect(self._on_rec_stopped)
        event_bus.status_update.connect(self._on_status)

        self._finalized_text = ""
        self._ai_text = ""

    # ── Transcript handling ───────────────────────────────────────

    def _on_interim(self, text):
        display = self._finalized_text
        if display:
            display += "\n"
        display += f"\u25b8 {text}"
        self.transcript.setPlainText(display)
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)
        self.speaking_indicator.setText("\u25cf speaking")
        self.speaking_indicator.setStyleSheet("color: rgba(255, 200, 50, 0.8);")
        self.status_dot.setStyleSheet("color: rgba(255, 200, 50, 0.9);")

    def _on_final(self, text):
        if text:
            self._finalized_text += ("" if not self._finalized_text else "\n") + text
        self.transcript.setPlainText(self._finalized_text)
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)
        self.speaking_indicator.setText("")
        self.status_dot.setStyleSheet("color: rgba(99, 132, 255, 0.9);")

    def _on_transcript_updated(self, text):
        pass  # handled by _on_final

    # ── AI response handling ──────────────────────────────────────

    def _on_ai_started(self):
        self._ai_text = ""
        self.ai_response.clear()
        self.ai_status.setText("thinking...")
        self.ai_status.setStyleSheet("color: rgba(255, 200, 50, 0.8);")
        self.status_dot.setStyleSheet("color: rgba(255, 200, 50, 0.9);")

    def _on_ai_chunk(self, chunk):
        self._ai_text += chunk
        self.ai_response.setPlainText(self._ai_text)
        self.ai_response.moveCursor(QTextCursor.MoveOperation.End)

    def _on_ai_complete(self, text):
        self._ai_text = text
        self.ai_response.setPlainText(text)
        self.ai_response.moveCursor(QTextCursor.MoveOperation.End)
        self.ai_status.setText("\u2713 ready")
        self.ai_status.setStyleSheet("color: rgba(120, 210, 120, 0.8);")
        self.status_dot.setStyleSheet("color: rgba(120, 210, 120, 0.9);")

    def _on_ai_error(self, error):
        self.ai_status.setText("error")
        self.ai_status.setStyleSheet("color: rgba(255, 100, 100, 0.8);")
        self.ai_response.setPlainText(f"Error: {error}")
        self.status_dot.setStyleSheet("color: rgba(255, 80, 80, 0.9);")

    def _on_screenshot(self):
        self.ai_status.setText("analyzing...")
        self.ai_status.setStyleSheet("color: rgba(99, 180, 255, 0.8);")

    # ── Recording state ───────────────────────────────────────────

    def _on_rec_started(self):
        self.record_btn.setText("\u25a0 STOP")
        self.record_btn.setObjectName("icon_btn_active")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.status_text.setText("listening")
        self.status_dot.setStyleSheet("color: rgba(255, 80, 80, 0.9);")

    def _on_rec_stopped(self):
        self.record_btn.setText("REC")
        self.record_btn.setObjectName("icon_btn")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.status_text.setText("ready")
        self.status_dot.setStyleSheet("color: rgba(80, 80, 80, 0.8);")

    def _on_status(self, text):
        self.status_text.setText(text)

    # ── Actions ───────────────────────────────────────────────────

    def _copy_response(self):
        if self._ai_text:
            QApplication.clipboard().setText(self._ai_text)
            self.ai_status.setText("copied!")
            self.ai_status.setStyleSheet("color: rgba(120, 210, 120, 0.8);")

    def toggle_expand(self):
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        self.expand_btn.setText("\u25bc" if self._expanded else "\u25b6")
        self.adjustSize()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    # ── Drag support ──────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Paint rounded background ──────────────────────────────────

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        opacity = self.config.get("general", "overlay_opacity", 0.92)
        painter.setBrush(QBrush(QColor(12, 12, 16, int(opacity * 255))))
        painter.setPen(QPen(QColor(255, 255, 255, 18), 1))
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 16, 16)
        painter.end()

    # ── Public accessors for main.py wiring ───────────────────────

    @property
    def control_bar(self):
        """Compat layer so main.py can wire buttons."""
        return self
