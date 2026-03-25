import sys

_platform = sys.platform


def is_windows():
    return _platform == "win32"


def is_macos():
    return _platform == "darwin"


def is_linux():
    return _platform.startswith("linux")


def get_platform_module():
    if is_windows():
        from platform import windows as mod
    elif is_macos():
        from platform import macos as mod
    else:
        from platform import linux as mod
    return mod


def hide_from_capture(window):
    """Hide a PyQt6 window from screen capture, platform-specific."""
    if is_windows():
        from meetai.platform.windows import hide_from_capture as _hide
        _hide(window)
    elif is_macos():
        from meetai.platform.macos import hide_from_capture as _hide
        _hide(window)
    else:
        from meetai.platform.linux import hide_from_capture as _hide
        _hide(window)
