@echo off
chcp 65001 >nul
title Demo Veri Uretici
cd /d "%~dp0"

rem ============================================================
rem  Demo verisini silip yeniden uretir (SADECE diyabet_takip DB)
rem  4 hasta, ~90 gun olcum/log/uyari/skor verisi
rem ============================================================

set PY=
python --version >nul 2>&1 && set PY=python
if not defined PY py --version >nul 2>&1 && set PY=py
if not defined PY (
    echo [HATA] Python bulunamadi.
    pause
    exit /b 1
)

%PY% -X utf8 scripts\generate_demo_data.py --reset --days 90
pause
