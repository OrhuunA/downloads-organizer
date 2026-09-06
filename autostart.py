"""
"Bilgisayar açılışında otomatik başlat" özelliği - platforma göre.
"Start at login" feature - implemented per platform.

Windows : Kayıt defteri (HKCU...\\Run)   / Windows Registry Run key
macOS   : ~/Library/LaunchAgents plist   / LaunchAgent
Linux   : ~/.config/autostart .desktop   / XDG autostart entry

Dışarıya açılan tek API: is_enabled() / enable() / disable() / toggle()
The only public API: is_enabled() / enable() / disable() / toggle()
"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

APP_ID = "IndirilenlerDuzenleyici"


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


# ------------------------------------------------------------------ Windows

def _windows_command() -> str:
    return " ".join(f'"{part}"' for part in _launch_command_parts())


def _windows_is_enabled() -> bool:
    import winreg  # yalnizca Windows'ta mevcut

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"
        ) as key:
            value, _ = winreg.QueryValueEx(key, APP_ID)
            return bool(value)
    except FileNotFoundError:
        return False


def _windows_enable() -> None:
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Software\Microsoft\Windows\CurrentVersion\Run",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, APP_ID, 0, winreg.REG_SZ, _windows_command())


def _windows_disable() -> None:
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, APP_ID)
    except FileNotFoundError:
        pass


# -------------------------------------------------------------------- macOS

def _mac_plist_path() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"com.{APP_ID.lower()}.plist"


def _mac_is_enabled() -> bool:
    return _mac_plist_path().exists()


def _mac_enable() -> None:
    plist = _mac_plist_path()
    plist.parent.mkdir(parents=True, exist_ok=True)
    args_xml = "\n".join(f"    <string>{part}</string>" for part in _launch_command_parts())
    content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.{APP_ID.lower()}</string>
  <key>ProgramArguments</key>
  <array>
{args_xml}
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>
"""
    plist.write_text(content, encoding="utf-8")
    subprocess.run(["launchctl", "load", str(plist)], capture_output=True)


def _mac_disable() -> None:
    plist = _mac_plist_path()
    if plist.exists():
        subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
        plist.unlink()


# ------------------------------------------------------------------- Linux

def _linux_desktop_path() -> Path:
    return Path.home() / ".config" / "autostart" / f"{APP_ID.lower()}.desktop"


def _linux_is_enabled() -> bool:
    return _linux_desktop_path().exists()


def _linux_enable() -> None:
    path = _linux_desktop_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    exec_line = " ".join(f'"{part}"' for part in _launch_command_parts())
    content = f"""[Desktop Entry]
Type=Application
Name=İndirilenler Düzenleyici
Exec={exec_line}
X-GNOME-Autostart-enabled=true
"""
    path.write_text(content, encoding="utf-8")


def _linux_disable() -> None:
    path = _linux_desktop_path()
    if path.exists():
        path.unlink()


# ------------------------------------------------------------------ Public

def is_enabled() -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            return _windows_is_enabled()
        elif system == "Darwin":
            return _mac_is_enabled()
        else:
            return _linux_is_enabled()
    except Exception:
        return False


def enable() -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            _windows_enable()
        elif system == "Darwin":
            _mac_enable()
        else:
            _linux_enable()
        return True
    except Exception:
        return False


def disable() -> bool:
    system = platform.system()
    try:
        if system == "Windows":
            _windows_disable()
        elif system == "Darwin":
            _mac_disable()
        else:
            _linux_disable()
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
