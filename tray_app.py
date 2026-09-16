"""
Indirilenler Klasoru Otomatik Duzenleyici - Sistem Tepsisi Uygulamasi
=======================================================================

Calistirmak icin:
    python tray_app.py

Program sistem tepsisinde (saat yaninda) kucuk bir simge olarak calisir.
Simgeye sag tiklayarak (Windows/Linux) veya tiklayarak (macOS) menuyu
acabilirsiniz:

  - Durum: Calisiyor / Duraklatildi
  - Duraklat / Devam Et
  - Ayarlar...                  -> kurallari YAML dosyasini elle acmadan,
                                    kucuk bir pencerede gorsel olarak
                                    ekleyip/duzenleyip/silebileceginiz ekran
  - Kurallari Yeniden Yukle     -> config.yaml'i tekrar okur (programi kapatmadan)
  - Simdi Duzenle (Mevcut Dosyalar) -> Downloads'ta HALIHAZIRDA duran
                                       dosyalari da bir kerelik tarayip tasir
  - Indirilenler Klasorunu Ac
  - Kurallari Duzenle (config.yaml) -> ileri duzey: dosyayi varsayilan
                                        metin editorunde acar
  - Loglari Ac                  -> log dosyasini acar
  - Bilgisayar Acilisinda Baslat -> isaretliyse program her acilista
                                     otomatik calisir (Windows: kayit defteri,
                                     macOS: LaunchAgent, Linux: autostart .desktop)
  - Cikis
"""

from __future__ import annotations

import os
import platform
import sys
import threading
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from organizer import OrganizerService, DEFAULT_CONFIG_PATH, ensure_config_exists
from i18n import t
from platform_backend import backend
import autostart

try:
    import tkinter as tk
except ImportError:
    tk = None  # Bazi minimal Python kurulumlarinda tkinter olmayabilir;
    # bu durumda "Ayarlar" menusu, YAML dosyasini metin editorunde acan
    # eski davranisa geri doner (bkz. _open_settings).


def open_path(path: Path):
    """Isletim sistemine gore bir dosyayi/klasoru varsayilan uygulamada acar.
    (Platforma ozel acma mantigi artik platform_backend paketinde.)"""
    backend.open_path(Path(path))


def make_icon_image(paused: bool = False) -> Image.Image:
    """Harici bir dosyaya ihtiyac duymadan, PIL ile basit bir tepsi
    simgesi ciziyoruz: bir klasor sekli + durum rengi."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    body_color = (120, 120, 120, 255) if paused else (245, 166, 35, 255)  # gri / turuncu
    tab_color = (90, 90, 90, 255) if paused else (214, 140, 20, 255)

    # Klasor "kulagi"
    draw.rectangle([8, 14, 26, 22], fill=tab_color)
    # Klasor govdesi
    draw.rounded_rectangle([8, 20, 56, 50], radius=6, fill=body_color)

    # Durum noktasi (sag alt): yesil = calisiyor, kirmizi = duraklatildi
    dot_color = (200, 60, 60, 255) if paused else (70, 180, 90, 255)
    draw.ellipse([40, 38, 58, 56], fill=dot_color, outline=(255, 255, 255, 255), width=2)

    return img


class TrayApplication:
    def __init__(self):
        self.service = OrganizerService(DEFAULT_CONFIG_PATH)
        self.icon: pystray.Icon | None = None
        self.root = None  # tkinter kok penceresi (run() icinde olusturulur;
        # macOS'ta persistent bir root OLUSTURULMAZ, bkz. run())
        self._settings_window = None
        self._settings_thread = None  # macOS'ta Ayarlar penceresi icin
        # kullanilan, istek uzerine olusturulan kisa omurlu thread

    # ---- menu callbacks -------------------------------------------------

    def _toggle_pause(self, icon, item):
        self.service.toggle_pause()
        self._refresh_icon()

    def _open_settings(self, icon, item):
        if tk is None:
            # tkinter yoksa eski davranisa (YAML dosyasini editorde acmak) don
            self._open_rules(icon, item)
            return
        if self.root is not None:
            # Windows/Linux: persistent (gizli) bir root var. pystray'in
            # olay dongusu (thread) ile tkinter'in kendi ana thread'i ayri
            # oldugu icin, pencereyi tkinter'in kendi thread'inde acmak
            # icin root.after(...) ile "havale" ediyoruz.
            self.root.after(0, self._show_settings_window)
        else:
            # macOS: persistent bir root yok (bkz. run() / platform_backend
            # /macos.py::run_app'teki aciklama) -- Ayarlar penceresini
            # istek uzerine, ayri bir thread'de aciyoruz.
            self._show_settings_window_macos_on_demand()

    def _show_settings_window_macos_on_demand(self):
        """macOS icin: pystray ana thread'i kullandigindan, sureki acik
        bir tkinter kok penceresi tutamayiz. Bunun yerine, Ayarlar
        penceresi her istendiginde KISA OMURLU, kendi `tk.Tk()` koku olan
        ayri bir arka plan thread'i olusturuyoruz; pencere kapaninca o
        thread de sona eriyor.

        For macOS: since pystray owns the main thread, we can't keep a
        persistent tkinter root open. Instead, each time Settings is
        requested we spin up a SHORT-LIVED background thread with its
        own `tk.Tk()` root; when the window closes, that thread ends."""
        if self._settings_thread is not None and self._settings_thread.is_alive():
            # Zaten acik/aciliyor -- ikinci bir tane baslatma.
            return

        def _run():
            try:
                local_root = tk.Tk()
                local_root.withdraw()

                from settings_gui import SettingsWindow

                config_path = (
                    self.service.config_path if self.service.config else DEFAULT_CONFIG_PATH
                )
                win = SettingsWindow(
                    local_root, config_path, self._lang(), on_saved=self._on_settings_saved
                )
                win.deiconify()
                win.lift()
                win.focus_force()
                win.attributes("-topmost", True)
                win.after(300, lambda: win.attributes("-topmost", False))
                # Pencere kapatildiginda (X'e basildiginda) bu thread'in
                # kendi mainloop'unu sonlandir, boylece thread dogal olarak
                # biter.
                win.bind(
                    "<Destroy>",
                    lambda e: local_root.quit() if e.widget is win else None,
                )
                local_root.mainloop()
                local_root.destroy()
            except Exception:
                import traceback

                self._log_settings_error(traceback.format_exc())

        self._settings_thread = threading.Thread(target=_run, daemon=True)
        self._settings_thread.start()

    def _show_settings_window(self):
        try:
            if self._settings_window is not None:
                try:
                    if self._settings_window.winfo_exists():
                        self._settings_window.deiconify()
                        self._settings_window.lift()
                        self._settings_window.focus_force()
                        return
                except Exception:
                    pass

            from settings_gui import SettingsWindow

            config_path = (
                self.service.config_path if self.service.config else DEFAULT_CONFIG_PATH
            )
            self._settings_window = SettingsWindow(
                self.root, config_path, self._lang(), on_saved=self._on_settings_saved
            )
            # Pencerenin, ozellikle --windowed .exe olarak paketlenmis
            # halde, diger pencerelerin ARKASINDA sessizce acilmasini
            # onlemek icin one getiriyoruz.
            win = self._settings_window
            win.deiconify()
            win.lift()
            win.focus_force()
            win.attributes("-topmost", True)
            win.after(300, lambda: win.attributes("-topmost", False))
        except Exception:
            # --windowed olarak paketlenmis bir .exe'de konsol/stderr
            # olmadigi icin normalde bir hata OLDUGUNU BILE goremezsiniz.
            # Bu yuzden hatayi hem log dosyasina yaziyoruz, hem de
            # (mumkunse) kucuk bir uyari penceresi gosteriyoruz.
            import traceback

            err_text = traceback.format_exc()
            self._log_settings_error(err_text)
            try:
                from tkinter import messagebox

                messagebox.showerror(
                    "Hata / Error",
                    "Ayarlar penceresi açılamadı. Ayrıntılar log dosyasına yazıldı.\n"
                    "Could not open Settings. Details were written to the log file.\n\n"
                    f"{err_text.splitlines()[-1] if err_text else ''}",
                )
            except Exception:
                pass

    def _log_settings_error(self, err_text: str):
        logger = self.service.logger
        message = "Ayarlar penceresi acilirken hata olustu:\n" + err_text
        if logger:
            logger.error(message)
            return
        # Logger henuz yoksa (servis baslamadan once), en azindan
        # bilinen log dosyasina elle yazmayi dene.
        try:
            log_path = (
                self.service.config.log_file
                if self.service.config
                else Path.home() / "Downloads" / ".organizer_log.txt"
            )
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception:
            pass

    def _on_settings_saved(self):
        self.service.reload()
        self._refresh_icon()

    def _open_rules(self, icon, item):
        open_path(self.service.config_path if self.service.config else DEFAULT_CONFIG_PATH)

    def _open_log(self, icon, item):
        log_path = self.service.config.log_file if self.service.config else Path.home() / "Downloads" / ".organizer_log.txt"
        open_path(log_path)

    def _open_watch_folder(self, icon, item):
        folder = self.service.config.watch_folder if self.service.config else Path.home() / "Downloads"
        open_path(folder)

    def _reload_rules(self, icon, item):
        self.service.reload()
        self._refresh_icon()

    def _organize_now(self, icon, item):
        lang = self._lang()
        logger = self.service.logger

        def _run():
            if logger:
                logger.info(t(lang, "scan_started"))
            count = self.service.organize_existing_now()
            if logger:
                logger.info(t(lang, "scan_done", count=count))

        threading.Thread(target=_run, daemon=True).start()

    def _toggle_autostart(self, icon, item):
        lang = self._lang()
        logger = self.service.logger
        try:
            enabled = autostart.toggle()
            if logger:
                logger.info(t(lang, "autostart_enabled" if enabled else "autostart_disabled"))
        except Exception:
            if logger:
                logger.info(t(lang, "autostart_failed"))
        self._refresh_icon()

    def _quit(self, icon, item):
        self.service.stop()
        icon.stop()
        if self.root is not None:
            self.root.after(0, self.root.quit)

    # ---- dil / durum -------------------------------------------------------

    def _lang(self) -> str:
        return self.service.config.language if self.service.config else "tr"

    def _app_name(self) -> str:
        return t(self._lang(), "app_name")

    def _status_text(self, item=None):
        key = "menu_status_paused" if self.service.is_paused() else "menu_status_running"
        return t(self._lang(), key)

    def _pause_text(self, item=None):
        key = "menu_resume" if self.service.is_paused() else "menu_pause"
        return t(self._lang(), key)

    def _refresh_icon(self):
        if self.icon is not None:
            self.icon.icon = make_icon_image(self.service.is_paused())
            title_key = "tray_title_paused" if self.service.is_paused() else "tray_title_running"
            self.icon.title = t(self._lang(), title_key, app=self._app_name())
            self.icon.update_menu()

    def build_menu(self):
        lang = self._lang()
        return pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(self._pause_text, self._toggle_pause),
            pystray.MenuItem(t(lang, "menu_settings"), self._open_settings),
            pystray.MenuItem(t(lang, "menu_reload"), self._reload_rules),
            pystray.MenuItem(t(lang, "menu_organize_now"), self._organize_now),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t(lang, "menu_open_folder"), self._open_watch_folder),
            pystray.MenuItem(t(lang, "menu_open_rules"), self._open_rules),
            pystray.MenuItem(t(lang, "menu_open_log"), self._open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                t(lang, "menu_autostart"),
                self._toggle_autostart,
                checked=lambda item: autostart.is_enabled(),
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(t(lang, "menu_quit"), self._quit),
        )

    def run(self):
        self.service.start()
        lang = self._lang()

        self.icon = pystray.Icon(
            "downloads_organizer",
            icon=make_icon_image(False),
            title=t(lang, "tray_title_running", app=self._app_name()),
            menu=self.build_menu(),
        )

        # macOS'ta pystray'in Cocoa/NSStatusItem arka ucu tepsi simgesinin
        # ANA THREAD'de calismasini gerektiriyor; tkinter'in Aqua arka ucu
        # da ayni thread'i istiyor. Bu yuzden Windows/Linux'ta persistent
        # (surekli acik, gizli) bir tkinter koku tutarken, macOS'ta HIC
        # persistent root olusturmuyoruz -- Ayarlar penceresi istek
        # uzerine ayri bir thread'de aciliyor (bkz.
        # _show_settings_window_macos_on_demand). Ayrinti icin
        # platform_backend/macos.py::run_app'teki uyariya bakin.
        #
        # On macOS, pystray's Cocoa/NSStatusItem backend requires the
        # tray icon to run on the MAIN thread; tkinter's Aqua backend
        # wants the same thread. So while Windows/Linux keep a
        # persistent (hidden) tkinter root, macOS creates NO persistent
        # root at all -- the Settings window is opened on-demand in a
        # separate thread instead (see
        # _show_settings_window_macos_on_demand). See the warning in
        # platform_backend/macos.py::run_app for details.
        use_persistent_root = platform.system() != "Darwin"

        tk_ready = False
        if tk is not None:
            if use_persistent_root:
                try:
                    # "Ayarlar" penceresini acabilmek icin, tepsi simgesini
                    # AYRI bir thread'de ("detached") calistirip, tkinter'in
                    # kendi ana dongusunu (mainloop) bu (ana) thread'de
                    # calistiriyoruz -- tkinter widget'lari yalnizca kendi
                    # ana thread'inden olusturulabildigi/degistirilebildigi
                    # icin bu gerekli.
                    self.root = tk.Tk()
                    self.root.withdraw()
                    tk_ready = True
                except Exception:
                    # tkinter modulu var ama Tcl/Tk kurulumu bozuk/eksik
                    # olabilir (ozellikle bazi minimal Python dagitimlarinda,
                    # ya da .exe paketlemesinde). Bu durumda "Ayarlar" yerine
                    # eski "config.yaml'i editorde ac" davranisina donuyoruz.
                    self.root = None
            else:
                # macOS: root'u kasten olusturmuyoruz (yukaridaki notu
                # oku); yine de tkinter kullanilabilir oldugu icin
                # "Ayarlar" menusu on-demand yol ile calisacak.
                tk_ready = True

        if not tk_ready and self.service.logger:
            self.service.logger.info(t(lang, "tkinter_unavailable"))

        backend.run_app(self.icon, self.root)


def main():
    # .exe olarak paketlenmis halde, config.yaml yoksa pakete gomulu
    # varsayilan kopyayi .exe'nin yanina cikartir (ilk calistirma).
    ensure_config_exists(DEFAULT_CONFIG_PATH)
    if not DEFAULT_CONFIG_PATH.exists():
        print(t("tr", "config_not_found", path=DEFAULT_CONFIG_PATH))
        sys.exit(1)
    app = TrayApplication()
    app.run()
    # "Cikis"tan sonra bazi arka plan thread'leri (isletim sistemine gore)
    # hemen sonlanmayabilir; surecin gercekten kapanmasini garanti altina
    # almak icin acikca sonlandiriyoruz.
    os._exit(0)


if __name__ == "__main__":
    main()
