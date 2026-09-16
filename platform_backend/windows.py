"""Windows'a ozel platform backend'i.
Windows-specific platform backend.

Buradaki mantik, oncesinde autostart.py / tray_app.py / theme.py icinde
dagitik halde bulunan Windows koduyla BIREBIR AYNIDIR -- yalnizca bu
pakete tasindi, davranis degistirilmedi.

The logic here is IDENTICAL to the Windows code that used to be
scattered across autostart.py / tray_app.py / theme.py -- it was only
moved into this package, behavior was not changed.
"""

from __future__ import annotations

import os
import subprocess
import webbrowser
from pathlib import Path

_RUN_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
_THEME_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"


class WindowsBackend:
    # ---- autostart ------------------------------------------------------

    def is_autostart_enabled(self, app_id: str) -> bool:
        import winreg  # yalnizca Windows'ta mevcut

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY_PATH) as key:
                value, _ = winreg.QueryValueEx(key, app_id)
                return bool(value)
        except FileNotFoundError:
            return False

    def enable_autostart(
        self, app_id: str, launch_command: list[str], display_name: str = ""
    ) -> None:
        import winreg

        command = " ".join(f'"{part}"' for part in launch_command)
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            _RUN_KEY_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, app_id, 0, winreg.REG_SZ, command)

    def disable_autostart(self, app_id: str) -> None:
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                _RUN_KEY_PATH,
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.DeleteValue(key, app_id)
        except FileNotFoundError:
            pass

    # ---- dosya/klasor acma ------------------------------------------------

    def open_path(self, path: Path) -> None:
        path = Path(path)
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists() and path.suffix:
                    path.touch()
            os.startfile(str(path))  # type: ignore[attr-defined]
        except Exception:
            try:
                webbrowser.open(path.as_uri())
            except Exception:
                pass

    # ---- tema tespiti -------------------------------------------------------

    def detect_system_theme(self) -> str:
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _THEME_KEY_PATH) as key:
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return "light" if value else "dark"
        except Exception:
            return "light"

    # ---- ana dongu ---------------------------------------------------------

    def run_app(self, icon, root) -> None:
        """pystray'i ayri bir thread'de ("detached") calistirip, tkinter'in
        kendi ana dongusunu (varsa) bu thread'de calistirir -- widget'lar
        yalnizca kendi ana thread'inden olusturulabildigi/degistirilebildigi
        icin bu gerekli. `root` yoksa (tkinter kullanilamiyorsa) sadece
        pystray'in kendi dongusu calisir.

        Runs pystray in a separate ("detached") thread and runs tkinter's
        own main loop (if present) in this thread -- necessary because
        widgets can only be created/modified from their own main thread.
        If there's no `root` (tkinter unavailable), only pystray's own
        loop runs."""
        if root is not None:
            icon.run_detached()
            root.mainloop()
        else:
            icon.run()
