"""System tray icon with menu for MeetAI."""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QAction
from PyQt6.QtCore import QSize

from core.event_bus import event_bus


def _create_icon():
    """Create a simple colored circle icon."""
    size = 64
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QBrush(QColor(100, 140, 255)))
    painter.setPen(QColor(60, 100, 220))
    painter.drawEllipse(4, 4, size - 8, size - 8)
    # Draw 'M' letter
    painter.setPen(QColor(255, 255, 255))
    font = painter.font()
    font.setPixelSize(32)
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x0084, "M")  # AlignCenter
    painter.end()
    return QIcon(pixmap)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, app, overlay_window, parent=None):
        super().__init__(parent)
        self.app = app
        self.overlay_window = overlay_window
        self.setIcon(_create_icon())
        self.setToolTip("MeetAI - Meeting Assistant")

        menu = QMenu()

        show_action = QAction("Show/Hide Overlay", menu)
        show_action.triggered.connect(lambda: event_bus.overlay_toggle.emit())
        menu.addAction(show_action)

        menu.addSeparator()

        screenshot_action = QAction("Take Screenshot", menu)
        screenshot_action.triggered.connect(lambda: event_bus.screenshot_taken.emit(""))
        menu.addAction(screenshot_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)

        self.setContextMenu(menu)
        self.activated.connect(self._on_activated)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            event_bus.overlay_toggle.emit()
