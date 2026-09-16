"""
app_icon.ico -> app_icon.icns donusturucu (SADECE macOS'ta calisir).
Converts app_icon.ico -> app_icon.icns (macOS-ONLY, uses `iconutil`).

Bu betik build_app.sh tarafindan otomatik cagrilir; elle calistirmaniz
GENELLIKLE gerekmez. `iconutil` sadece macOS'ta bulundugu icin bu betik
baska bir isletim sisteminde CALISMAZ (ve calismamalidir) -- Windows/
Linux tarafinda .icns'e ihtiyac yoktur.

This script is called automatically by build_app.sh; you normally don't
need to run it by hand. Since `iconutil` only exists on macOS, this
script does NOT (and should not) run on any other OS -- Windows/Linux
builds don't need an .icns file.

Adimlar / Steps:
  1. Pillow ile app_icon.ico icindeki EN BUYUK cozunurluklu kareyi bulur.
     Finds the LARGEST embedded resolution inside app_icon.ico via Pillow.
  2. macOS'un istedigi standart boyut setini (16..1024 px, @1x/@2x)
     uretmek icin bu kareyi yeniden olceklendirir (kaynak kucukse
     buyutme kalite kaybina yol acabilir -- bu normal ve beklenen bir
     durumdur, .ico dosyalarinda genelde 256x256'dan buyuk kare yoktur).
     Rescales that frame to produce the standard size set macOS wants
     (16..1024 px, @1x/@2x) -- upscaling a small source can lose some
     quality, which is expected since .ico files rarely embed a frame
     larger than 256x256.
  3. `iconutil -c icns` ile bu boyut setinden tek bir .icns dosyasi
     uretir.
     Builds a single .icns file from that size set with `iconutil -c icns`.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("HATA / ERROR: Pillow bulunamadi. Once 'pip install -r requirements.txt' calistirin.")
    sys.exit(1)

PROJECT_DIR = Path(__file__).resolve().parent
SOURCE_ICO = PROJECT_DIR / "app_icon.ico"
OUTPUT_ICNS = PROJECT_DIR / "app_icon.icns"
ICONSET_DIR = PROJECT_DIR / "build" / "app_icon.iconset"

# macOS'un bir .iconset klasorunde bekledigi dosya adlari ve boyutlari.
# The filenames and sizes macOS expects inside an .iconset folder.
_ICONSET_SIZES = [
    ("icon_16x16.png", 16),
    ("icon_16x16@2x.png", 32),
    ("icon_32x32.png", 32),
    ("icon_32x32@2x.png", 64),
    ("icon_128x128.png", 128),
    ("icon_128x128@2x.png", 256),
    ("icon_256x256.png", 256),
    ("icon_256x256@2x.png", 512),
    ("icon_512x512.png", 512),
    ("icon_512x512@2x.png", 1024),
]


def _largest_ico_frame(ico_path: Path) -> Image.Image:
    """app_icon.ico icindeki en buyuk cozunurluklu kareyi RGBA olarak
    dondurur. Pillow'un ICO eklentisi, ico icinde birden fazla boyut
    gomulu oldugunda varsayilan olarak EN BUYUGUNU yukler -- ayrica
    elle secim yapmaya gerek yoktur.

    Returns the largest-resolution frame embedded in app_icon.ico, as
    RGBA. Pillow's ICO plugin loads the LARGEST embedded size by
    default when an .ico contains more than one -- no manual selection
    needed."""
    with Image.open(ico_path) as img:
        try:
            available = img.ico.sizes()  # [(w, h), ...] -- sadece bilgi amacli / informational only
            if available:
                print(f"  ico icindeki boyutlar / sizes inside ico: {sorted(available)}")
        except AttributeError:
            pass
        return img.convert("RGBA").copy()


def build_icns() -> None:
    if platform.system() != "Darwin":
        print(
            "HATA: Bu betik SADECE macOS'ta calisir ('iconutil' macOS'a "
            "ozeldir). Windows/Linux derlemeleri icin .icns'e ihtiyac yoktur.\n"
            "ERROR: This script only runs on macOS ('iconutil' is "
            "macOS-only). Windows/Linux builds don't need an .icns file."
        )
        sys.exit(1)

    if shutil.which("iconutil") is None:
        print(
            "HATA: 'iconutil' komutu bulunamadi (macOS Xcode Command Line "
            "Tools'un bir parcasidir).\n"
            "ERROR: the 'iconutil' command was not found (it ships with "
            "the macOS Xcode Command Line Tools)."
        )
        sys.exit(1)

    if not SOURCE_ICO.exists():
        print(f"HATA / ERROR: {SOURCE_ICO} bulunamadi / not found.")
        sys.exit(1)

    print(f"En buyuk kare cikariliyor / Extracting largest frame: {SOURCE_ICO}")
    base_frame = _largest_ico_frame(SOURCE_ICO)
    print(f"  -> kaynak boyut / source size: {base_frame.size}")

    if ICONSET_DIR.exists():
        shutil.rmtree(ICONSET_DIR)
    ICONSET_DIR.mkdir(parents=True, exist_ok=True)

    for filename, size in _ICONSET_SIZES:
        resized = base_frame.resize((size, size), Image.LANCZOS)
        resized.save(ICONSET_DIR / filename, format="PNG")

    print(f"iconutil calistiriliyor / Running iconutil -> {OUTPUT_ICNS}")
    subprocess.run(
        ["iconutil", "-c", "icns", str(ICONSET_DIR), "-o", str(OUTPUT_ICNS)],
        check=True,
    )
    print(f"Tamamlandi / Done: {OUTPUT_ICNS}")


if __name__ == "__main__":
    build_icns()
