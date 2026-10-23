#!/bin/bash
# Linux/Mac script to start Django and ngrok

echo "========================================"
echo "KAAF Chatbot - Starting with ngrok"
echo "========================================"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "ERROR: ngrok is not installed or not in PATH"
    echo "Please download from: https://ngrok.com/download"
    echo ""
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Starting Django development server..."
echo ""

# Start Django in background
python manage.py runserver 8000 &
DJANGO_PID=$!

# Wait for Django to start
sleep 5

echo ""
echo "Starting ngrok tunnel..."
echo ""
echo "Your public URL will appear below:"
echo "========================================"
echo ""

# Start ngrok (this will block)
ngrok http 8000

# When ngrok exits, kill Django
echo ""
echo "Stopping Django server..."
kill $DJANGO_PID

echo "Done!"
