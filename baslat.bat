@echo off
chcp 65001 >nul
title Diyabet Takip Sistemi
cd /d "%~dp0"

rem ============================================================
rem  Diyabet Takip Sistemi - tek tik baslatici
rem  - Python ve paketleri denetler, gerekirse kurar
rem  - MongoDB'yi denetler (localhost:27017)
rem  - Uygulamayi baslatir
rem ============================================================

set PY=
python --version >nul 2>&1 && set PY=python
if not defined PY py --version >nul 2>&1 && set PY=py
if not defined PY (
    echo [HATA] Python bulunamadi.
    echo        https://www.python.org/downloads/ adresinden kurun.
    echo        Kurulumda "Add Python to PATH" kutusunu isaretleyin.
    pause
    exit /b 1
)

%PY% -c "import pymongo, matplotlib, tkcalendar, PIL" >nul 2>&1
if errorlevel 1 (
    echo Bagimliliklar yukleniyor: pymongo, matplotlib, tkcalendar, Pillow ...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [HATA] Paketler kurulamadi. Internet baglantinizi kontrol edin.
        pause
        exit /b 1
    )
)

%PY% -c "import pymongo; pymongo.MongoClient('mongodb://127.0.0.1:27017', serverSelectionTimeoutMS=2000).admin.command('ping')" >nul 2>&1
if errorlevel 1 (
    echo [UYARI] MongoDB'ye baglanilamadi - 127.0.0.1:27017.
    echo         Kurulu degilse: "docker compose up -d"  veya
    echo         https://www.mongodb.com/try/download/community
    echo         Yine de uygulamayi baslatiyorum...
) else (
    echo MongoDB baglantisi OK.
)

echo Uygulama baslatiliyor...
%PY% main.py

if errorlevel 1 (
    echo.
    echo [HATA] Uygulama beklenmedik sekilde kapandi.
    echo        Ustteki hata mesajini kontrol edin.
    pause
)
