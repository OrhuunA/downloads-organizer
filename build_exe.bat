@echo off
REM =============================================================
REM Indirilenler Duzenleyici - Tek Dosyalik .exe Olusturma Betigi
REM =============================================================
REM Bu betik, programi Python kurulumu GEREKTIRMEYEN tek bir .exe
REM dosyasi haline getirir. Olusan .exe'yi arkadaslariniza
REM gonderebilirsiniz -- onlarin bilgisayarinda Python, pip ya da
REM komut satiri kullanmalarina HIC gerek kalmaz; sadece cift
REM tiklayip calistirirlar.
REM
REM Kullanim: Bu dosyaya (build_exe.bat) CIFT TIKLAYIN, ya da bir
REM cmd penceresinde bulundugunuz klasorde "build_exe.bat" yazip
REM Enter'a basin. Bir kac dakika surebilir.
REM
REM Sonuc: dist\IndirilenlerDuzenleyici.exe

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

py -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name IndirilenlerDuzenleyici ^
    --icon app_icon.ico ^
    --add-data "config.yaml;." ^
    tray_app.py

echo.
if exist dist\IndirilenlerDuzenleyici.exe (
    echo ============================================================
    echo  BASARILI! Dosya hazir: dist\IndirilenlerDuzenleyici.exe
    echo.
    echo  Bu TEK dosyayi (IndirilenlerDuzenleyici.exe^) baskalarina
    echo  gonderebilirsiniz. Calistirmak icin sadece cift tiklamalari
    echo  yeterli -- Python kurmalarina gerek yoktur.
    echo ============================================================
) else (
    echo HATA: .exe olusturulamadi. Yukaridaki hata mesajlarina bakin.
)
echo.
pause
