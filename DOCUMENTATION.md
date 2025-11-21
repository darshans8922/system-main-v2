# Complete System Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [System Flow](#system-flow)
3. [HTTP REST APIs](#http-rest-apis)
4. [WebSocket APIs (Socket.IO)](#websocket-apis-socketio)
5. [SSE (Server-Sent Events) APIs](#sse-server-sent-events-apis)
6. [Authentication](#authentication)
7. [Testing Guide](#testing-guide)
8. [Production Deployment](#production-deployment)
9. [Quick Reference](#quick-reference)

---

## System Overview

This is a real-time code broadcasting system that supports multiple connection methods:
- **HTTP REST APIs** - For simple code ingestion
- **WebSocket (Socket.IO)** - For bidirectional real-time communication
- **SSE (Server-Sent Events)** - For one-way streaming via hidden iframes

### Key Features
- Username-based authentication
- Real-time code broadcasting to all connected clients
- Multiple ingestion methods (HTTP, WebSocket, SSE)
- Automatic connection cleanup and memory management
- Production-ready with monitoring endpoints

---

## System Flow

### 1. Authentication Flow
```
Client → Provides username → Server validates against database → Cache result
```

**Details:**
- Every request must include a `username`
- Server validates against `app_users` table
- Results are cached (180s TTL) for performance
- Unknown usernames receive `403 Forbidden`

### 2. Code Ingestion Flow
```
Client → Send code → Server validates → Normalize payload → Broadcast to all clients
```

**Details:**
- Codes can be sent via HTTP POST/GET, WebSocket, or SSE
- Server normalizes the payload (adds defaults, validates structure)
- Server adds: `username`, `user_id`, `timestamp`
- For SSE: Server adds `value: 3` field

### 3. Code Broadcasting Flow
```
Code received → websocket_manager.broadcast_code() → 
  ├─ Socket.IO clients (all namespaces)
  └─ SSE clients (via message queues)
```

**Details:**
- Codes are broadcast simultaneously to Socket.IO and SSE clients
- Socket.IO: Uses rooms (`code_listeners`) and default namespace
- SSE: Uses per-user message queues
- All clients receive the same code data in real-time

### 4. Connection Management
```
Client connects → Server validates → Add to connection pool → 
  ├─ Heartbeat (ping/pong every 10s)
  └─ Auto-cleanup (stale connections after 120s)
```

---

## HTTP REST APIs

### Base URL
```
http://localhost:5000  (development)
https://your-domain.com  (production)
```

### Endpoints

#### 1. `POST /api/ingest` (Primary Code Ingestion)
**Purpose:** Send codes via HTTP

**Request:**
```http
POST /api/ingest
Content-Type: application/json

{
  "username": "bharat",
  "code": "ABC123",
  "source": "my-app",
  "type": "default",
  "metadata": {
    "note": "test"
  }
}
```

**Response (200):**
```json
{
  "status": "success",
  "message": "Code received and broadcasted",
  "username": "bharat"
}
```

**Alternative: GET Method**
```http
GET /api/ingest?username=bharat&code=ABC123&source=my-app
```

**Error Responses:**
- `400` - Missing username or invalid code
- `403` - Unknown username
- `500` - Server error

---

#### 2. `GET /api/users/<username>/verify`
**Purpose:** Verify if a username exists

**Request:**
```http
GET /api/users/bharat/verify
```

**Response (200 - User exists):**
```json
{
  "username": "bharat",
  "user_id": 1,
  "verified": true,
  "cache_expires_at": 1732030000
}
```

**Response (404 - User not found):**
```json
{
  "username": "invalid",
  "verified": false
}
```

---

#### 3. `GET /health`
**Purpose:** Public health check

**Response (200):**
```json
{
  "status": "healthy",
  "service": "code-server"
}
```

---

#### 4. `GET /internal/health`
**Purpose:** Internal health check with extra metadata

**Response (200):**
```json
{
  "status": "healthy",
  "service": "code-server",
  "internal": true
}
```

---

#### 5. `GET /sse-stats`
**Purpose:** SSE connection statistics (monitoring)

**Response (200):**
```json
{
  "active_connections": 150,
  "users_with_connections": 150,
  "total_queued_messages": 23,
  "total_health_tracked": 150
}
```

---

#### 6. `GET /relay?url=...`
**Purpose:** HTTP proxy to bypass CSP/CORS restrictions

**Request:**
```http
GET /relay?url=https://example.com/api
```

**Response:** Proxied content from target URL

**Error Responses:**
- `400` - Missing url parameter
- `500` - Upstream fetch failed

---

#### 7. Decoy Routes
These routes return randomized JSON to mislead scanners:
- `GET /`
- `GET /dashboard`
- `GET /admin`
- `GET /api`
- `GET /status`
- `GET /api/status`
- `GET /api/info`

---

## WebSocket APIs (Socket.IO)

### Connection
All WebSocket connections require `username` in query string or header.

**JavaScript:**
```javascript
const socket = io('http://localhost:5000/events', {
  query: { username: 'bharat' }
});
```

**Python:**
```python
import socketio
sio = socketio.Client()
sio.connect('http://localhost:5000/events?username=bharat')
```

---

### Namespaces

#### 1. `/events` - Code Listener (Primary)
**Purpose:** Receive code broadcasts

**Connection:**
```javascript
const socket = io('/events', { query: { username: 'bharat' } });
```

**Subscribe:**
```javascript
socket.on('connect', () => {
  socket.emit('subscribe');
});
```

**Listen for codes:**
```javascript
socket.on('new_code', (data) => {
  console.log('Code received:', data);
});
```

**Received Payload:**
```json
{
  "code": "ABC123",
  "source": "my-app",
  "type": "default",
  "username": "bharat",
  "user_id": 1,
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {}
}
```

---

#### 2. `/internal/newcodes` - Code Ingestion (Bots/CLI)
**Purpose:** Send codes via WebSocket

**Connection:**
```javascript
const socket = io('/internal/newcodes', { query: { username: 'bharat' } });
```

**Send code:**
```javascript
socket.emit('code', {
  code: 'ABC123',
  source: 'my-app',
  type: 'default',
  metadata: {}
});
```

**Response Events:**
- `ack` → `{status: 'received'}`
- `error` → `{message: '...'}`

---

#### 3. `/ws/ingest` - Code Ingestion (Public)
**Purpose:** Same as `/internal/newcodes`, public variant

**Usage:** Identical to `/internal/newcodes`

---

#### 4. `/embed` - Code Ingestion (Embed Widgets)
**Purpose:** Same as `/ws/ingest`, for embed widgets

**Usage:** Identical to `/ws/ingest`

---

#### 5. `(default)` - Fallback Namespace
**Purpose:** Backwards compatibility

**Usage:** All `new_code` broadcasts also go to default namespace

---

## SSE (Server-Sent Events) APIs

### Overview
SSE provides a hidden iframe-based streaming solution for cross-origin scenarios. The iframe maintains a 24/7 connection and forwards messages to the parent window via `postMessage`.

---

### 1. `GET /embed-stream`
**Purpose:** Returns HTML page that creates SSE connection in hidden iframe

**Request:**
```http
GET /embed-stream?user=bharat&nonce=random12345
```

**Parameters:**
- `user` (required) - Username
- `nonce` (required) - Random string (minimum 8 characters)

**Response:** HTML page with embedded JavaScript that:
1. Creates EventSource connection to `/events`
2. Forwards messages to parent window via `postMessage`
3. Handles reconnection automatically

**Security:**
- Validates origin against `ALLOWED_ORIGINS`
- Generates HMAC-signed token (15-minute expiry)
- Validates nonce (minimum 8 characters)

**Error Responses:**
- `400` - Missing user/nonce or invalid nonce
- `403` - Unknown username or unauthorized origin
- `500` - Server configuration error

---

### 2. `GET /events` (SSE Stream)
**Purpose:** Server-Sent Events stream for real-time code delivery

**Request:**
```http
GET /events?user=bharat&token=SIGNED_TOKEN
```

**Parameters:**
- `user` (required) - Username
- `token` (required) - HMAC-signed token from `/embed-stream`

**Response:** `text/event-stream` with:
- Initial `connected` message
- Real-time code broadcasts
- Ping messages every 10 seconds
- Keepalive comments every 15 seconds

**Message Format:**
```
data: {"type":"connected","message":"SSE stream connected","username":"bharat",...}

data: {"code":"ABC123","source":"my-app","value":3,...}

: SSE keepalive
```

---

### 3. `POST /sse-pong`
**Purpose:** Heartbeat response endpoint

**Request:**
```http
POST /sse-pong?connection_id=bharat_1234567890&token=SIGNED_TOKEN
```

**Response (200):**
```json
{
  "status": "pong_received"
}
```

**Purpose:** Updates last pong time to keep connection alive

---

### PostMessage Events (from iframe to parent)

The iframe sends these events to the parent window:

#### `iframe_ready`
Sent when iframe loads:
```javascript
{
  type: 'iframe_ready',
  nonce: 'random12345',
  timestamp: 1234567890
}
```

#### `iframe_sse_connected`
Sent when SSE connection is established:
```javascript
{
  type: 'iframe_sse_connected',
  nonce: 'random12345',
  timestamp: 1234567890
}
```

#### `iframe_sse_message`
Sent when new code/data arrives:
```javascript
{
  type: 'iframe_sse_message',
  data: {
    code: 'ABC123',
    source: 'my-app',
    value: 3,
    ...
  },
  nonce: 'random12345',
  timestamp: 1234567890
}
```

#### `iframe_pong_success`
Sent after successful heartbeat:
```javascript
{
  type: 'iframe_pong_success',
  nonce: 'random12345',
  timestamp: 1234567890
}
```

#### `iframe_sse_error`
Sent on connection errors:
```javascript
{
  type: 'iframe_sse_error',
  attempt: 1,
  maxAttempts: 5,
  nonce: 'random12345',
  timestamp: 1234567890,
  error: 'Connection error'  // optional
}
```

#### `iframe_sse_failed`
Sent when max reconnect attempts reached:
```javascript
{
  type: 'iframe_sse_failed',
  nonce: 'random12345',
  timestamp: 1234567890,
  error: 'error message'  // optional
}
```

---

### Client Integration Example

```javascript
// Create hidden iframe
const username = 'bharat';
const nonce = Math.random().toString(36).substring(2, 15);
const iframeUrl = `${API_BASE_URL}/embed-stream?user=${username}&nonce=${nonce}`;

const iframe = document.createElement('iframe');
iframe.src = iframeUrl;
iframe.sandbox = 'allow-scripts allow-same-origin';
iframe.style.display = 'none';
document.body.appendChild(iframe);

// Listen for messages
window.addEventListener('message', function(event) {
  switch (event.data.type) {
    case 'iframe_ready':
      console.log('Iframe loaded');
      break;
    case 'iframe_sse_connected':
      console.log('SSE connected');
      break;
    case 'iframe_sse_message':
      console.log('Code received:', event.data.data);
      break;
    case 'iframe_pong_success':
      console.log('Heartbeat OK');
      break;
    case 'iframe_sse_error':
      console.error('Connection error:', event.data);
      break;
    case 'iframe_sse_failed':
      console.error('Connection failed');
      break;
  }
});
```

---

## Authentication

### HTTP Authentication
Include `username` in:
- JSON body: `{"username": "bharat", ...}`
- Query params: `?username=bharat`
- Form data: `username=bharat`

### WebSocket Authentication
Include `username` in:
- Query string: `io('/events', { query: { username: 'bharat' } })`
- Header: `X-Username: bharat`

### SSE Authentication
1. Request `/embed-stream` with `user` and `nonce` parameters
2. Server generates HMAC-signed token
3. Iframe uses token to connect to `/events`
4. Token expires after 15 minutes

### Token Security (SSE)
- Tokens are HMAC-signed with `WS_SECRET`
- Format: `{user}:{expiry}:{signature}`
- Expiry: 15 minutes
- Validated on every `/events` request

---

## Testing Guide

### Prerequisites

1. **Start Server:**
```bash
python app.py
```

2. **Create Test User:**
```bash
python test_sse_helper.py create bharat
```

3. **Verify User:**
```bash
curl http://localhost:5000/api/users/bharat/verify
```

---

### Test HTTP API

**Send Code:**
```bash
curl -X POST http://localhost:5000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"username":"bharat","code":"TEST-123","source":"curl"}'
```

**Expected Response:**
```json
{
  "status": "success",
  "message": "Code received and broadcasted",
  "username": "bharat"
}
```

---

### Test WebSocket

**JavaScript (Browser Console):**
```javascript
const socket = io('http://localhost:5000/events', {
  query: { username: 'bharat' }
});

socket.on('connect', () => {
  console.log('Connected');
  socket.emit('subscribe');
});

socket.on('new_code', (data) => {
  console.log('Code:', data);
});
```

**Python:**
```python
import socketio

sio = socketio.Client()
sio.connect('http://localhost:5000/events?username=bharat')

@sio.on('connect')
def on_connect():
    sio.emit('subscribe', namespace='/events')

@sio.on('new_code')
def on_code(data):
    print('Code:', data)
```

---

### Test SSE

**Option 1: Use Test Page**
1. Open: `http://localhost:5000/sse-test`
2. Page auto-connects
3. Send code via API
4. Watch events appear in log

**Option 2: Manual Integration**
```html
<!DOCTYPE html>
<html>
<head>
    <title>SSE Test</title>
</head>
<body>
    <div id="status">Connecting...</div>
    <div id="messages"></div>

    <script>
        const username = 'bharat';
        const nonce = Math.random().toString(36).substring(2, 15);
        const iframeUrl = `http://localhost:5000/embed-stream?user=${username}&nonce=${nonce}`;
        
        const iframe = document.createElement('iframe');
        iframe.src = iframeUrl;
        iframe.style.display = 'none';
        document.body.appendChild(iframe);
        
        window.addEventListener('message', function(event) {
            console.log('Event:', event.data);
            if (event.data.type === 'iframe_sse_message') {
                document.getElementById('messages').innerHTML += 
                    '<div>' + JSON.stringify(event.data.data) + '</div>';
            }
        });
    </script>
</body>
</html>
```

---

### Test Helper Script

**Create User:**
```bash
python test_sse_helper.py create bharat
```

**Verify User:**
```bash
python test_sse_helper.py verify bharat
```

**Send Code:**
```bash
python test_sse_helper.py send bharat TEST-123
```

---

## Production Deployment

### Requirements
- Python 3.8+
- Flask, Flask-SocketIO
- SQLAlchemy
- 2GB RAM (supports 200-400 concurrent users)

### Environment Variables
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key-here
WS_SECRET=your-ws-secret-here  # or uses SECRET_KEY as fallback

# Optional
ENVIRONMENT=production
RENDER_EXTERNAL_URL=https://your-app.onrender.com
```
> **Important:** The application will refuse to start if `DATABASE_URL` is not set. Point it to your production database (Postgres, MySQL, etc.).

### Configuration

**Allowed Origins** (`app/config.py`):
```python
ALLOWED_ORIGINS = [
    "https://your-domain.com",
    "https://stake.com",
    # ... add your domains
]
```

### Production Checklist

- [x] Automatic connection cleanup (stale connections after 120s)
- [x] Connection limits (500 max)
- [x] Error logging
- [x] Monitoring endpoint (`/sse-stats`)
- [ ] Set `WS_SECRET` environment variable
- [ ] Configure `ALLOWED_ORIGINS`
- [ ] Set up monitoring alerts
- [ ] Load test with expected user count
- [ ] Monitor memory usage for 24-48 hours

### Monitoring

**Check SSE Stats:**
```bash
curl http://localhost:5000/sse-stats
```

**Expected Response:**
```json
{
  "active_connections": 150,
  "users_with_connections": 150,
  "total_queued_messages": 23,
  "total_health_tracked": 150
}
```

**Set Up Alerts:**
- Connection count > 450 (80% of limit)
- Memory usage > 1.5GB
- Cleanup removing > 50 connections/hour

### Memory Estimation (400 Users)

- SSE System: ~80-100MB
- Socket.IO: ~50-100MB
- Database: ~50MB
- Other: ~200MB
- **Total: ~400-500MB**
- **Available: ~1.5GB**
- **Headroom: ~1GB** ✅

### Scaling Beyond 400 Users

For 1000+ users, consider:
1. **Redis** for message queues (multi-worker support)
2. **Message broker** (RabbitMQ/Redis PubSub)
3. **Load balancer** (distribute connections)
4. **Connection pooling** (optimize database)
5. **Monitoring** (Prometheus/Grafana)

---

## Quick Reference

### Send Code (All Methods)

**HTTP:**
```bash
curl -X POST http://localhost:5000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"username":"bharat","code":"ABC123","source":"test"}'
```

**WebSocket (JavaScript):**
```javascript
socket.emit('code', {code: 'ABC123', source: 'test'});
```

**WebSocket (Python):**
```python
sio.emit('code', {'code': 'ABC123', 'source': 'test'})
```

---

### Receive Code (All Methods)

**WebSocket (JavaScript):**
```javascript
socket.on('new_code', (data) => console.log(data));
```

**SSE (via iframe):**
```javascript
window.addEventListener('message', (event) => {
  if (event.data.type === 'iframe_sse_message') {
    console.log(event.data.data);
  }
});
```

---

### Code Payload Structure

**Send:**
```json
{
  "username": "bharat",      // Required (HTTP only)
  "code": "ABC123",          // Required
  "source": "my-app",        // Optional (default: "unknown")
  "type": "default",         // Optional (default: "default")
  "metadata": {}             // Optional
}
```

**Receive:**
```json
{
  "code": "ABC123",
  "source": "my-app",
  "type": "default",
  "username": "bharat",      // Added by server
  "user_id": 1,              // Added by server
  "timestamp": "2024-01-01T12:00:00",  // Added by server
  "value": 3,                // Added by server (SSE only)
  "metadata": {}             // Enhanced by server
}
```

---

### Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| `400` | Missing username or invalid code | Check payload structure |
| `401` | Invalid/expired token (SSE) | Refresh iframe connection |
| `403` | Unknown username | Verify user exists: `/api/users/<username>/verify` |
| `500` | Server error | Check server logs |

---

### WebSocket Error Events

- `error` → `{message: 'Unauthorized or unknown username'}` → Username invalid
- `error` → `{message: 'Invalid code data'}` → Code missing/invalid

---

### Connection Limits

- **Max SSE Connections:** 500 (configurable)
- **Max Queue Size:** 100 messages per user
- **Connection Timeout:** 120 seconds (stale connections cleaned up)
- **Token Expiry (SSE):** 15 minutes

---

### Testing Endpoints

- **Socket.IO Test:** `http://localhost:5000/test`
- **SSE Test:** `http://localhost:5000/sse-test`
- **Health Check:** `http://localhost:5000/health`
- **SSE Stats:** `http://localhost:5000/sse-stats`

---

## Support

For issues or questions:
1. Check server logs
2. Check browser console (F12)
3. Verify user exists: `GET /api/users/<username>/verify`
4. Check connection stats: `GET /sse-stats`
5. Review this documentation

---

**Last Updated:** 2024-11-21

