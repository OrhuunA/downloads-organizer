"""Linux'a ozel platform backend'i.
Linux-specific platform backend.

Oncesinde autostart.py / tray_app.py icinde dagitik halde bulunan Linux
koduyla BIREBIR AYNIDIR -- yalnizca bu pakete tasindi.

Identical to the Linux code that used to be scattered across
autostart.py / tray_app.py -- only moved into this package.
"""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path


class LinuxBackend:
    # ---- autostart ------------------------------------------------------

    def _desktop_path(self, app_id: str) -> Path:
        return Path.home() / ".config" / "autostart" / f"{app_id.lower()}.desktop"

    def is_autostart_enabled(self, app_id: str) -> bool:
        return self._desktop_path(app_id).exists()

    def enable_autostart(
        self, app_id: str, launch_command: list[str], display_name: str = ""
    ) -> None:
        path = self._desktop_path(app_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        exec_line = " ".join(f'"{part}"' for part in launch_command)
        name = display_name or app_id
        content = f"""[Desktop Entry]
Type=Application
Name={name}
Exec={exec_line}
X-GNOME-Autostart-enabled=true
"""
        path.write_text(content, encoding="utf-8")

    def disable_autostart(self, app_id: str) -> None:
        path = self._desktop_path(app_id)
        if path.exists():
            path.unlink()

    # ---- dosya/klasor acma ------------------------------------------------

    def open_path(self, path: Path) -> None:
        path = Path(path)
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists() and path.suffix:
                    path.touch()
            subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            try:
                webbrowser.open(path.as_uri())
            except Exception:
                pass

    # ---- tema tespiti -------------------------------------------------------

    def detect_system_theme(self) -> str:
        # Linux masaustu ortamlari (GNOME/KDE/...) arasinda standart bir
        # tema-tespit API'si yok; simdilik guvenli varsayilan "light".
        # There's no standard theme-detection API across Linux desktop
        # environments (GNOME/KDE/...); default safely to "light" for now.
        return "light"

    # ---- ana dongu ---------------------------------------------------------

    def run_app(self, icon, root) -> None:
        """Windows ile ayni strateji: pystray ayri thread'de, tkinter ana
        dongusu (varsa) bu thread'de.
        Same strategy as Windows: pystray in a separate thread, tkinter's
        main loop (if present) in this thread."""
        if root is not None:
            icon.run_detached()
            root.mainloop()
        else:
            icon.run()
