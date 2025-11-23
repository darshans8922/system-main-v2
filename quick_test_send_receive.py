"""
Quick test script to send a code and receive it via WebSocket.
Usage: python quick_test_send_receive.py
"""
import socketio
import requests
import time

# Create Socket.IO client
sio = socketio.Client()
received_codes = []

@sio.on('connect', namespace='/events')
def on_connect():
    print('✅ WebSocket connected to /events namespace')

@sio.on('new_code')
def on_code(data):
    print(f'📨 Code received: {data["code"]}')
    print(f'   Source: {data["source"]}')
    print(f'   Timestamp: {data["timestamp"]}')
    received_codes.append(data)

@sio.on('error')
def on_error(error):
    print(f'❌ Error: {error}')

print('=== Quick Send & Receive Test ===\n')

# Connect to WebSocket
print('1. Connecting to WebSocket...')
try:
    print('   (This may take 30-60s if Render is in cold start...)')
    sio.connect(
        'https://system-main-v2.onrender.com/events?username=bharat',
        wait_timeout=60,
        transports=['websocket', 'polling']
    )
    time.sleep(2)  # Wait for connection to establish
except Exception as e:
    print(f'❌ Connection failed: {e}')
    print('   Tip: Render free tier may have cold starts. Try again in 1-2 minutes.')
    exit(1)

# Send a code
print('\n2. Sending test code...')
test_code = f'QUICK-TEST-{int(time.time())}'
try:
    response = requests.post(
        'https://system-main-v2.onrender.com/api/ingest',
        json={
            'username': 'bharat',
            'code': test_code,
            'source': 'quick-test-script',
            'type': 'default'
        },
        timeout=30
    )
    if response.status_code == 200:
        print(f'✅ Code sent successfully: {test_code}')
        print(f'   Response: {response.json()}')
    else:
        print(f'❌ Failed to send code: {response.status_code}')
        print(f'   Response: {response.text}')
except Exception as e:
    print(f'❌ Error sending code: {e}')

# Wait for code to be received
print('\n3. Waiting for code to be received via WebSocket...')
time.sleep(5)

# Summary
print('\n=== Summary ===')
print(f'Codes received: {len(received_codes)}')
if received_codes:
    for code_data in received_codes:
        print(f'  ✅ {code_data["code"]}')
else:
    print('  ⚠️  No codes received (may take a few seconds)')

# Disconnect
sio.disconnect()
print('\n✅ Test complete!')

