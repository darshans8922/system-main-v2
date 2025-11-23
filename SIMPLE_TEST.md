# Simple Test Guide - Send & Receive Codes

## Test with Username: bharat

---

## 1. Send Code (HTTP API)

### Endpoint:
```
POST https://system-main-v2.onrender.com/api/ingest
```

### Payload:
```json
{
  "username": "bharat",
  "code": "TEST-123",
  "source": "my-app",
  "type": "default",
  "metadata": {
    "note": "test code"
  }
}
```

### Examples:

**cURL:**
```bash
curl -X POST https://system-main-v2.onrender.com/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "username": "bharat",
    "code": "TEST-123",
    "source": "curl-test"
  }'
```

**JavaScript:**
```javascript
fetch('https://system-main-v2.onrender.com/api/ingest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'bharat',
    code: 'TEST-123',
    source: 'javascript-test'
  })
})
.then(r => r.json())
.then(console.log);
```

**Python:**
```python
import requests

response = requests.post(
    'https://system-main-v2.onrender.com/api/ingest',
    json={
        'username': 'bharat',
        'code': 'TEST-123',
        'source': 'python-test'
    }
)
print(response.json())
```

**Response:**
```json
{
  "status": "success",
  "message": "Code received and broadcasted",
  "username": "bharat"
}
```

---

## 2. Receive Code (WebSocket)

### Connection URL:
```
wss://system-main-v2.onrender.com/events?username=bharat
```

### JavaScript (Browser):
```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <h1>Code Receiver for bharat</h1>
    <div id="output"></div>
    
    <script>
        const socket = io('https://system-main-v2.onrender.com/events', {
            query: { username: 'bharat' }
        });
        
        socket.on('connect', () => {
            console.log('✅ Connected');
            document.getElementById('output').innerHTML += '<p>✅ Connected</p>';
        });
        
        socket.on('new_code', (data) => {
            console.log('📨 Code received:', data);
            document.getElementById('output').innerHTML += 
                `<p><strong>Code:</strong> ${data.code}<br>
                 <strong>Source:</strong> ${data.source}<br>
                 <strong>Time:</strong> ${data.timestamp}</p>`;
        });
    </script>
</body>
</html>
```

### Python:
```python
import socketio
import time

sio = socketio.Client()

@sio.on('connect', namespace='/events')
def on_connect():
    print('✅ Connected')

@sio.on('new_code')
def on_code(data):
    print(f'📨 Code received: {data["code"]}')
    print(f'   Source: {data["source"]}')
    print(f'   Timestamp: {data["timestamp"]}')

# Connect
sio.connect('https://system-main-v2.onrender.com/events?username=bharat')

# Keep running to receive codes
sio.wait()
```

### Node.js:
```javascript
const io = require('socket.io-client');

const socket = io('https://system-main-v2.onrender.com/events', {
    query: { username: 'bharat' }
});

socket.on('connect', () => {
    console.log('✅ Connected');
});

socket.on('new_code', (data) => {
    console.log('📨 Code received:', data.code);
    console.log('   Source:', data.source);
});
```

---

## Quick Test Script

Run this Python script to test both send and receive:

```python
import socketio
import requests
import time

sio = socketio.Client()
received = []

@sio.on('connect', namespace='/events')
def on_connect():
    print('✅ WebSocket connected')

@sio.on('new_code')
def on_code(data):
    print(f'📨 Received: {data["code"]}')
    received.append(data)

# Connect
sio.connect('https://system-main-v2.onrender.com/events?username=bharat')
time.sleep(2)

# Send code
code = f'TEST-{int(time.time())}'
print(f'📤 Sending: {code}')
response = requests.post(
    'https://system-main-v2.onrender.com/api/ingest',
    json={'username': 'bharat', 'code': code, 'source': 'test'}
)
print(f'✅ Sent: {response.json()}')

# Wait to receive
time.sleep(3)
print(f'📊 Received {len(received)} code(s)')

sio.disconnect()
```

Or use the included script:
```bash
python quick_test_send_receive.py
```

---

## What You'll Receive

When a code is sent, all connected WebSocket clients receive:

```json
{
  "code": "TEST-123",
  "username": "bharat",
  "user_id": 1,
  "source": "my-app",
  "type": "default",
  "timestamp": "2025-11-22T20:00:00.000000",
  "value": 3,
  "metadata": {
    "note": "test code"
  }
}
```

---

## Required Fields

**Send Code (Minimum):**
- `username` - Must be "bharat" (or any user that exists in database)
- `code` - The code string to broadcast

**Optional Fields:**
- `source` - Source identifier
- `type` - Code type (default: "default")
- `metadata` - Additional data object

---

## Test It Now

1. **Open browser console** and paste the JavaScript code above
2. **In another terminal**, send a code using cURL:
   ```bash
   curl -X POST https://system-main-v2.onrender.com/api/ingest \
     -H "Content-Type: application/json" \
     -d '{"username":"bharat","code":"HELLO-123","source":"test"}'
   ```
3. **Watch the browser** - you should see the code appear!

