# Running KAAF Chatbot with ngrok

## Prerequisites

1. **Install ngrok**: Download from https://ngrok.com/download
2. **Sign up for ngrok account**: Get your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
3. **Configure ngrok authtoken** (one-time setup):
   ```bash
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

## Steps to Run

### 1. Start Django Development Server
Open a terminal in the project directory and run:

```bash
cd kaaf_chatbot
python manage.py runserver 8000
```

Keep this terminal running.

### 2. Start ngrok Tunnel
Open a **new terminal** and run:

```bash
ngrok http 8000
```

Or for a custom subdomain (requires paid ngrok plan):
```bash
ngrok http 8000 --subdomain=kaaf-chatbot
```

### 3. Get Your Public URL
After running ngrok, you'll see output like:

```
Forwarding   https://abc123.ngrok-free.app -> http://localhost:8000
```

Copy the `https://abc123.ngrok-free.app` URL - this is your public URL!

### 4. Update ALLOWED_HOSTS (if needed)
Your `.env` already includes `.ngrok-free.app` and `.ngrok.io` wildcards, so any ngrok URL should work automatically.

If you get a "DisallowedHost" error, add your specific ngrok domain to `.env`:
```
ALLOWED_HOSTS=localhost,127.0.0.1,.ngrok-free.app,.ngrok.io,abc123.ngrok-free.app
```

Then restart Django server.

## Important Notes

- **Free ngrok URLs change** every time you restart ngrok
- **Paid plans** allow custom subdomains that don't change
- **Keep both terminals running** (Django + ngrok)
- **Share the ngrok URL** with anyone who needs to access your app
- **ngrok free tier** shows a warning page before redirecting (users click "Visit Site")

## Troubleshooting

### "Invalid Host header" or "DisallowedHost"
- Check that `.ngrok-free.app` is in your `ALLOWED_HOSTS` in `.env`
- Restart Django server after changing `.env`

### CSRF verification failed
- Your `settings.py` already has `CSRF_TRUSTED_ORIGINS` configured for ngrok
- Make sure you're using `https://` (not `http://`) when accessing the ngrok URL

### WebSocket connection issues
- ngrok free tier supports WebSockets
- Make sure your ngrok URL uses `https://` (WebSocket will use `wss://`)

## Alternative: ngrok Configuration File

Create `ngrok.yml` in your home directory for persistent configuration:

```yaml
version: "2"
authtoken: YOUR_AUTH_TOKEN
tunnels:
  kaaf:
    proto: http
    addr: 8000
    inspect: true
```

Then run:
```bash
ngrok start kaaf
```

## Quick Start Script

See `start_ngrok.sh` (Linux/Mac) or `start_ngrok.bat` (Windows) for automated startup.
