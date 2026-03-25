"""Dark glass-morphism theme for the overlay."""

DARK_THEME = """
QWidget#overlay_main {
    background-color: rgba(15, 15, 20, 235);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}

QWidget#title_bar {
    background-color: rgba(25, 25, 35, 240);
    border-top-left-radius: 12px;
    border-top-right-radius: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

QLabel#title_label {
    color: rgba(255, 255, 255, 0.9);
    font-size: 13px;
    font-weight: 600;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
}

QLabel#status_label {
    color: rgba(120, 200, 120, 0.9);
    font-size: 11px;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
}

QTextEdit#transcript_panel {
    background-color: rgba(20, 20, 30, 200);
    color: rgba(220, 220, 230, 0.95);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    font-family: "JetBrains Mono", "Fira Code", "Cascadia Code", monospace;
    selection-background-color: rgba(100, 140, 255, 0.3);
}

QTextEdit#ai_panel {
    background-color: rgba(25, 30, 50, 200);
    color: rgba(180, 210, 255, 0.95);
    border: 1px solid rgba(100, 140, 255, 0.15);
    border-radius: 8px;
    padding: 8px;
    font-size: 12px;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
    selection-background-color: rgba(100, 140, 255, 0.3);
}

QLabel#section_label {
    color: rgba(255, 255, 255, 0.5);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
}

QPushButton#control_btn {
    background-color: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 500;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
}

QPushButton#control_btn:hover {
    background-color: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.2);
}

QPushButton#control_btn:pressed {
    background-color: rgba(255, 255, 255, 0.04);
}

QPushButton#control_btn_active {
    background-color: rgba(255, 80, 80, 0.2);
    color: rgba(255, 120, 120, 0.95);
    border: 1px solid rgba(255, 80, 80, 0.3);
    border-radius: 6px;
    padding: 6px 12px;
    font-size: 11px;
    font-weight: 500;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
}

QPushButton#title_btn {
    background-color: transparent;
    color: rgba(255, 255, 255, 0.5);
    border: none;
    padding: 2px 6px;
    font-size: 14px;
}

QPushButton#title_btn:hover {
    color: rgba(255, 255, 255, 0.9);
}

QComboBox#provider_select {
    background-color: rgba(255, 255, 255, 0.06);
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 11px;
    font-family: "Inter", "Segoe UI", "SF Pro", sans-serif;
}

QComboBox#provider_select QAbstractItemView {
    background-color: rgba(25, 25, 35, 250);
    color: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.1);
    selection-background-color: rgba(100, 140, 255, 0.3);
}
"""
