@echo off
REM Windows batch script to start Django and ngrok

echo ========================================
echo KAAF Chatbot - Starting with ngrok
echo ========================================
echo.

REM Check if ngrok is installed
where ngrok >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: ngrok is not installed or not in PATH
    echo Please download from: https://ngrok.com/download
    echo.
    pause
    exit /b 1
)

echo Starting Django development server...
echo.

REM Start Django in a new window
start "Django Server" cmd /k "cd /d %~dp0 && python manage.py runserver 8000"

REM Wait a few seconds for Django to start
timeout /t 5 /nobreak >nul

echo.
echo Starting ngrok tunnel...
echo.
echo Your public URL will appear below:
echo ========================================
echo.

REM Start ngrok (this will keep the window open)
ngrok http 8000

REM If ngrok exits, this will run
echo.
echo ngrok has stopped.
pause
