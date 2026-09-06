@echo off
REM =============================================================
REM Indirilenler Duzenleyici - .exe Olusturma Betigi
REM =============================================================
REM Bu betik, programi Python kurulumu GEREKTIRMEYEN bir .exe
REM haline getirir. Olusan klasoru arkadaslariniza gonderebilirsiniz --
REM onlarin bilgisayarinda Python, pip ya da komut satiri
REM kullanmalarina HIC gerek kalmaz; sadece klasordeki .exe'ye
REM cift tiklayip calistirirlar.
REM
REM NOT: Bilerek "--onedir" (klasor) modu kullaniyoruz, "--onefile"
REM (tek dosya) DEGIL. Tek-dosya modu, calisirken kendini gizlice
REM bir gecici klasore acar -- bu davranis, zararli yazilimlarin
REM kullandigi "self-extracting dropper" yontemine cok benzedigi
REM icin Windows Defender / Chrome / Google Safe Browsing tarafindan
REM sik sik YANLIS ALARM olarak isaretlenir ve dosya otomatik
REM silinir/engellenir. Klasor modunda boyle bir gizli acilma
REM olmadigi icin bu yanlis alarm riski COK azalir. Ayni sebeple
REM UPX sikistirmasini da (--noupx) kapatiyoruz; UPX ile sikistirilmis
REM .exe'ler de antivirus yazilimlari tarafindan siklikla supheli
REM bulunur. Detaylar icin README'deki "Antivirus / Windows
REM Defender uyarilari" bolumune bakin.
REM
REM Kullanim: Bu dosyaya (build_exe.bat) CIFT TIKLAYIN, ya da bir
REM cmd penceresinde bulundugunuz klasorde "build_exe.bat" yazip
REM Enter'a basin. Bir kac dakika surebilir.
REM
REM Sonuc: dist\IndirilenlerDuzenleyici\IndirilenlerDuzenleyici.exe
REM        (bu .exe'yi klasorunden AYIRMAYIN -- yanindaki dosyalara
REM        ihtiyaci var; baskalarina gonderirken TUM
REM        "IndirilenlerDuzenleyici" klasorunu zip'leyip gonderin)

echo ============================================================
echo  Indirilenler Duzenleyici - .exe olusturuluyor...
echo ============================================================
echo.

py -m pip install --upgrade pyinstaller >nul 2>&1
if errorlevel 1 (
    echo HATA: pyinstaller kurulamadi. Once "py -m pip install -r requirements.txt" calistirdiginizdan emin olun.
    pause
    exit /b 1
)

REM Onceki --onefile derlemesinden kalma build/ ve spec dosyasini
REM temizleyelim ki eski ayarlar karismasin.
if exist build rmdir /s /q build
if exist IndirilenlerDuzenleyici.spec del /q IndirilenlerDuzenleyici.spec

py -m PyInstaller ^
    --onedir ^
    --noupx ^
    --windowed ^
    --name IndirilenlerDuzenleyici ^
    --icon app_icon.ico ^
    --add-data "config.yaml;." ^
    tray_app.py

echo.
if exist dist\IndirilenlerDuzenleyici\IndirilenlerDuzenleyici.exe (
    echo ============================================================
    echo  BASARILI! Klasor hazir: dist\IndirilenlerDuzenleyici\
    echo.
    echo  Programi calistirmak icin o klasorun icindeki
    echo  IndirilenlerDuzenleyici.exe'ye cift tiklamaniz yeterli --
    echo  Python kurmalarina gerek yoktur.
    echo.
    echo  BASKALARINA GONDERIRKEN: sadece .exe'yi degil, TUM
    echo  "IndirilenlerDuzenleyici" klasorunu (icindeki _internal
    echo  klasoruyle birlikte) zip'leyip gonderin -- .exe tek
    echo  basina yaninda gerekli dosyalar olmadan calismaz.
    echo ============================================================
) else (
    echo HATA: .exe olusturulamadi. Yukaridaki hata mesajlarina bakin.
)
echo.
pause
