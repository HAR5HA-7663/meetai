"""Cluely-inspired dark glass-morphism theme."""

DARK_THEME = """
/* Main floating bar */
QWidget#overlay_main {
    background-color: rgba(12, 12, 16, 190);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 16px;
}

/* Compact bar mode */
QWidget#compact_bar {
    background: transparent;
}

QLabel#app_title {
    color: rgba(255, 255, 255, 0.4);
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1.5px;
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
}

QLabel#status_dot {
    font-size: 8px;
}

QLabel#status_text {
    color: rgba(255, 255, 255, 0.45);
    font-size: 10px;
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
}

QLabel#hotkey_hint {
    color: rgba(255, 255, 255, 0.2);
    font-size: 9px;
    font-family: "JetBrains Mono", "Fira Code", monospace;
}

/* Transcript area */
QLabel#section_header {
    color: rgba(255, 255, 255, 0.3);
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1.5px;
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
}

QTextEdit#transcript_area {
    background-color: rgba(255, 255, 255, 0.02);
    color: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 12px;
    line-height: 1.5;
    font-family: "Inter", "SF Pro Text", "Segoe UI", sans-serif;
    selection-background-color: rgba(99, 132, 255, 0.3);
}

/* AI response area */
QTextEdit#ai_area {
    background-color: rgba(99, 132, 255, 0.04);
    color: rgba(200, 215, 255, 0.92);
    border: 1px solid rgba(99, 132, 255, 0.1);
    border-radius: 10px;
    padding: 10px 12px;
    font-size: 12.5px;
    line-height: 1.5;
    font-family: "Inter", "SF Pro Text", "Segoe UI", sans-serif;
    selection-background-color: rgba(99, 132, 255, 0.3);
}

QLabel#ai_status {
    font-size: 10px;
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
}

/* Buttons */
QPushButton#icon_btn {
    background: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 11px;
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
}

QPushButton#icon_btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.8);
}

QPushButton#icon_btn_active {
    background: rgba(255, 60, 60, 0.15);
    color: rgba(255, 120, 120, 0.9);
    border: 1px solid rgba(255, 60, 60, 0.2);
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 11px;
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
}

QPushButton#close_btn {
    background: transparent;
    color: rgba(255, 255, 255, 0.25);
    border: none;
    border-radius: 6px;
    padding: 2px 6px;
    font-size: 13px;
}

QPushButton#close_btn:hover {
    background: rgba(255, 60, 60, 0.2);
    color: rgba(255, 100, 100, 0.9);
}

QPushButton#expand_btn {
    background: transparent;
    color: rgba(255, 255, 255, 0.3);
    border: none;
    font-size: 10px;
}

QPushButton#expand_btn:hover {
    color: rgba(255, 255, 255, 0.7);
}

/* Provider selector */
QComboBox#provider_combo {
    background: rgba(255, 255, 255, 0.05);
    color: rgba(255, 255, 255, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 10px;
    font-family: "Inter", "SF Pro Display", "Segoe UI", sans-serif;
}

QComboBox#provider_combo QAbstractItemView {
    background: rgba(18, 18, 24, 250);
    color: rgba(255, 255, 255, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    selection-background-color: rgba(99, 132, 255, 0.25);
}
"""
