@echo off
:: Navigate to the directory where this batch file is located
cd /d "%~dp0"

:: Check if python is in the path and run the application
python main.py

:: If it fails, try python3
if %errorlevel% neq 0 (
    python3 main.py
)

:: Keep the window open if there is an error
if %errorlevel% neq 0 (
    pause
)
