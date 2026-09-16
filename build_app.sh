#!/usr/bin/env bash
# =============================================================
# Indirilenler Duzenleyici - macOS .app Olusturma Betigi
# Downloads Organizer - macOS .app build script
# =============================================================
# Windows tarafindaki build_exe.bat'e paralel: programi Python kurulumu
# GEREKTIRMEYEN bir "İndirilenler Düzenleyici.app" haline getirir.
# Parallels build_exe.bat on the Windows side: turns the app into an
# "İndirilenler Düzenleyici.app" bundle that doesn't require a Python
# install to run.
#
# NOT: build_exe.bat'teki gibi bilerek "--onedir" + "--noupx"
# kullaniyoruz (tek-dosya modunun kendini gizlice bir gecici klasore
# acmasi, antivirus/Gatekeeper tarafindan supheli bulunabiliyor).
# NOTE: like build_exe.bat, we deliberately use "--onedir" + "--noupx"
# (a one-file build silently self-extracting to a temp folder can look
# suspicious to antivirus/Gatekeeper).
#
# Kullanim / Usage:
#   chmod +x build_app.sh   (bir kere / once)
#   ./build_app.sh
#
# Sonuc / Result:
#   dist/IndirilenlerDuzenleyici.app
#   dist/IndirilenlerDuzenleyici-macOS.zip   (paylasima hazir / ready to share)
#
# ONEMLI: Bu betik SADECE macOS'ta calisir -- PyInstaller cross-compile
# yapamaz, yani Windows/Linux'tan bir .app URETILEMEZ. Apple Silicon'da
# derlerseniz sonuc yalnizca Apple Silicon Mac'lerde calisir (universal2
# hedeflenmiyor -- tum bagimliliklarin universal2 tekerlek sunmasi
# gerekirdi, bu asamada pratik degil).
# IMPORTANT: This script ONLY runs on macOS -- PyInstaller can't
# cross-compile, so a .app can't be produced from Windows/Linux. If you
# build on Apple Silicon, the result will only run on Apple Silicon
# Macs (we don't target universal2 -- that would require every
# dependency to ship a universal2 wheel, impractical at this stage).

set -euo pipefail

APP_NAME="IndirilenlerDuzenleyici"
DISPLAY_NAME="İndirilenler Düzenleyici"
BUNDLE_ID="com.orhunaslan.indirilenlerduzenleyici"
VERSION="1.0.0"

echo "============================================================"
echo " ${DISPLAY_NAME} - .app olusturuluyor... / building..."
echo "============================================================"
echo

if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "HATA: Bu betik SADECE macOS'ta calisir."
    echo "ERROR: this script only runs on macOS."
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "HATA: python3 bulunamadi. Once python.org'dan ya da Homebrew ile"
    echo "('brew install python-tk') Python kurun."
    echo "ERROR: python3 not found. Install Python first, from python.org"
    echo "or via Homebrew ('brew install python-tk')."
    exit 1
fi

echo "Bagimliliklar kuruluyor / Installing dependencies..."
python3 -m pip install --upgrade pip pyinstaller >/dev/null
python3 -m pip install -r requirements.txt >/dev/null

echo
echo "Simge donusturuluyor / Converting icon (app_icon.ico -> .icns)..."
python3 make_icns.py

# Onceki derlemeden kalma build/ ve spec dosyasini temizle ki eski
# ayarlar karismasin.
# Clean up any leftover build/ dir and spec file from a previous build
# so stale settings don't linger.
rm -rf build/pyinstaller "${APP_NAME}.spec"

echo
echo "PyInstaller calistiriliyor / Running PyInstaller..."
# NOT: macOS'ta --add-data ayraci ';' degil ':' -- Windows'takinin tersi.
# NOTE: on macOS the --add-data separator is ':' not ';' -- the
# opposite of the Windows build.
python3 -m PyInstaller \
    --onedir \
    --noupx \
    --windowed \
    --name "${APP_NAME}" \
    --icon app_icon.icns \
    --add-data "config.yaml:." \
    --osx-bundle-identifier "${BUNDLE_ID}" \
    tray_app.py

APP_BUNDLE="dist/${APP_NAME}.app"

if [[ ! -d "${APP_BUNDLE}" ]]; then
    echo "HATA: .app olusturulamadi. Yukaridaki hata mesajlarina bakin."
    echo "ERROR: .app was not created. See the errors above."
    exit 1
fi

echo
echo "Info.plist ayarlaniyor (menu cubugu uygulamasi, Dock'ta gorunmesin)..."
echo "Configuring Info.plist (menu-bar app, hidden from the Dock)..."
python3 - "${APP_BUNDLE}" "${DISPLAY_NAME}" "${BUNDLE_ID}" "${VERSION}" <<'PYEOF'
import plistlib
import sys
from pathlib import Path

app_bundle, display_name, bundle_id, version = sys.argv[1:5]
plist_path = Path(app_bundle) / "Contents" / "Info.plist"

with open(plist_path, "rb") as f:
    data = plistlib.load(f)

# LSUIElement = True -> Dock'ta simge/uygulama gostermez, sadece menu
# cubugunda calisir (bu tam olarak istedigimiz "tepsi uygulamasi" davranisi).
# LSUIElement = True -> hides the Dock icon, runs as a menu-bar-only
# app (exactly the "tray app" behavior we want).
data["LSUIElement"] = True
data["CFBundleName"] = display_name
data["CFBundleDisplayName"] = display_name
data["CFBundleIdentifier"] = bundle_id
data["CFBundleShortVersionString"] = version
data["CFBundleVersion"] = version

with open(plist_path, "wb") as f:
    plistlib.dump(data, f)

print(f"  {plist_path} guncellendi / updated.")
PYEOF

echo
echo "Ad-hoc imzalaniyor / Ad-hoc code signing..."
# Ucretli bir Apple Developer sertifikamiz olmadigi icin "ad-hoc"
# (kimliksiz) imzaliyoruz -- bu Gatekeeper uyarisini ORTADAN KALDIRMAZ,
# ama uygulamanin makinede DEGISTIRILMEDEN calismasini saglar.
# We don't have a paid Apple Developer certificate, so we sign "ad-hoc"
# (identity-less) -- this does NOT remove the Gatekeeper warning, but
# lets the app run un-tampered-with on the machine.
codesign --force --deep --sign - "${APP_BUNDLE}"

echo
echo "Zip'leniyor / Zipping..."
ZIP_PATH="dist/${APP_NAME}-macOS.zip"
rm -f "${ZIP_PATH}"
# Adi ditto kullaniyoruz: normal 'zip' aksine kaynak-catallari (resource
# forks) ve genisletilmis oznitelikleri (xattr) dogru sekilde korur --
# .app paketleri icin Apple'in kendi onerdigi yontem budur.
# We use ditto: unlike plain 'zip', it correctly preserves resource
# forks and extended attributes -- this is Apple's own recommended way
# to zip a .app bundle.
ditto -c -k --sequesterRsrc --keepParent "${APP_BUNDLE}" "${ZIP_PATH}"

echo
echo "============================================================"
echo " BASARILI! / SUCCESS!"
echo "   ${APP_BUNDLE}"
echo "   ${ZIP_PATH}"
echo
echo " Not: kod imzalama sertifikamiz olmadigi icin, .app'i ilk"
echo " acisinizda (ya da baskasina gonderdiginizde) Gatekeeper bir"
echo " uyari gosterecek. README'deki 'macOS Gatekeeper uyarisi'"
echo " bolumune bakin (sag tik -> Ac, ya da 'xattr -dr"
echo " com.apple.quarantine' komutu)."
echo
echo " Note: since we don't have a code-signing certificate,"
echo " Gatekeeper will show a warning the first time the .app is"
echo " opened (or when someone else downloads it). See the 'macOS"
echo " Gatekeeper warning' section in the README (right-click -> Open,"
echo " or the 'xattr -dr com.apple.quarantine' command)."
echo "============================================================"
