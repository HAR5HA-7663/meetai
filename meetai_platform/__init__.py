import sys

_platform = sys.platform


def is_windows():
    return _platform == "win32"


def is_macos():
    return _platform == "darwin"


def is_linux():
    return _platform.startswith("linux")


def hide_from_capture(window):
    """Hide a PyQt6 window from screen capture, platform-specific."""
    if is_windows():
        from meetai_platform.windows import hide_from_capture as _hide
        _hide(window)
    elif is_macos():
        from meetai_platform.macos import hide_from_capture as _hide
        _hide(window)
    else:
        from meetai_platform.linux import hide_from_capture as _hide
        _hide(window)
