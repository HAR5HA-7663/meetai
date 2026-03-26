"""Cluely-style overlay: thin sidebar strip, draggable on Wayland, click-through friendly."""

import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QApplication, QScrollArea,
)
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QTextCursor

from overlay.theme import DARK_THEME
from core.event_bus import event_bus

import logging
logger = logging.getLogger(__name__)


class OverlayWindow(QWidget):
    """Thin floating sidebar — like Cluely. Sits at screen edge, doesn't block your work."""

    COLLAPSED_WIDTH = 340
    COLLAPSED_HEIGHT = 36
    EXPANDED_WIDTH = 340
    EXPANDED_HEIGHT = 420

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._expanded = False  # Start collapsed — just a thin bar
        self._drag_pos = None
        self._finalized_text = ""
        self._ai_text = ""

        self._setup_window()
        self._build_ui()
        self.setStyleSheet(DARK_THEME)
        self._hide_from_capture()
        self._position_window()
        self._apply_size()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.BypassWindowManagerHint  # Enables free positioning on Wayland
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

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
        # Right edge, vertically centered
        x = geo.right() - self.COLLAPSED_WIDTH - 10
        y = geo.top() + (geo.height() - self.COLLAPSED_HEIGHT) // 3
        self.move(x, y)

    def _apply_size(self):
        if self._expanded:
            self.setFixedSize(self.EXPANDED_WIDTH, self.EXPANDED_HEIGHT)
        else:
            self.setFixedSize(self.COLLAPSED_WIDTH, self.COLLAPSED_HEIGHT)

    # ── UI ──

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.container = QWidget()
        self.container.setObjectName("overlay_main")
        self.c_layout = QVBoxLayout(self.container)
        self.c_layout.setContentsMargins(12, 8, 12, 8)
        self.c_layout.setSpacing(0)

        # ── Top bar (always visible) ──
        top = QHBoxLayout()
        top.setSpacing(6)

        self.status_dot = QLabel("\u25cf")
        self.status_dot.setFixedWidth(10)
        self.status_dot.setStyleSheet("color: rgba(70,70,70,0.9); font-size: 9px;")
        top.addWidget(self.status_dot)

        title = QLabel("MEETAI")
        title.setObjectName("app_title")
        top.addWidget(title)

        self.status_text = QLabel("ready")
        self.status_text.setObjectName("status_text")
        top.addWidget(self.status_text)

        top.addStretch()

        self.expand_btn = QPushButton("\u25b6")
        self.expand_btn.setObjectName("expand_btn")
        self.expand_btn.setFixedSize(18, 18)
        self.expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.expand_btn.clicked.connect(self.toggle_expand)
        top.addWidget(self.expand_btn)

        close_btn = QPushButton("\u00d7")
        close_btn.setObjectName("close_btn")
        close_btn.setFixedSize(18, 18)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide)
        top.addWidget(close_btn)

        self.c_layout.addLayout(top)

        # ── Expanded content ──
        self.content = QWidget()
        cl = QVBoxLayout(self.content)
        cl.setContentsMargins(0, 8, 0, 0)
        cl.setSpacing(6)

        # Transcript
        th = QHBoxLayout()
        tl = QLabel("TRANSCRIPT")
        tl.setObjectName("section_header")
        th.addWidget(tl)
        self.speaking_indicator = QLabel("")
        self.speaking_indicator.setObjectName("ai_status")
        th.addStretch()
        th.addWidget(self.speaking_indicator)
        cl.addLayout(th)

        self.transcript = QTextEdit()
        self.transcript.setObjectName("transcript_area")
        self.transcript.setReadOnly(True)
        self.transcript.setPlaceholderText("Alt+R to listen...")
        self.transcript.setMaximumHeight(100)
        cl.addWidget(self.transcript)

        # AI response
        ah = QHBoxLayout()
        al = QLabel("ANSWER")
        al.setObjectName("section_header")
        ah.addWidget(al)
        self.ai_status = QLabel("")
        self.ai_status.setObjectName("ai_status")
        ah.addStretch()
        ah.addWidget(self.ai_status)
        self.copy_btn = QPushButton("copy")
        self.copy_btn.setObjectName("icon_btn")
        self.copy_btn.setFixedHeight(20)
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._copy_response)
        ah.addWidget(self.copy_btn)
        cl.addLayout(ah)

        self.ai_response = QTextEdit()
        self.ai_response.setObjectName("ai_area")
        self.ai_response.setReadOnly(True)
        self.ai_response.setPlaceholderText("Suggestions here...")
        cl.addWidget(self.ai_response)

        # Controls row
        cr = QHBoxLayout()
        cr.setSpacing(4)

        self.record_btn = QPushButton("REC")
        self.record_btn.setObjectName("icon_btn")
        self.record_btn.setFixedHeight(24)
        self.record_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cr.addWidget(self.record_btn)

        self.screenshot_btn = QPushButton("SNAP")
        self.screenshot_btn.setObjectName("icon_btn")
        self.screenshot_btn.setFixedHeight(24)
        self.screenshot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cr.addWidget(self.screenshot_btn)

        self.ask_btn = QPushButton("ASK")
        self.ask_btn.setObjectName("icon_btn")
        self.ask_btn.setFixedHeight(24)
        self.ask_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cr.addWidget(self.ask_btn)

        cr.addStretch()

        self.provider_combo = QComboBox()
        self.provider_combo.setObjectName("provider_combo")
        self.provider_combo.addItems(["claude", "codex", "gemini"])
        self.provider_combo.setFixedWidth(70)
        self.provider_combo.setFixedHeight(22)
        cr.addWidget(self.provider_combo)

        self.profile_combo = QComboBox()
        self.profile_combo.setObjectName("provider_combo")
        self.profile_combo.addItems(["sde", "ml", "devops", "ai_automation", "java_fullstack"])
        self.profile_combo.setFixedWidth(80)
        self.profile_combo.setFixedHeight(22)
        cr.addWidget(self.profile_combo)

        cl.addLayout(cr)

        self.content.setVisible(False)
        self.c_layout.addWidget(self.content)
        root.addWidget(self.container)

        # ── Events ──
        event_bus.overlay_toggle.connect(self.toggle_visibility)
        event_bus.transcript_interim.connect(self._on_interim)
        event_bus.transcript_final.connect(self._on_final)
        event_bus.transcript_updated.connect(lambda t: None)
        event_bus.ai_response_started.connect(self._on_ai_started)
        event_bus.ai_response_chunk.connect(self._on_ai_chunk)
        event_bus.ai_response_complete.connect(self._on_ai_complete)
        event_bus.ai_error.connect(self._on_ai_error)
        event_bus.screenshot_analyzing.connect(lambda: self.ai_status.setText("analyzing..."))
        event_bus.recording_started.connect(self._on_rec_started)
        event_bus.recording_stopped.connect(self._on_rec_stopped)
        event_bus.status_update.connect(lambda t: self.status_text.setText(t))

    # ── Transcript ──

    def _on_interim(self, text):
        d = self._finalized_text
        if d:
            d += "\n"
        d += f"\u25b8 {text}"
        self.transcript.setPlainText(d)
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)
        self.speaking_indicator.setText("\u25cf live")
        self.speaking_indicator.setStyleSheet("color: rgba(255,200,50,0.8);")
        self._set_dot("yellow")
        # Auto-expand when speech starts
        if not self._expanded:
            self.toggle_expand()

    def _on_final(self, text):
        if text:
            self._finalized_text += ("\n" if self._finalized_text else "") + text
        self.transcript.setPlainText(self._finalized_text)
        self.transcript.moveCursor(QTextCursor.MoveOperation.End)
        self.speaking_indicator.setText("")

    # ── AI ──

    def _on_ai_started(self):
        self._ai_text = ""
        self.ai_response.clear()
        self.ai_status.setText("thinking...")
        self.ai_status.setStyleSheet("color: rgba(255,200,50,0.8);")
        self._set_dot("yellow")
        if not self._expanded:
            self.toggle_expand()

    def _on_ai_chunk(self, chunk):
        self._ai_text += chunk
        self.ai_response.setPlainText(self._ai_text)
        self.ai_response.moveCursor(QTextCursor.MoveOperation.End)

    def _on_ai_complete(self, text):
        self._ai_text = text
        self.ai_response.setPlainText(text)
        self.ai_response.moveCursor(QTextCursor.MoveOperation.End)
        self.ai_status.setText("\u2713 ready")
        self.ai_status.setStyleSheet("color: rgba(120,210,120,0.8);")
        self._set_dot("green")

    def _on_ai_error(self, err):
        self.ai_status.setText("error")
        self.ai_status.setStyleSheet("color: rgba(255,100,100,0.8);")
        self.ai_response.setPlainText(f"Error: {err}")
        self._set_dot("red")

    # ── Recording ──

    def _on_rec_started(self):
        self.record_btn.setText("\u25a0 STOP")
        self.record_btn.setObjectName("icon_btn_active")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.status_text.setText("listening")
        self._set_dot("red")

    def _on_rec_stopped(self):
        self.record_btn.setText("REC")
        self.record_btn.setObjectName("icon_btn")
        self.record_btn.style().unpolish(self.record_btn)
        self.record_btn.style().polish(self.record_btn)
        self.status_text.setText("ready")
        self._set_dot("gray")

    # ── Actions ──

    def _copy_response(self):
        if self._ai_text:
            QApplication.clipboard().setText(self._ai_text)
            self.ai_status.setText("copied!")

    def _set_dot(self, color):
        colors = {
            "gray": "rgba(70,70,70,0.9)",
            "red": "rgba(255,70,70,0.9)",
            "yellow": "rgba(255,200,50,0.9)",
            "green": "rgba(120,210,120,0.9)",
            "blue": "rgba(99,132,255,0.9)",
        }
        self.status_dot.setStyleSheet(f"color: {colors.get(color, colors['gray'])}; font-size: 9px;")

    def toggle_expand(self):
        self._expanded = not self._expanded
        self.content.setVisible(self._expanded)
        self.expand_btn.setText("\u25bc" if self._expanded else "\u25b6")
        self._apply_size()

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()

    # ── Drag (works on Wayland with BypassWindowManagerHint) ──

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and (event.buttons() & Qt.MouseButton.LeftButton):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    # ── Paint ──

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        opacity = self.config.get("general", "overlay_opacity", 0.92)
        p.setBrush(QBrush(QColor(12, 12, 16, int(opacity * 255))))
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        p.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)
        p.end()

    @property
    def control_bar(self):
        return self
