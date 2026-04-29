@echo off
chcp 65001 >nul
title Xiaomi MiMo TTS Voice Clone

cd /d "%~dp0"

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.9+ or use the .exe version.
    pause
    exit /b 1
)

:: Install missing deps silently
pip install -q openai flask pydub 2>nul

:: Open browser
start "" "http://localhost:7860"

:: Run
python app.py
pause
