# Real-Time Code Broadcasting System

Production-ready Flask application for real-time code broadcasting with HTTP REST APIs, WebSocket (Socket.IO), and Server-Sent Events (SSE).

## Quick Start

1. **Set Database URL (required):**
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

2. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

3. **Start Server:**
```bash
python app.py  # Development
# Or for production:
gunicorn --config gunicorn.conf.py wsgi:app
```

## Key Endpoints

- `POST /api/ingest` - Send codes via HTTP
- `GET /api/users/<username>/verify` - Verify username
- `GET /health` - Health check
- WebSocket: `/events` namespace
- SSE: `/embed-stream`, `/events` (SSE stream)

## Testing

```bash
python test_sse_helper.py test-all bharat
```

## Rate limiting

- **Convert-to-USD** (`POST /api/users/claims/convert-to-usd`): 15/min per IP, 10/min per username.
- **Embed-stream** (`GET /embed-stream`): 25/min per username (query param `user`).
- **Relay** (`GET /relay`): only allowed domains (see `RELAY_ALLOWED_DOMAINS` in config).

Optional env: `RATELIMIT_IP_USERNAME_PER_MINUTE`, `RATELIMIT_PER_USERNAME_PER_MINUTE`, `RATELIMIT_EMBED_STREAM_PER_USERNAME_PER_MINUTE`. For production with multiple workers, set `RATELIMIT_STORAGE_URI` (e.g. `redis://...`) so limits are shared. Run `python test_rate_limit.py` to verify.

## Production Deployment

Set `DATABASE_URL` in your deployment platform (e.g., Render). For shared rate limits across workers, set `RATELIMIT_STORAGE_URI`.
