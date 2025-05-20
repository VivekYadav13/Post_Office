@echo off
:: IndiaPostAI Auto-Launcher
title IndiaPostAI Flask App
color 0a
cls

cd /d "%~dp0"

if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

if not exist "templates\" (
    mkdir templates
    echo Created missing templates folder
)

if not exist "data\" (
    mkdir data
    echo Created missing data folder
)

pip install flask --quiet

echo Starting Flask app at http://127.0.0.1:5001
echo Press CTRL+C to stop
python app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Application failed to start!
    echo Common fixes:
    echo 1. Check if app.py exists
    echo 2. Look for missing files
    echo 3. Try changing port in app.py
)
pause