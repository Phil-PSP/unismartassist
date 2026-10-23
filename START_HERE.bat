@echo off
REM ========================================
REM KAAF Chatbot - Complete Startup Script
REM ========================================

echo.
echo ========================================
echo KAAF Chatbot - Starting with ngrok
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv venv
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
echo [1/4] Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: ngrok is not installed or not in PATH
    echo Download from: https://ngrok.com/download
    echo.
    echo Continuing with Django server only...
    echo.
)

REM Collect static files
echo [2/4] Collecting static files...
python manage.py collectstatic --noinput >nul 2>&1

REM Start Django server
echo [3/4] Starting Django development server on port 8000...
echo.
start "KAAF Django Server" cmd /k "call venv\Scripts\activate.bat && python manage.py runserver 8000"

REM Wait for Django to start
timeout /t 5 /nobreak >nul

REM Start ngrok if available
where ngrok >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    echo [4/4] Starting ngrok tunnel...
    echo.
    echo ========================================
    echo Your public URL will appear below:
    echo Copy the https://xxxxx.ngrok-free.app URL
    echo ========================================
    echo.
    ngrok http 8000
) else (
    echo [4/4] Skipping ngrok (not installed)
    echo.
    echo ========================================
    echo Django is running at:
    echo http://localhost:8000
    echo ========================================
    echo.
    echo To use ngrok:
    echo 1. Download from https://ngrok.com/download
    echo 2. Run: ngrok http 8000
    echo.
    pause
)
