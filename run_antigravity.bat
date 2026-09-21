@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [1/2] Tworzenie srodowiska Python...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Nie udalo sie utworzyc .venv. Sprawdz instalacje Pythona.
        pause
        exit /b 1
    )
    echo [2/2] Instalowanie zaleznosci...
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Instalacja zaleznosci nie powiodla sie.
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" app_gui.py
if errorlevel 1 pause
