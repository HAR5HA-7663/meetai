"""Main overlay window: frameless, transparent, always-on-top, draggable."""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt6.QtCore import Qt, QPoint, QSize
from PyQt6.QtGui import QPainter, QColor, QBrush

from overlay.widgets import TranscriptPanel, AIResponsePanel, ControlBar
from overlay.theme import DARK_THEME
from core.event_bus import event_bus

import platform as platform_mod


class TitleBar(QWidget):
    """Custom draggable title bar."""

    def __init__(self, parent_window, parent=None):
        super().__init__(parent)
        self.parent_window = parent_window
        self.setObjectName("title_bar")
        self.setFixedHeight(32)
        self._drag_pos = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 6, 0)
        layout.setSpacing(4)

        self.title = QLabel("MeetAI")
        self.title.setObjectName("title_label")
        layout.addWidget(self.title)

        layout.addStretch()

        self.minimize_btn = QPushButton("\u2013")
        self.minimize_btn.setObjectName("title_btn")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.clicked.connect(self._minimize)
        layout.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("\u00d7")
        self.close_btn.setObjectName("title_btn")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.clicked.connect(self._close)
        layout.addWidget(self.close_btn)

    def _minimize(self):
        self.parent_window.showMinimized()

    def _close(self):
        self.parent_window.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.parent_window.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.parent_window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class OverlayWindow(QWidget):
    """The main overlay window that sits on top of everything."""

    def __init__(self, config):
        super().__init__()
        self.config = config
        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._hide_from_capture()
        self._position_window()

    def _setup_window(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool  # Skip taskbar and alt-tab
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("overlay_main")

        width = self.config.get("general", "overlay_width", 420)
        height = self.config.get("general", "overlay_height", 600)
        self.resize(width, height)
        self.setMinimumSize(300, 400)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Container widget for background painting
        self.container = QWidget()
        self.container.setObjectName("overlay_main")
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Title bar
        self.title_bar = TitleBar(self)
        container_layout.addWidget(self.title_bar)

        # Content area
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(10, 6, 10, 10)
        content_layout.setSpacing(8)

        # Transcript panel (top, 40% height)
        self.transcript_panel = TranscriptPanel()
        content_layout.addWidget(self.transcript_panel, stretch=4)

        # AI response panel (bottom, 60% height)
        self.ai_panel = AIResponsePanel()
        content_layout.addWidget(self.ai_panel, stretch=6)

        # Control bar
        self.control_bar = ControlBar()
        content_layout.addWidget(self.control_bar)

        container_layout.addWidget(content, stretch=1)
        main_layout.addWidget(self.container)

        # Connect overlay toggle
        event_bus.overlay_toggle.connect(self.toggle_visibility)

    def _apply_theme(self):
        self.setStyleSheet(DARK_THEME)

    def _hide_from_capture(self):
        """Call platform-specific API to hide from screen capture."""
        try:
            from meetai_platform import hide_from_capture
            hide_from_capture(self)
        except ImportError:
            pass
        # Direct import approach
        import sys
        if sys.platform == "win32":
            from platform.windows import hide_from_capture
            hide_from_capture(self)
        elif sys.platform == "darwin":
            from platform.macos import hide_from_capture
            hide_from_capture(self)
        else:
            from platform.linux import hide_from_capture
            hide_from_capture(self)

    def _position_window(self):
        """Position the window at the configured location."""
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        pos = self.config.get("general", "overlay_position", "top-right")

        if pos == "top-right":
            x = geo.right() - self.width() - 20
            y = geo.top() + 20
        elif pos == "top-left":
            x = geo.left() + 20
            y = geo.top() + 20
        elif pos == "bottom-right":
            x = geo.right() - self.width() - 20
            y = geo.bottom() - self.height() - 20
        elif pos == "bottom-left":
            x = geo.left() + 20
            y = geo.bottom() - self.height() - 20
        elif pos == "center":
            x = geo.center().x() - self.width() // 2
            y = geo.center().y() - self.height() // 2
        else:
            x = geo.right() - self.width() - 20
            y = geo.top() + 20

        self.move(x, y)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.raise_()
            self.activateWindow()

    def paintEvent(self, event):
        """Paint rounded rectangle background."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        opacity = self.config.get("general", "overlay_opacity", 0.92)
        bg_color = QColor(15, 15, 20, int(opacity * 255))
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QColor(255, 255, 255, 20))
        painter.drawRoundedRect(self.rect(), 12, 12)
        painter.end()

    # Resize support via edge dragging
    _resize_margin = 6

    def _edge_at(self, pos):
        r = self.rect()
        m = self._resize_margin
        edges = Qt.Edge(0)
        if pos.x() < m:
            edges |= Qt.Edge.LeftEdge
        elif pos.x() > r.width() - m:
            edges |= Qt.Edge.RightEdge
        if pos.y() < m:
            edges |= Qt.Edge.TopEdge
        elif pos.y() > r.height() - m:
            edges |= Qt.Edge.BottomEdge
        return edges

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            edges = self._edge_at(event.position().toPoint())
            if edges:
                if hasattr(self.windowHandle(), 'startSystemResize'):
                    self.windowHandle().startSystemResize(edges)
        super().mousePressEvent(event)
