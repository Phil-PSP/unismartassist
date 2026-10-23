# 🔄 Restart Django Server

## Backend Changes Applied

I've fixed the offline mode issue in the **backend code**. You need to restart your Django server for the changes to take effect.

## Files Changed:
1. ✅ `apps/chatbot/views.py` - Forced online mode
2. ✅ `apps/chatbot/consumers.py` - Forced online mode for WebSocket
3. ✅ `templates/base.html` - Disabled service worker
4. ✅ `templates/chatbot/chat.html` - Disabled offline detection

## How to Restart

### Option 1: Stop and Restart
1. **Stop Django server**: Press `Ctrl+C` in the Django terminal
2. **Restart**: 
   ```bash
   python manage.py runserver 8000
   ```

### Option 2: Use the Startup Script
1. **Stop Django server**: Press `Ctrl+C` in the Django terminal
2. **Stop ngrok**: Press `Ctrl+C` in the ngrok terminal
3. **Run**:
   ```bash
   START_HERE.bat
   ```

## After Restarting

1. **Clear browser cache** (important!):
   - Press `Ctrl+Shift+Delete`
   - Clear "All time"
   - Check "Cookies" and "Cached files"
   - Click "Clear data"

2. **Unregister service worker**:
   - Press `F12` (DevTools)
   - Go to "Application" tab
   - Click "Service Workers"
   - Click "Unregister"
   - Click "Clear site data"

3. **Hard refresh**:
   - Press `Ctrl+Shift+R`

4. **Test the chatbot**:
   - Send a message
   - Should get AI response (not offline message)

## What Changed

### Before:
```
📡 I'm in offline mode, Kofi. My AI brain needs internet...
```

### After:
```
[Normal AI-powered response from Gemini]
```

## Troubleshooting

### Still seeing offline mode?
1. Make sure you **restarted Django server**
2. **Clear ALL browser data** (not just cache)
3. **Unregister service worker** in DevTools
4. Try a **different browser** or **incognito mode**
5. Check that your **Gemini API key** is set in `.env`

### Check if server restarted correctly:
Look for this in the Django terminal:
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Verify changes are loaded:
The Django server should show:
```
Watching for file changes with StatReloader
```

This means it's monitoring for code changes.

## Quick Test

After restarting, try these messages in the chatbot:
- "Hello" - Should get AI greeting
- "What is my GPA?" - Should show your GPA
- "Tell me about KAAF" - Should get AI response

If all work without "offline mode" message, you're good! ✅

---

**Remember: Always restart Django after backend code changes!**
