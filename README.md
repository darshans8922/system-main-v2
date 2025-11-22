# Real-Time Code Broadcasting System

A production-ready Flask application for real-time code broadcasting with support for HTTP REST APIs, WebSocket (Socket.IO), and Server-Sent Events (SSE).

## Quick Start

0. **Set Database URL (required):**
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"  # Linux/Mac
set DATABASE_URL=postgresql://user:pass@host:5432/dbname       # Windows
```

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start Server:**
```bash
python app.py
```

3. **Create Test User:**
```bash
python test_sse_helper.py create bharat
```

4. **Send Test Code:**
```bash
python test_sse_helper.py send bharat TEST-123
```

## Features

- ✅ **Multiple Connection Methods:** HTTP REST, WebSocket (Socket.IO), SSE
- ✅ **Real-Time Broadcasting:** Codes delivered instantly to all connected clients
- ✅ **Production Ready:** Automatic cleanup, connection limits, monitoring
- ✅ **Scalable:** Supports 200-400 concurrent users on 2GB RAM
- ✅ **Secure:** HMAC token validation, origin checking, username authentication

## Documentation

📖 **Complete documentation available in [DOCUMENTATION.md](DOCUMENTATION.md)**

Includes:
- System overview and flow
- All HTTP REST APIs
- WebSocket (Socket.IO) APIs
- SSE (Server-Sent Events) APIs
- Authentication guide
- Testing guide
- Production deployment guide
- Quick reference

## Key Endpoints

- `POST /api/ingest` - Send codes via HTTP
- `GET /api/users/<username>/verify` - Verify username
- `GET /health` - Health check
- WebSocket: `/events`, `/internal/newcodes`, `/ws/ingest`, `/embed`
- SSE: `/embed-stream`, `/events` (SSE stream)

## Testing

- **Socket.IO Test Page:** `http://localhost:5000/test`
- **SSE Test Page:** `http://localhost:5000/sse-test`
- **Helper Script:** `python test_sse_helper.py`

## Production

See [DOCUMENTATION.md](DOCUMENTATION.md#production-deployment) for:
- Environment variables
- Configuration
- Monitoring
- Scaling guidelines

