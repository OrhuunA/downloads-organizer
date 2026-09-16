"""
Platform backend'lerinin uymasi gereken arayuz (Protocol).
The interface (Protocol) every platform backend must implement.

Bu bir soyut sinif DEGIL -- `typing.Protocol` kullaniyoruz ki
`windows.py`/`macos.py`/`linux.py` icindeki siniflar bundan miras almak
ZORUNDA KALMASIN (duck typing + statik tip kontrolu, calisma zamaninda
ekstra maliyet yok).

This is NOT an abstract base class -- we use `typing.Protocol` so the
classes in windows.py/macos.py/linux.py don't have to inherit from it
(duck typing + static type checking, no runtime overhead).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class PlatformBackend(Protocol):
    """Her platform backend'inin saglamasi gereken islevler.
    Functions every platform backend must provide."""

    # ---- Bilgisayar acilisinda otomatik baslatma / autostart -----------

    def is_autostart_enabled(self, app_id: str) -> bool:
        """Otomatik baslatma su an acik mi?
        Is autostart currently enabled?"""
        ...

    def enable_autostart(
        self, app_id: str, launch_command: list[str], display_name: str = ""
    ) -> None:
        """Otomatik baslatmayi acar. `launch_command`, programi yeniden
        baslatmak icin kullanilacak komut parcalaridir (autostart.py'de
        hesaplanir). `display_name`, kullaniciya gosterilecek isim
        (su an yalnizca Linux .desktop dosyasinda kullaniliyor).

        Enables autostart. `launch_command` is the command used to
        relaunch the app (computed in autostart.py). `display_name` is
        the user-visible name (currently only used in the Linux
        .desktop entry)."""
        ...

    def disable_autostart(self, app_id: str) -> None:
        """Otomatik baslatmayi kapatir. Zaten kapaliysa sessizce gecer.
        Disables autostart. Silently no-ops if already disabled."""
        ...

    # ---- Dosya/klasor acma / opening files and folders ------------------

    def open_path(self, path: Path) -> None:
        """Verilen dosya/klasoru isletim sisteminin varsayilan
        uygulamasinda acar.
        Opens the given file/folder in the OS's default application."""
        ...

    # ---- Tema tespiti / theme detection ----------------------------------

    def detect_system_theme(self) -> str:
        """Isletim sisteminin acik/koyu tema tercihini tespit eder.
        "light" ya da "dark" doner; tespit edilemezse "light".

        Detects the OS's light/dark theme preference. Returns "light"
        or "dark"; falls back to "light" when it can't be determined."""
        ...

    # ---- Ana uygulama dongusu / main application loop --------------------

    def run_app(self, icon, root) -> None:
        """Tepsi simgesinin (pystray.Icon) ve -- varsa -- tkinter kok
        penceresinin (root) olay donguisunu baslatir; bu cagri, uygulama
        kapanana kadar GERI DONMEZ (blocking). `root`, tkinter
        kullanilamiyorsa None olabilir.

        Starts the event loop for the tray icon (pystray.Icon) and --
        if present -- the tkinter root window; this call BLOCKS until
        the app quits. `root` may be None when tkinter is unavailable."""
        ...
