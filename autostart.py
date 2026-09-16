"""
"Bilgisayar açılışında otomatik başlat" özelliği - platforma göre.
"Start at login" feature - implemented per platform.

Platforma ozel kisim (Windows kayit defteri / macOS LaunchAgent / Linux
.desktop dosyasi) artik `platform_backend` paketinde yasiyor. Bu dosya,
programi yeniden baslatmak icin gereken komutu (_launch_command_parts)
hesaplayip dogru backend'e ileten INCE bir sarmalayicidir -- geri kalan
tum kod (import autostart / autostart.is_enabled() / .enable() /
.disable() / .toggle()) hicbir degisiklik gerektirmeden calismaya
devam eder.

The platform-specific part (Windows registry / macOS LaunchAgent /
Linux .desktop file) now lives in the `platform_backend` package. This
file is a THIN WRAPPER that computes the relaunch command
(_launch_command_parts) and forwards it to the right backend -- all
other existing code (import autostart / autostart.is_enabled() /
.enable() / .disable() / .toggle()) keeps working with no changes.
"""

from __future__ import annotations

import sys
from pathlib import Path

from platform_backend import backend

APP_ID = "IndirilenlerDuzenleyici"
DISPLAY_NAME = "İndirilenler Düzenleyici"


def _windowless_python() -> str:
    """Mumkunse pythonw.exe (konsol penceresi acmayan) donuyor, yoksa
    mevcut yorumlayiciyi kullanir."""
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")
    if pythonw.exists():
        return str(pythonw)
    return str(exe)


def _script_path() -> Path:
    return Path(__file__).resolve().parent / "tray_app.py"


def _launch_command_parts() -> list:
    """Programi yeniden baslatmak icin kullanilacak komut parcalarini
    dondurur. PyInstaller ile TEK DOSYA (.exe) olarak paketlenmisse
    sadece .exe'nin kendisi calistirilir (Python'a gerek yoktur);
    kaynaktan calisirken pythonw.exe + tray_app.py kullanilir."""
    if getattr(sys, "frozen", False):
        return [sys.executable]
    return [_windowless_python(), str(_script_path())]


# ------------------------------------------------------------------ Public

def is_enabled() -> bool:
    try:
        return backend.is_autostart_enabled(APP_ID)
    except Exception:
        return False


def enable() -> bool:
    try:
        backend.enable_autostart(APP_ID, _launch_command_parts(), DISPLAY_NAME)
        return True
    except Exception:
        return False


def disable() -> bool:
    try:
        backend.disable_autostart(APP_ID)
        return True
    except Exception:
        return False


def toggle() -> bool:
    """Islemi tersine cevirir ve sonrasindaki durumu (True=acik) dondurur."""
    if is_enabled():
        disable()
        return False
    enable()
    return True
