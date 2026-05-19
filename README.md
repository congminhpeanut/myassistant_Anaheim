ENVI Translator
===============

A mobile-first web app for real-time English-to-Vietnamese translation while traveling.

Features
--------
- **Camera translation**: Point your phone camera at printed English text, tap capture, and see Vietnamese translation.
- **Voice translation**: Tap the mic, speak English, get Vietnamese text back.
- **Text-to-speech**: Tap the speaker icon to hear the Vietnamese translation spoken aloud.
- **PWA support**: Add to your Android home screen for native-app feel.

Architecture
------------
- **Backend**: Python Flask (OCR via pytesseract, translation via Ollama Cloud API: kimi-k2.6:cloud)
- **Frontend**: Vanilla JS + Tailwind CSS, Web Speech API, HTML5 getUserMedia camera
- **No database**: Images processed in-memory, no files saved.

Local Development (WSL)
-----------------------
### Prerequisites
- Ubuntu 22.04+
- Python 3.10+
- `tesseract-ocr` installed:
  ```bash
  sudo apt-get update && sudo apt-get install -y tesseract-ocr
  ```

### Setup
```bash
cd /mnt/d/hermes_data/private_online_translation_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run
```bash
source .venv/bin/activate
python3 app.py
```
App will be at `http://localhost:5000`

### Test endpoints
```bash
curl -X POST http://localhost:5000/api/translate \
  -H "Content-Type: application/json" \
  -d '{"text":"Where is the pharmacy?"}'

curl -F "image=@your_sign.png" http://localhost:5000/api/ocr_translate
```

Deploy to Render (Recommended for travel)
------------------------------------------
1. Push this repo to GitHub.
2. Go to [Render.com](https://render.com) → "New Web Service" → connect GitHub repo.
3. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Environment Variables**:
     | Key | Value |
     |-----|-------|
     | `OLLAMA_API_KEY` | `your_api_key_here` |
     | `OLLAMA_BASE_URL` | `https://ollama.com/api` |
     | `OLLAMA_MODEL` | `kimi-k2.6:cloud` |
     | `FLASK_ENV` | `production` |
4. Deploy. The URL is accessible worldwide from your Android phone.

Cloudflare Tunnel Fallback
--------------------------
If you prefer to keep everything on your laptop:
```bash
# Install cloudflared
sudo snap install cloudflared

# Start Flask
source .venv/bin/activate
python3 app.py

# In another terminal
cloudflared tunnel --url http://localhost:5000
```
Copy the generated `.trycloudflare.com` URL to your phone. **Your laptop must stay on.**

Environment Variables
---------------------
| Variable | Description |
|----------|-------------|
| `OLLAMA_API_KEY` | Your Ollama cloud API key |
| `OLLAMA_BASE_URL` | `https://ollama.com/api` |
| `OLLAMA_MODEL` | `kimi-k2.6:cloud` |
| `FLASK_PORT` | Local dev port (default 5000) |
| `FLASK_ENV` | `production` or `development` |

Important Config for Render
---------------------------
- `Aptfile`: contains `tesseract-ocr` so Render installs it at build time.
- `runtime.txt`: pins Python 3.11.
- `Procfile`: uses gunicorn to serve Flask.

Notes
-----
- API responses from `/api/chat` return translation in `"message"."content"`. The OpenAI-compatible `/v1/chat/completions` did not populate `"content"` correctly for this model, so the native endpoint is used directly via `requests`.
- For the USA trip, deploy to Render and add the PWA to your Android home screen for one-tap access.
- No camera images or sensitive data are stored on disk.
