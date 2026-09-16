"""
Platforma ozel (Windows / macOS / Linux) davranislari tek bir yerde
toplayan paket. Uygulamanin geri kalani (autostart.py, theme.py,
tray_app.py) artik `platform.system()` ile kendi ici dallanma YAPMAZ;
bunun yerine bu paketin disa verdigi `backend` nesnesini kullanir.

This package centralizes all platform-specific (Windows / macOS / Linux)
behavior in one place. The rest of the app (autostart.py, theme.py,
tray_app.py) no longer branches on `platform.system()` itself -- it uses
the `backend` object this package exposes instead.

Kullanim / Usage:
    from platform_backend import backend
    backend.open_path(some_path)
    backend.detect_system_theme()
    ...
"""

from __future__ import annotations

import platform

from .base import PlatformBackend

__all__ = ["backend", "PlatformBackend"]


def _create_backend() -> PlatformBackend:
    system = platform.system()
    if system == "Windows":
        from .windows import WindowsBackend

        return WindowsBackend()
    if system == "Darwin":
        from .macos import MacOSBackend

        return MacOSBackend()
    from .linux import LinuxBackend

    return LinuxBackend()


# Surec basina bir kere olusturulan, tum uygulamanin paylastigi tekil
# (singleton) backend nesnesi.
# A single backend instance created once per process, shared by the
# whole app.
backend: PlatformBackend = _create_backend()
