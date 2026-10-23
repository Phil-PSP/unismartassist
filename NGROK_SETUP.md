# 🚀 KAAF Chatbot - ngrok Setup Guide

## ✅ Changes Made for ngrok

I've disabled the offline detection features that were causing the "offline mode" message:

### Files Modified:
1. **`templates/base.html`**
   - Disabled Service Worker registration (commented out)
   - Forced online status in offline detection banner

2. **`templates/chatbot/chat.html`**
   - Disabled offline message queueing
   - Set `offline: false` for all chat messages

## 🎯 How to Start with ngrok

### Step 1: Install ngrok
```bash
# Download from https://ngrok.com/download
# Or use package manager:
choco install ngrok  # Windows (Chocolatey)
brew install ngrok   # Mac (Homebrew)
```

### Step 2: Configure ngrok (one-time)
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```
Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken

### Step 3: Start Django Server
```bash
cd kaaf_chatbot
python manage.py runserver 8000
```

### Step 4: Start ngrok (in a new terminal)
```bash
ngrok http 8000
```

### Step 5: Access Your App
Copy the ngrok URL from the terminal output:
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:8000
```

Visit: `https://abc123.ngrok-free.app`

## 🔧 Troubleshooting

### Still seeing "offline mode"?
1. **Clear browser cache**: Ctrl+Shift+Delete (Chrome/Edge)
2. **Unregister service worker**:
   - Open DevTools (F12)
   - Go to Application > Service Workers
   - Click "Unregister"
   - Refresh page (Ctrl+Shift+R)

3. **Clear site data**:
   - DevTools > Application > Storage
   - Click "Clear site data"
   - Refresh page

### "DisallowedHost" error?
Your `.env` already has ngrok domains configured:
```
ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app,.ngrok.io
```

If you still get the error, restart Django server.

### CSRF verification failed?
Your `settings.py` already has:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
]
```

Make sure you're using `https://` (not `http://`) with ngrok URL.

### WebSocket not connecting?
- ngrok free tier supports WebSockets
- Use `https://` for the page (WebSocket will use `wss://`)
- Check browser console for connection errors

## 🔄 Restoring Offline Features

When you're done testing with ngrok and want to restore offline functionality:

### 1. Re-enable Service Worker
In `templates/base.html`, uncomment the service worker registration:
```javascript
// Remove the /* and */ comments around the service worker code
```

### 2. Re-enable Offline Detection
In `templates/base.html`, change:
```javascript
const isOnline = true; // Change to: navigator.onLine
```

### 3. Re-enable Chat Offline Mode
In `templates/chatbot/chat.html`, uncomment the offline check:
```javascript
// Remove the /* and */ comments around the navigator.onLine check
```

## 📝 Quick Commands

### Windows (Automated)
```bash
cd kaaf_chatbot
start_ngrok.bat
```

### Manual (2 terminals)
Terminal 1:
```bash
cd kaaf_chatbot
python manage.py runserver 8000
```

Terminal 2:
```bash
ngrok http 8000
```

## 🌐 Sharing Your App

1. Copy the ngrok URL: `https://abc123.ngrok-free.app`
2. Share with anyone
3. They'll see an ngrok warning page (click "Visit Site")
4. Your app will load normally

## 💡 Tips

- **Free ngrok URLs change** every restart
- **Paid plans** get custom subdomains
- **Keep both terminals running** while testing
- **Check your internet connection** if issues persist

## 🆘 Still Having Issues?

1. Check your actual internet connection
2. Try a different browser
3. Check browser console (F12) for errors
4. Verify Django server is running on port 8000
5. Verify ngrok is tunneling to port 8000

---

**Your app is now configured for ngrok! 🎉**
