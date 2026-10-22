@echo off
chcp 65001 >nul
title Dogrulama (Smoke Test)
cd /d "%~dp0"

rem ============================================================
rem  Uctan uca 33 denetim - veritabanina sallar, GUI acmaz
rem ============================================================

set PY=
python --version >nul 2>&1 && set PY=python
if not defined PY py --version >nul 2>&1 && set PY=py
if not defined PY (
    echo [HATA] Python bulunamadi.
    pause
    exit /b 1
)

%PY% -X utf8 scripts\smoke_test.py
pause
