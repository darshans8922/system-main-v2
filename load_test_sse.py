"""
Load testing script for SSE connections.
Tests multiple concurrent connections to verify system can handle scale.
"""
import socketio
import requests
import time
import threading
import random
import string
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

SERVER = "https://system-main-v2.onrender.com"
USERNAME = "bharat"
NUM_CONNECTIONS = 50  # Number of concurrent connections to test
CODES_TO_SEND = 10    # Number of codes to send during test
TEST_DURATION = 60    # Test duration in seconds

class SSELoadTester:
    def __init__(self, server, username, connection_id):
        self.server = server
        self.username = username
        self.connection_id = connection_id
        self.sio = socketio.Client()
        self.received_codes = []
        self.connected = False
        self.errors = []
        self.start_time = None
        self.end_time = None
        
    def connect(self):
        """Connect to WebSocket."""
        try:
            self.start_time = time.time()
            self.sio.connect(
                f"{self.server}/events?username={self.username}",
                wait_timeout=30,
                transports=['websocket', 'polling']
            )
            self.connected = True
            return True
        except Exception as e:
            self.errors.append(f"Connection failed: {e}")
            return False
    
    def setup_handlers(self):
        """Setup event handlers."""
        @self.sio.on('connect', namespace='/events')
        def on_connect():
            self.connected = True
        
        @self.sio.on('new_code')
        def on_code(data):
            self.received_codes.append({
                'code': data.get('code'),
                'timestamp': time.time(),
                'connection_id': self.connection_id
            })
        
        @self.sio.on('error')
        def on_error(error):
            self.errors.append(f"WebSocket error: {error}")
    
    def disconnect(self):
        """Disconnect from WebSocket."""
        try:
            if self.sio.connected:
                self.sio.disconnect()
            self.end_time = time.time()
        except Exception as e:
            self.errors.append(f"Disconnect error: {e}")
    
    def get_stats(self):
        """Get connection statistics."""
        duration = (self.end_time or time.time()) - (self.start_time or time.time())
        return {
            'connection_id': self.connection_id,
            'connected': self.connected,
            'codes_received': len(self.received_codes),
            'errors': len(self.errors),
            'duration': duration,
            'error_messages': self.errors[:5]  # First 5 errors
        }


def send_test_code(server, username, code_num):
    """Send a test code via HTTP API."""
    try:
        code = f"LOAD-TEST-{code_num}-{int(time.time())}"
        response = requests.post(
            f"{server}/api/ingest",
            json={
                'username': username,
                'code': code,
                'source': 'load-test',
                'type': 'default'
            },
            timeout=30
        )
        return {
            'success': response.status_code == 200,
            'code': code,
            'status': response.status_code
        }
    except Exception as e:
        return {
            'success': False,
            'code': None,
            'error': str(e)
        }


def run_load_test(num_connections=50, codes_to_send=10, duration=60):
    """Run load test with multiple concurrent connections."""
    print("=" * 70)
    print("SSE LOAD TEST")
    print("=" * 70)
    print(f"Server: {SERVER}")
    print(f"Username: {USERNAME}")
    print(f"Connections: {num_connections}")
    print(f"Test Duration: {duration} seconds")
    print(f"Codes to Send: {codes_to_send}")
    print("=" * 70)
    print()
    
    # Create testers
    testers = []
    for i in range(num_connections):
        tester = SSELoadTester(SERVER, USERNAME, i + 1)
        tester.setup_handlers()
        testers.append(tester)
    
    # Phase 1: Connect all clients
    print("Phase 1: Connecting clients...")
    connected_count = 0
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {executor.submit(tester.connect): tester for tester in testers}
        for future in as_completed(futures):
            tester = futures[future]
            try:
                if future.result():
                    connected_count += 1
                    if connected_count % 10 == 0:
                        print(f"  Connected: {connected_count}/{num_connections}")
            except Exception as e:
                print(f"  Connection error for tester {tester.connection_id}: {e}")
    
    print(f"\n✅ Connected: {connected_count}/{num_connections} clients")
    time.sleep(2)  # Wait for all connections to stabilize
    
    # Phase 2: Send codes and monitor
    print(f"\nPhase 2: Sending {codes_to_send} codes and monitoring...")
    start_time = time.time()
    codes_sent = []
    
    # Send codes in background
    def send_codes_loop():
        for i in range(codes_to_send):
            result = send_test_code(SERVER, USERNAME, i + 1)
            codes_sent.append(result)
            if result['success']:
                print(f"  📤 Sent code {i+1}/{codes_to_send}: {result['code']}")
            else:
                print(f"  ❌ Failed to send code {i+1}: {result.get('error', result.get('status'))}")
            time.sleep(max(1, duration / codes_to_send))  # Spread codes over duration
    
    send_thread = threading.Thread(target=send_codes_loop, daemon=True)
    send_thread.start()
    
    # Monitor for duration
    elapsed = 0
    while elapsed < duration and send_thread.is_alive():
        time.sleep(5)
        elapsed = time.time() - start_time
        total_received = sum(len(t.received_codes) for t in testers)
        print(f"  ⏱️  {int(elapsed)}s - Total codes received: {total_received}")
    
    # Wait for send thread to finish
    send_thread.join(timeout=10)
    
    # Phase 3: Disconnect and collect stats
    print("\nPhase 3: Disconnecting and collecting statistics...")
    for tester in testers:
        tester.disconnect()
    
    time.sleep(2)  # Wait for disconnections
    
    # Collect statistics
    stats = {
        'total_connections': num_connections,
        'connected': sum(1 for t in testers if t.connected),
        'total_codes_received': sum(len(t.received_codes) for t in testers),
        'total_errors': sum(len(t.errors) for t in testers),
        'codes_sent': len([c for c in codes_sent if c['success']]),
        'codes_sent_failed': len([c for c in codes_sent if not c['success']]),
        'connection_stats': [t.get_stats() for t in testers]
    }
    
    # Calculate distribution
    codes_per_connection = defaultdict(int)
    for tester in testers:
        codes_per_connection[len(tester.received_codes)] += 1
    
    # Print results
    print("\n" + "=" * 70)
    print("LOAD TEST RESULTS")
    print("=" * 70)
    print(f"Total Connections Attempted: {stats['total_connections']}")
    print(f"Successfully Connected: {stats['connected']} ({stats['connected']/stats['total_connections']*100:.1f}%)")
    print(f"Codes Sent: {stats['codes_sent']} (Failed: {stats['codes_sent_failed']})")
    print(f"Total Codes Received: {stats['total_codes_received']}")
    print(f"Average Codes per Connection: {stats['total_codes_received']/max(stats['connected'], 1):.2f}")
    print(f"Total Errors: {stats['total_errors']}")
    
    if codes_per_connection:
        print(f"\nCodes Distribution:")
        for count, num_connections in sorted(codes_per_connection.items()):
            print(f"  {count} codes: {num_connections} connections")
    
    # Show connection details
    print(f"\nConnection Details:")
    avg_duration = sum(s['duration'] for s in stats['connection_stats'] if s['duration'] > 0) / max(len([s for s in stats['connection_stats'] if s['duration'] > 0]), 1)
    print(f"  Average Connection Duration: {avg_duration:.2f}s")
    
    # Show errors if any
    error_testers = [t for t in testers if t.errors]
    if error_testers:
        print(f"\n⚠️  Connections with Errors: {len(error_testers)}")
        for tester in error_testers[:5]:  # Show first 5
            print(f"  Connection {tester.connection_id}: {tester.errors[0]}")
    
    print("=" * 70)
    
    return stats


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    num_conn = NUM_CONNECTIONS
    codes = CODES_TO_SEND
    duration = TEST_DURATION
    
    if len(sys.argv) > 1:
        num_conn = int(sys.argv[1])
    if len(sys.argv) > 2:
        codes = int(sys.argv[2])
    if len(sys.argv) > 3:
        duration = int(sys.argv[3])
    
    print(f"\nStarting load test with {num_conn} connections...")
    print("Press Ctrl+C to stop early\n")
    
    try:
        stats = run_load_test(num_conn, codes, duration)
        
        # Summary
        success_rate = stats['connected'] / stats['total_connections'] * 100
        if success_rate >= 95:
            print("\n✅ PASS: Load test successful (>95% connection rate)")
        elif success_rate >= 80:
            print("\n⚠️  WARNING: Some connection issues (<95% connection rate)")
        else:
            print("\n❌ FAIL: Significant connection issues (<80% connection rate)")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

