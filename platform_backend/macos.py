"""macOS'a ozel platform backend'i.
macOS-specific platform backend.

Autostart ve tema tespiti mantigi, oncesinde autostart.py / theme.py
icinde zaten var olan macOS koduyla BIREBIR AYNIDIR (yalnizca tasindi).
`run_app()` ise YENI kod -- asagidaki uyariya bakin.

The autostart and theme-detection logic here is IDENTICAL to the macOS
code that already existed in autostart.py / theme.py (only moved).
`run_app()` is NEW code -- see the warning below.
"""

from __future__ import annotations

import subprocess
import webbrowser
from pathlib import Path


class MacOSBackend:
    # ---- autostart (LaunchAgent) ------------------------------------------

    def _plist_path(self, app_id: str) -> Path:
        return Path.home() / "Library" / "LaunchAgents" / f"com.{app_id.lower()}.plist"

    def is_autostart_enabled(self, app_id: str) -> bool:
        return self._plist_path(app_id).exists()

    def enable_autostart(
        self, app_id: str, launch_command: list[str], display_name: str = ""
    ) -> None:
        plist = self._plist_path(app_id)
        plist.parent.mkdir(parents=True, exist_ok=True)
        args_xml = "\n".join(f"    <string>{part}</string>" for part in launch_command)
        content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.{app_id.lower()}</string>
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

    def disable_autostart(self, app_id: str) -> None:
        plist = self._plist_path(app_id)
        if plist.exists():
            subprocess.run(["launchctl", "unload", str(plist)], capture_output=True)
            plist.unlink()

    # ---- dosya/klasor acma ------------------------------------------------

    def open_path(self, path: Path) -> None:
        path = Path(path)
        try:
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists() and path.suffix:
                    path.touch()
            subprocess.Popen(["open", str(path)])
        except Exception:
            try:
                webbrowser.open(path.as_uri())
            except Exception:
                pass

    # ---- tema tespiti -------------------------------------------------------

    def detect_system_theme(self) -> str:
        try:
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if result.returncode == 0 and "dark" in result.stdout.strip().lower():
                return "dark"
            return "light"
        except Exception:
            return "light"

    # ---- ana dongu ---------------------------------------------------------

    def run_app(self, icon, root) -> None:
        """UYARI -- gercek Mac donaniminda DOGRULANMADI:

        pystray'in Cocoa/NSStatusItem arka ucu, tepsi simgesinin ANA
        THREAD'de calismasini gerektirir. tkinter'in Aqua arka ucu da
        genelde ana thread'i tercih eder -- ikisi ayni anda ana thread'i
        isteyemeyecegi icin, macOS'ta Windows/Linux'takinin TERSİ bir
        strateji uyguluyoruz: `icon.run()`'i burada, ana thread'de
        blocking olarak calistiriyoruz; tkinter'i ise SUREKLI ACIK bir
        kok pencere olarak degil, Ayarlar penceresi her acildiginda
        `tray_app.py` icinde AYRI bir arka plan thread'inde, kisa omurlu
        kendi `tk.Tk()` kokuyle olusturuyoruz (bkz.
        TrayApplication._show_settings_window_macos_on_demand).

        Bu yuzden buraya gelen `root` parametresi macOS'ta HER ZAMAN
        None'dir ve kullanilmaz -- tray_app.py, Darwin'de persistent bir
        root olusturmuyor.

        Bu strateji gercek bir Mac'te test edilmeden %100 dogru kabul
        EDILMEMELIDIR. Eger tepsi simgesi gorunmuyor ya da Ayarlar
        penceresi kararsiz davranirsa (donma/cizim hatasi), alternatif
        olarak macOS'a ozel `rumps` kutuphanesine gecis
        degerlendirilebilir.

        WARNING -- NOT VERIFIED on real Mac hardware:

        pystray's Cocoa/NSStatusItem backend requires the tray icon to
        run on the MAIN THREAD. tkinter's Aqua backend also generally
        prefers the main thread -- since both can't claim the main
        thread at once, we use the OPPOSITE strategy from Windows/Linux
        on macOS: `icon.run()` runs here, blocking, on the main thread;
        tkinter is not held open as a persistent root window, but is
        instead created on-demand -- each time the Settings window is
        opened, `tray_app.py` spins up a SEPARATE background thread with
        its own short-lived `tk.Tk()` root (see
        TrayApplication._show_settings_window_macos_on_demand).

        Because of this, the `root` parameter here is ALWAYS None on
        macOS and is unused -- tray_app.py does not create a persistent
        root on Darwin.

        This strategy should NOT be assumed correct until tested on real
        Mac hardware. If the tray icon doesn't appear, or the Settings
        window behaves unreliably (freezing/rendering glitches), a
        fallback is to evaluate switching to the macOS-specific `rumps`
        library instead of pystray."""
        icon.run()
