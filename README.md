# METO CORE

Production FastAPI backend for **NEXORA**. AI = official **Groq** API.

## Files

| File | Purpose |
|------|---------|
| `main.py` | API server (`app = FastAPI()`) |
| `requirements.txt` | Dependencies |
| `.env.example` | Env var names only |
| `.gitignore` | Ignores `.env` and caches |
| `README.md` | This file |

## Local run

```bash
cp .env.example .env
# edit .env and set GROQ_API_KEY=...

pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Test:

```bash
curl http://127.0.0.1:8000/api/health
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}'
```

## Deploy on Render

1. Push this folder to GitHub (never commit `.env`).
2. Render → **New** → **Web Service** → select the repo.
3. Settings:

| Field | Value |
|-------|--------|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

4. **Environment** → add:

| Key | Value |
|-----|--------|
| `GROQ_API_KEY` | from https://console.groq.com → API Keys |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` (optional) |
| `ALLOWED_ORIGINS` | `*` (optional) |

5. Deploy. Open `https://YOUR-SERVICE.onrender.com/api/health`.

## API

### GET /api/health

```json
{
  "success": true,
  "service": "METO CORE Brain",
  "status": "online",
  "version": "2.1.0",
  "provider": "groq",
  "groq_key_configured": true,
  "auth_required": false
}
```

### GET /api/capabilities

Supported features and model name.

### POST /api/chat

Request:

```json
{ "message": "Hello" }
```

Response:

```json
{
  "success": true,
  "reply": "Hello! How can I help you?",
  "model": "llama-3.3-70b-versatile"
}
```

If `GROQ_API_KEY` is missing:

```json
{
  "success": false,
  "error": {
    "code": "GROQ_KEY_MISSING",
    "message": "GROQ_API_KEY is not configured on the server."
  }
}
```

## Security

- `GROQ_API_KEY` is read only from the environment.
- Never returned in API responses.
- `.env` is gitignored; only `.env.example` is shipped.

## NEXORA

```
METO_CORE_BASE_URL=https://YOUR-SERVICE.onrender.com
```

Call `POST /api/chat` with JSON `{"message":"..."}`.
