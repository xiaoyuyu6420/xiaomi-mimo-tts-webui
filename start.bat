@echo off
chcp 65001 >nul
title Xiaomi MiMo TTS Voice Clone

echo.
echo ==========================================
echo   Xiaomi MiMo TTS Voice Clone
echo ==========================================
echo.

cd /d "%~dp0"

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+ from https://www.python.org
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo Using Python: %PYVER%

:: Check ffmpeg
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] ffmpeg not found. MP3 files may not work.
    echo Install from https://ffmpeg.org/download.html and add to PATH
    echo.
)

:: Setup virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

:: Activate venv
call venv\Scripts\activate.bat

:: Install dependencies
echo Checking dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo.
echo Starting server...
echo Open http://localhost:7860 in your browser
echo Press Ctrl+C to stop
echo.

:: Auto-open browser
start "" "http://localhost:7860"

:: Start server
python app.py

pause
