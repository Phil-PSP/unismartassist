# 🚀 Quick Start - KAAF Chatbot with ngrok

## ✅ Problem Fixed!

The "offline mode" issue has been resolved. I've disabled the service worker and offline detection that was causing the problem.

## 🎯 Start Your App (3 Easy Steps)

### Option 1: Automated (Easiest)
```bash
cd kaaf_chatbot
START_HERE.bat
```
This will:
- Activate virtual environment
- Collect static files
- Start Django server
- Start ngrok tunnel
- Show your public URL

### Option 2: Manual
**Terminal 1 - Django:**
```bash
cd kaaf_chatbot
venv\Scripts\activate
python manage.py runserver 8000
```

**Terminal 2 - ngrok:**
```bash
ngrok http 8000
```

## 📋 Before You Start

### 1. Install ngrok (if not installed)
- Download: https://ngrok.com/download
- Extract and add to PATH

### 2. Configure ngrok (one-time)
```bash
ngrok config add-authtoken YOUR_AUTH_TOKEN
```
Get token from: https://dashboard.ngrok.com/get-started/your-authtoken

## 🌐 Access Your App

After starting, you'll see:
```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:8000
```

**Copy that URL and share it!** 🎉

## 🔧 If You Still See "Offline Mode"

### Clear Browser Data:
1. Press **Ctrl+Shift+Delete**
2. Select "All time"
3. Check:
   - ✅ Cookies and site data
   - ✅ Cached images and files
4. Click "Clear data"

### Unregister Service Worker:
1. Press **F12** (DevTools)
2. Go to **Application** tab
3. Click **Service Workers** (left sidebar)
4. Click **Unregister**
5. Go to **Storage** (left sidebar)
6. Click **Clear site data**
7. **Refresh page**: Ctrl+Shift+R

## ✨ What Was Changed

### Files Modified:
1. **`templates/base.html`**
   - Service Worker disabled (commented out)
   - Offline banner forced to hidden

2. **`templates/chatbot/chat.html`**
   - Offline detection disabled
   - All messages sent as online

### Your Configuration:
- ✅ `.env` has ngrok domains in ALLOWED_HOSTS
- ✅ `settings.py` has CSRF_TRUSTED_ORIGINS configured
- ✅ WebSocket support ready for ngrok

## 🆘 Troubleshooting

### "DisallowedHost" error
- Restart Django server
- Check `.env` has: `.ngrok-free.app,.ngrok.io`

### CSRF verification failed
- Use `https://` (not `http://`) with ngrok URL
- Clear browser cookies

### Can't connect to WebSocket
- Make sure you're using `https://` URL
- Check browser console (F12) for errors

### Django won't start
- Activate virtual environment: `venv\Scripts\activate`
- Install dependencies: `pip install -r requirements.txt`

## 📱 Sharing Your App

1. Start the app (see above)
2. Copy the ngrok URL: `https://abc123.ngrok-free.app`
3. Share with anyone
4. They click "Visit Site" on ngrok warning page
5. App loads normally! 🎉

## 💡 Important Notes

- **Free ngrok URLs change** every time you restart
- **Keep both terminals running** (Django + ngrok)
- **Paid ngrok plans** get custom subdomains
- **First-time visitors** see ngrok warning (they click "Visit Site")

## 🔄 Restoring Offline Features Later

See `NGROK_SETUP.md` for instructions on re-enabling:
- Service Worker
- Offline detection
- Message queueing

---

**Ready to go! Run `START_HERE.bat` and you're live! 🚀**
