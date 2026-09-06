"""
Indirilenler Klasoru Otomatik Duzenleyici - Cekirdek Mantik
=============================================================

Bu dosya, kural okuma, dosya eslestirme ve tasima islemlerini icerir.
Sistem tepsisi (tray_app.py) bu modulu kullanir, ama bu dosya tek
basina da (tepsi/GUI olmadan) calistirilabilir ve test edilebilir --
bu yuzden watchdog/pystray importlari fonksiyon ici degil, ama GUI'ye
bagimli hicbir sey burada yok.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from i18n import t, normalize_lang

def _app_base_dir() -> Path:
    """Programin 'kendi klasoru'. Kaynaktan (python tray_app.py ile)
    calisirken bu dosyalarin bulundugu klasordur. PyInstaller ile TEK
    DOSYA (.exe) olarak paketlenmis calistirilabilir bir dosyadan
    calisirken ise __file__ her seferinde GECICI bir cikartma klasorune
    (sys._MEIPASS) isaret eder ve sistem her acilista silinir -- bu
    yuzden orada durum/ayar dosyasi TUTULAMAZ. Boyle bir durumda .exe
    dosyasinin YANINDAKI kalici klasoru kullaniyoruz."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _bundled_default_config_path() -> Optional[Path]:
    """.exe icine PyInstaller'in --add-data secenegiyle gomulmus olan
    ORIJINAL/varsayilan config.yaml'in (salt-okunur) gecici cikartma
    yolu. Sadece paketlenmis modda ve MEIPASS varsa anlamlidir."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidate = Path(meipass) / "config.yaml"
        if candidate.exists():
            return candidate
    return None


def ensure_config_exists(path: Path) -> None:
    """Belirtilen konumda config.yaml yoksa, pakete gomulu varsayilan
    kopyayi oraya kopyalar. Bu, .exe'yi arkadaslarina gonderen birinin
    hicbir kurulum yapmadan, sadece cift tiklayarak calistirabilmesini
    saglar -- program ilk acilista kendi config.yaml'ini yaninda
    olusturur."""
    if path.exists():
        return
    bundled = _bundled_default_config_path()
    if bundled is not None and bundled.resolve() != path.resolve():
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(str(bundled), str(path))


DEFAULT_CONFIG_PATH = _app_base_dir() / "config.yaml"


# ---------------------------------------------------------------------------
# Config yukleme
# ---------------------------------------------------------------------------

def expand(path_str: Optional[str]) -> Optional[Path]:
    if not path_str:
        return None
    return Path(os.path.expanduser(os.path.expandvars(str(path_str))))


@dataclass
class Rule:
    name: str
    extensions: list = field(default_factory=list)
    name_contains: list = field(default_factory=list)
    regex: Optional[str] = None
    older_than_days: Optional[int] = None
    destination: str = ""

    def matches(self, file_path: Path) -> bool:
        """Bir dosyanin bu kurala uyup uymadigini kontrol eder.
        Tanimli tum kriterlerin (VE mantigi) dogru olmasi gerekir."""
        checked_any = False

        if self.extensions:
            checked_any = True
            suffixes = "".join(file_path.suffixes).lower()
            name_lower = file_path.name.lower()
            ext_lower = [e.lower() for e in self.extensions]
            if not any(name_lower.endswith(e) for e in ext_lower):
                return False

        if self.name_contains:
            checked_any = True
            name_lower = file_path.name.lower()
            if not any(kw.lower() in name_lower for kw in self.name_contains):
                return False

        if self.regex:
            checked_any = True
            if not re.search(self.regex, file_path.name):
                return False

        if self.older_than_days is not None:
            checked_any = True
            try:
                mtime = file_path.stat().st_mtime
            except FileNotFoundError:
                return False
            age_days = (time.time() - mtime) / 86400.0
            if age_days < self.older_than_days:
                return False

        # Hicbir kriter tanimlanmamis bos bir kural her seye uyar sayilmaz.
        return checked_any


@dataclass
class Config:
    watch_folder: Path
    ignore_extensions: list
    stability_check_seconds: float
    poll_interval_seconds: float
    rules: list
    default_destination: Optional[Path]
    log_file: Path
    raw_path: Path
    language: str = "tr"
    organize_folders: bool = False
    folders_destination: Optional[Path] = None
    protected_folder_names: frozenset = field(default_factory=frozenset)

    @classmethod
    def load(cls, path: Path = DEFAULT_CONFIG_PATH) -> "Config":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        language = normalize_lang(data.get("language", "tr"))
        watch_folder = expand(data.get("watch_folder", "~/Downloads"))
        ignore_extensions = [e.lower() for e in data.get("ignore_extensions", [])]
        stability_check_seconds = float(data.get("stability_check_seconds", 2))
        poll_interval_seconds = float(data.get("poll_interval_seconds", 1))

        rules = []
        for r in data.get("rules", []) or []:
            match = r.get("match", {}) or {}
            rules.append(
                Rule(
                    name=r.get("name", "İsimsiz Kural"),
                    extensions=match.get("extensions", []) or [],
                    name_contains=match.get("name_contains", []) or [],
                    regex=match.get("regex"),
                    older_than_days=match.get("older_than_days"),
                    destination=r.get("destination", ""),
                )
            )

        default_destination = expand(data.get("default_destination"))
        log_file = expand(data.get("log_file", "~/Downloads/.organizer_log.txt"))

        organize_folders = bool(data.get("organize_folders", False))
        folders_destination_raw = data.get("folders_destination")
        folders_destination = expand(folders_destination_raw)

        # Kendi olusturdugumuz kategori klasorlerinin ASLA yeniden
        # tasinmamasi icin: tum kural hedeflerinin + varsayilan hedefin +
        # klasor hedefinin, izlenen klasore gore ILK path parcasini
        # (ust duzey klasor adini) topluyoruz. Bu isimler her zaman
        # korumaya alinir -- boylece "Belgeler" klasorunu "Klasorler"
        # icine, sonra "Klasorler"i baska bir yere... diye sonsuz bir
        # ic ice gecme / kendi kendini yeniden duzenleme dongusu asla
        # yasanmaz.
        #
        # To make sure the app's own category folders are NEVER moved
        # again: we collect the top-level path segment (relative to the
        # watched folder) of every rule destination + the default
        # destination + the folders destination. Those names are always
        # protected -- this is what prevents an infinite
        # nested-reorganization loop.
        destination_templates = [r.destination for r in rules]
        if data.get("default_destination"):
            destination_templates.append(str(data.get("default_destination")))
        if folders_destination_raw:
            destination_templates.append(str(folders_destination_raw))
        protected_folder_names = frozenset(
            _compute_protected_top_level_names(watch_folder, destination_templates)
        )

        return cls(
            watch_folder=watch_folder,
            ignore_extensions=ignore_extensions,
            stability_check_seconds=stability_check_seconds,
            poll_interval_seconds=poll_interval_seconds,
            rules=rules,
            default_destination=default_destination,
            log_file=log_file,
            raw_path=path,
            language=language,
            organize_folders=organize_folders,
            folders_destination=folders_destination,
            protected_folder_names=protected_folder_names,
        )


def _compute_protected_top_level_names(watch_folder: Path, destination_templates: list) -> set:
    """destination_templates icindeki her yol, izlenen klasorun (watch_folder)
    altindaysa, o yolun ilk (ust duzey) parcasini kucuk harfle toplar.
    Path.resolve() kullanilmaz (semboluk baglantilarda / OneDrive gibi
    senkron klasorlerde yaniltici olabilir); sadece "~" genisletilmis
    duz metin karsilastirmasi yapilir."""
    protected = set()
    watch_str = os.path.normcase(os.path.normpath(str(watch_folder)))

    for template in destination_templates:
        if not template:
            continue
        expanded = expand(str(template))
        if expanded is None:
            continue
        expanded_str = os.path.normcase(os.path.normpath(str(expanded)))

        if expanded_str == watch_str:
            continue
        prefix = watch_str + os.sep
        if not expanded_str.startswith(prefix):
            continue

        remainder = expanded_str[len(prefix):]
        first_part = remainder.split(os.sep)[0]
        if first_part:
            protected.add(first_part.lower())

    return protected


# ---------------------------------------------------------------------------
# Yer tutucu cozumleme (tarih placeholder'lari)
# ---------------------------------------------------------------------------

MONTH_NAMES_TR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def resolve_destination(template: str, when: Optional[datetime] = None) -> Path:
    when = when or datetime.now()
    filled = (
        template
        .replace("{year}", f"{when.year:04d}")
        .replace("{month}", f"{when.month:02d}")
        .replace("{month_name}", MONTH_NAMES_TR[when.month - 1])
        .replace("{day}", f"{when.day:02d}")
    )
    return expand(filled)


# ---------------------------------------------------------------------------
# Kural motoru
# ---------------------------------------------------------------------------

def find_matching_rule(file_path: Path, rules: list) -> Optional[Rule]:
    for rule in rules:
        if rule.matches(file_path):
            return rule
    return None


def unique_destination(dest_dir: Path, filename: str) -> Path:
    """Hedefte ayni isimde dosya varsa 'isim (1).uzanti' seklinde
    çakışmayan bir yol üretir."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate

    stem = Path(filename).stem
    suffix = "".join(Path(filename).suffixes)
    # Basit .tar.gz gibi cift uzantilar icin de calisir cunku suffixes kullanildi
    counter = 1
    while True:
        candidate = dest_dir / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def is_stable(path: Path, wait_seconds: float, poll_seconds: float) -> bool:
    """Dosya boyutu belirtilen sure boyunca degismiyorsa True doner.
    Hala indiriliyor olan buyuk dosyalari yanlislikla erken tasimayi engeller."""
    try:
        last_size = path.stat().st_size
    except FileNotFoundError:
        return False

    elapsed = 0.0
    while elapsed < wait_seconds:
        time.sleep(poll_seconds)
        elapsed += poll_seconds
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size != last_size:
            last_size = size
            elapsed = 0.0  # boyut degistiyse sayaci sifirla
    return True


# ---------------------------------------------------------------------------
# Ana islem: bir dosyayi degerlendir ve gerekiyorsa tasi
# ---------------------------------------------------------------------------

def process_file(path: Path, config: Config, logger: logging.Logger) -> Optional[Path]:
    lang = config.language
    """Tek bir dosyayi kurallara gore degerlendirir, uyuyorsa tasir.
    Tasinan yeni yolu (ya da islem yapilmadiysa None) doner."""

    if not path.is_file():
        return None

    name_lower = path.name.lower()
    if any(name_lower.endswith(ext) for ext in config.ignore_extensions):
        return None

    # Programin kendi log/config dosyalarini asla tasima
    try:
        if path.resolve() == config.log_file.resolve():
            return None
    except OSError:
        pass

    if not is_stable(path, config.stability_check_seconds, config.poll_interval_seconds):
        logger.info(t(lang, "skipped_writing", name=path.name))
        return None

    if not path.exists():
        return None

    rule = find_matching_rule(path, config.rules)

    if rule is not None:
        dest_template = rule.destination
        rule_name = rule.name
    elif config.default_destination is not None:
        dest_template = str(config.default_destination)
        rule_name = t(lang, "default_rule_label")
    else:
        return None

    if not dest_template:
        return None

    dest_dir = resolve_destination(dest_template)

    # Ayni klasorse tasima
    try:
        if dest_dir.resolve() == path.parent.resolve():
            return None
    except OSError:
        pass

    target = unique_destination(dest_dir, path.name)

    try:
        shutil.move(str(path), str(target))
    except (shutil.Error, OSError) as e:
        logger.error(t(lang, "move_error", name=path.name, error=e))
        return None

    logger.info(t(lang, "moved", rule=rule_name, name=path.name, dest=target))
    return target


def process_folder(path: Path, config: Config, logger: logging.Logger) -> Optional[Path]:
    """Downloads kokunde duran bir KLASORU (dosya degil) degerlendirir.
    Sadece config.organize_folders acikken calisir. Programin kendi
    olusturdugu kategori klasorleri (protected_folder_names) ile gizli
    (nokta ile baslayan) klasorler ASLA tasinmaz -- sonsuz ic ice gecme
    riskini burada kesiyoruz."""
    lang = config.language

    if not config.organize_folders:
        return None
    if not path.is_dir():
        return None

    name_lower = path.name.lower()
    if name_lower.startswith("."):
        return None
    if name_lower in config.protected_folder_names:
        return None
    if config.folders_destination is None:
        return None

    dest_dir = config.folders_destination
    try:
        if dest_dir.resolve() == path.parent.resolve():
            return None
    except OSError:
        pass

    target = unique_destination(dest_dir, path.name)

    try:
        shutil.move(str(path), str(target))
    except (shutil.Error, OSError) as e:
        logger.error(t(lang, "move_error", name=path.name, error=e))
        return None

    logger.info(t(lang, "moved", rule=t(lang, "folder_label"), name=path.name, dest=target))
    return target


def organize_existing(config: Config, logger: logging.Logger) -> int:
    """Downloads klasorunde HALIHAZIRDA duran dosyalari (ve config.organize_folders
    aciksa klasorleri de) bir kerelik tarar ve kurallara gore tasir (yalniz
    izlenen klasorun kokundeki ogeler, alt klasorlere inilmez). Tasinan
    oge sayisini dondurur.

    Bu, programin ilk kez calistirildiginda veya "Simdi Duzenle" menu
    ogesine tiklandiginda kullanilir -- normalde watchdog sadece YENI
    gelen dosyalari/klasorleri yakalar, zaten orada duran eskileri
    kendiliginden fark etmez."""
    if not config.watch_folder.exists():
        return 0

    moved_count = 0
    try:
        entries = sorted(config.watch_folder.iterdir())
    except OSError:
        return 0

    for entry in entries:
        try:
            is_file = entry.is_file()
            is_dir = entry.is_dir()
        except OSError:
            continue

        if is_file:
            result = process_file(entry, config, logger)
        elif is_dir and config.organize_folders:
            result = process_folder(entry, config, logger)
        else:
            result = None

        if result is not None:
            moved_count += 1

    return moved_count


# ---------------------------------------------------------------------------
# Watchdog entegrasyonu
# ---------------------------------------------------------------------------

class DownloadEventHandler(FileSystemEventHandler):
    def __init__(self, config: Config, logger: logging.Logger, pause_flag: threading.Event):
        super().__init__()
        self.config = config
        self.logger = logger
        self.pause_flag = pause_flag  # set() -> duraklatilmis

    def _handle(self, path_str: str, is_directory: bool):
        if self.pause_flag.is_set():
            return
        if is_directory and not self.config.organize_folders:
            # Klasor duzenleme kapaliysa klasor olaylarini tamamen yok say.
            return
        path = Path(path_str)
        target_fn = process_folder if is_directory else process_file
        # Islemi ayri bir thread'de yap ki watchdog'un observer thread'i
        # stabilite beklemesinden dolayi kilitlenmesin.
        threading.Thread(
            target=target_fn, args=(path, self.config, self.logger), daemon=True
        ).start()

    def on_created(self, event):
        self._handle(event.src_path, event.is_directory)

    def on_moved(self, event):
        # Tarayicilar genelde "isim.crdownload" -> "isim.pdf" seklinde
        # yeniden adlandirir; bu yuzden on_moved da dinlenmeli.
        self._handle(event.dest_path, event.is_directory)


def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("downloads_organizer")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    log_file.parent.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter("%(asctime)s  %(message)s", "%Y-%m-%d %H:%M:%S"))
    logger.addHandler(sh)

    return logger


class OrganizerService:
    """Watchdog Observer'i yonetir; tray_app tarafindan baslat/durdur/
    yeniden yukle icin kullanilir."""

    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH):
        self.config_path = config_path
        self.config: Optional[Config] = None
        self.observer: Optional[Observer] = None
        self.logger: Optional[logging.Logger] = None
        self.pause_flag = threading.Event()
        self._lock = threading.Lock()

    def start(self):
        with self._lock:
            self.config = Config.load(self.config_path)
            self.logger = setup_logger(self.config.log_file)
            self.config.watch_folder.mkdir(parents=True, exist_ok=True)

            self.logger.info(
                t(
                    self.config.language,
                    "started",
                    folder=self.config.watch_folder,
                    count=len(self.config.rules),
                )
            )

            handler = DownloadEventHandler(self.config, self.logger, self.pause_flag)
            self.observer = Observer()
            self.observer.schedule(handler, str(self.config.watch_folder), recursive=False)
            self.observer.start()

    def stop(self):
        with self._lock:
            if self.observer is not None:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            if self.logger is not None:
                lang = self.config.language if self.config else "tr"
                self.logger.info(t(lang, "stopped"))

    def reload(self):
        if self.logger and self.config:
            self.logger.info(t(self.config.language, "reloading"))
        self.stop()
        self.start()

    def toggle_pause(self) -> bool:
        """Doner: True ise artik duraklatilmis durumda."""
        lang = self.config.language if self.config else "tr"
        if self.pause_flag.is_set():
            self.pause_flag.clear()
            self.logger and self.logger.info(t(lang, "resumed"))
        else:
            self.pause_flag.set()
            self.logger and self.logger.info(t(lang, "paused"))
        return self.pause_flag.is_set()

    def is_paused(self) -> bool:
        return self.pause_flag.is_set()

    def organize_existing_now(self) -> int:
        """Izlenen klasorde halihazirda duran dosyalari tek seferlik tarar.
        Cagiran taraf (tray_app) bunu genelde bir arka plan thread'inde
        cagirir, cunku cok sayida dosya varsa biraz surebilir."""
        with self._lock:
            if self.config is None or self.logger is None:
                return 0
            return organize_existing(self.config, self.logger)


if __name__ == "__main__":
    # Tray olmadan, konsoldan calistirma (test/hata ayiklama icin).
    service = OrganizerService()
    service.start()
    print(t(service.config.language, "running_hint"))
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        service.stop()
