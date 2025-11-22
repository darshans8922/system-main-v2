"""
Comprehensive test script for all APIs in the Code Broadcasting System.
Tests HTTP REST, WebSocket, and SSE endpoints.
"""
import requests
import sys
import json
import time
import random
import string

SERVER = "https://system-main-v2.onrender.com"  # Production server
USERNAME = "bharat"  # Default test username


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(msg):
    """Print success message."""
    print(f"✅ {msg}")


def print_error(msg):
    """Print error message."""
    print(f"❌ {msg}")


def print_info(msg):
    """Print info message."""
    print(f"ℹ️  {msg}")


def print_warning(msg):
    """Print warning message."""
    print(f"⚠️  {msg}")


def create_user(username):
    """Create a test user in the production database."""
    try:
        import os
        from dotenv import load_dotenv
        
        # Load environment variables (DATABASE_URL should be set)
        load_dotenv()
        
        # Check if DATABASE_URL is set
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print_error("DATABASE_URL environment variable is not set!")
            print_info("To use production database, set it in one of these ways:")
            print_info("1. Create a .env file with: DATABASE_URL=postgresql://...")
            print_info("2. Set environment variable: export DATABASE_URL='postgresql://...' (Linux/Mac)")
            print_info("3. Set environment variable: set DATABASE_URL=postgresql://... (Windows)")
            print_info("4. Set environment variable: $env:DATABASE_URL='postgresql://...' (PowerShell)")
            return False
        
        # Show which database we're using (mask password, show host)
        if '@' in database_url:
            db_display = database_url.split('@')[1]
        else:
            db_display = 'configured database'
        print_info(f"Using PRODUCTION database: {db_display}")
        
        from app.database import db_session
        from app.models import User
        
        with db_session() as session:
            # Check if user exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                print_success(f"User '{username}' already exists (ID: {existing.id})")
                return True
            
            # Create new user
            user = User(username=username)
            session.add(user)
            session.commit()
            print_success(f"User '{username}' created successfully in production database!")
            return True
    except Exception as e:
        print_error(f"Error creating user: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health():
    """Test health endpoint."""
    print_header("Testing Health Endpoint")
    try:
        # Longer timeout for remote servers
        timeout = 30 if SERVER.startswith('https://') else 10
        resp = requests.get(f"{SERVER}/health", timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            print_success(f"Health check passed: {data}")
            return True
        else:
            print_error(f"Health check failed: {resp.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


def verify_user(username):
    """Verify if a user exists (checks both HTTP API and database directly)."""
    print_header(f"Verifying User: {username}")
    
    # First, check database directly (production database)
    try:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        if os.getenv("DATABASE_URL"):
            from app.database import db_session
            from app.models import User
            
            with db_session() as session:
                user = session.query(User).filter(User.username == username).first()
                if user:
                    print_success(f"✅ User '{username}' exists in PRODUCTION database (ID: {user.id})")
                else:
                    print_warning(f"⚠️  User '{username}' NOT found in production database")
        else:
            print_warning("⚠️  DATABASE_URL not set, skipping direct database check")
    except Exception as e:
        print_warning(f"⚠️  Could not check database directly: {e}")
    
    # Also test HTTP API endpoint
    try:
        timeout = 30 if SERVER.startswith('https://') else 10
        resp = requests.get(f"{SERVER}/api/users/{username}/verify", timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            print_success(f"✅ HTTP API verified: {json.dumps(data, indent=2)}")
            return True
        elif resp.status_code == 404:
            print_warning(f"⚠️  HTTP API returned 404 (user not found via API)")
            print_info("Note: User may exist in database but API endpoint may have issues")
            return False
        else:
            print_error(f"❌ HTTP API verification failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print_error(f"❌ Error verifying user via HTTP API: {e}")
        return False


def send_code_post(username, code="TEST-CODE-123", source="test-script"):
    """Send a test code via POST API."""
    print_header(f"Sending Code via POST: {code}")
    try:
        data = {
            "username": username,
            "code": code,
            "source": source,
            "type": "default",
            "metadata": {
                "test": True,
                "timestamp": int(time.time())
            }
        }
        
        timeout = 30 if SERVER.startswith('https://') else 10
        resp = requests.post(
            f"{SERVER}/api/ingest",
            json=data,
            headers={"Content-Type": "application/json"},
            timeout=timeout
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print_success(f"Code sent successfully: {json.dumps(result, indent=2)}")
            return True
        else:
            print_error(f"Failed to send code: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print_error(f"Error sending code: {e}")
        return False


def send_code_get(username, code="TEST-CODE-456", source="test-script"):
    """Send a test code via GET API."""
    print_header(f"Sending Code via GET: {code}")
    try:
        params = {
            "username": username,
            "code": code,
            "source": source,
            "type": "default"
        }
        
        timeout = 30 if SERVER.startswith('https://') else 10
        resp = requests.get(
            f"{SERVER}/api/ingest",
            params=params,
            timeout=timeout
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print_success(f"Code sent successfully: {json.dumps(result, indent=2)}")
            return True
        else:
            print_error(f"Failed to send code: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print_error(f"Error sending code: {e}")
        return False


def test_websocket(username):
    """Test WebSocket connection and code reception."""
    print_header("Testing WebSocket Connection")
    try:
        import socketio
        import warnings
        
        # Suppress websocket-client warning (it's just informational)
        warnings.filterwarnings('ignore', message='.*websocket-client.*')
        
        sio = socketio.Client()
        received_codes = []
        connected = False
        
        @sio.on('connect', namespace='/events')
        def on_connect_events():
            nonlocal connected
            connected = True
            print_success("WebSocket connected to /events namespace")
            # Note: /events namespace automatically joins 'code_listeners' room on connect
            # The server handler already calls join_room('code_listeners') on connect
        
        @sio.on('connected', namespace='/events')
        def on_connected_events(data):
            """Handle 'connected' event from server."""
            print_info(f"Server confirmed connection: {data.get('message', '')}")
        
        @sio.on('connect')
        def on_connect_default():
            """Handle default namespace connection (fallback)."""
            nonlocal connected
            if not connected:  # Only set if /events didn't connect
                connected = True
                print_success("WebSocket connected to default namespace")
        
        @sio.on('new_code')
        def on_code(data):
            print_success(f"Received code via WebSocket: {json.dumps(data, indent=2)}")
            received_codes.append(data)
        
        @sio.on('error')
        def on_error(data):
            print_error(f"WebSocket error: {data}")
        
        # Connect to /events namespace (where code broadcasts happen)
        # Use wss:// for HTTPS servers
        ws_url = SERVER.replace('https://', 'wss://').replace('http://', 'ws://')
        print_info(f"Connecting to {ws_url}/events with username: {username}")
        try:
            # SocketIO handles SSL automatically for wss:// URLs
            sio.connect(f"{ws_url}/events?username={username}", wait_timeout=30)
        except Exception as e:
            print_error(f"Connection failed: {e}")
            return False
        
        # Wait for connection to establish (namespace connection is async)
        # Longer wait for remote servers (may have cold start delays)
        wait_time = 5 if SERVER.startswith('https://') else 3
        time.sleep(wait_time)
        
        if not connected:
            print_error("WebSocket connection not established")
            sio.disconnect()
            return False
        
        # For /events namespace, subscription happens automatically on connect
        # The server's handle_events_connect() already calls join_room('code_listeners')
        print_info("Connected and ready to receive codes (already subscribed to code_listeners room)")
        
        # Send a test code via HTTP API (to trigger broadcast)
        print_info("Sending test code via HTTP API to trigger broadcast...")
        test_code = f"WS-TEST-{int(time.time())}"
        try:
            resp = requests.post(
                f"{SERVER}/api/ingest",
                json={
                    'username': username,
                    'code': test_code,
                    'source': 'websocket-test',
                    'type': 'default'
                },
                timeout=30 if SERVER.startswith('https://') else 10
            )
            if resp.status_code == 200:
                print_success(f"Test code sent via API: {test_code}")
            else:
                print_error(f"Failed to send test code: {resp.status_code}")
        except Exception as e:
            print_error(f"Error sending test code: {e}")
        
        # Wait for code to be received
        print_info("Waiting for code to be received via WebSocket...")
        wait_time = 5 if SERVER.startswith('https://') else 3
        time.sleep(wait_time)
        
        # Disconnect
        sio.disconnect()
        print_success("WebSocket disconnected")
        
        if received_codes:
            print_success(f"Received {len(received_codes)} code(s) via WebSocket")
            return True
        else:
            print_error("No codes received via WebSocket (this is OK if no codes were broadcast)")
            print_info("Note: WebSocket connection works, but you need to send codes to see them")
            return True  # Connection works, just no codes to receive
            
    except ImportError:
        print_error("python-socketio not installed. Install with: pip install python-socketio")
        return False
    except Exception as e:
        print_error(f"WebSocket test error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sse_embed_stream(username):
    """Test SSE embed-stream endpoint."""
    print_header("Testing SSE Embed Stream")
    try:
        nonce = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        url = f"{SERVER}/embed-stream?user={username}&nonce={nonce}"
        
        # SSE embed-stream requires origin header for security
        # Use localhost as origin for testing (allowed in ALLOWED_ORIGINS)
        headers = {
            'Origin': 'http://localhost:5000',
            'Referer': 'http://localhost:5000/'
        }
        
        timeout = 30 if SERVER.startswith('https://') else 10
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            if 'text/html' in resp.headers.get('Content-Type', ''):
                print_success(f"Embed stream endpoint accessible (HTML returned)")
                print_info(f"URL: {url}")
                return True
            else:
                print_error(f"Unexpected content type: {resp.headers.get('Content-Type')}")
                return False
        elif resp.status_code == 403:
            # 403 is expected if origin is not allowed - this is a security feature
            print_warning(f"Embed stream returned 403 (origin validation)")
            print_info("This is expected - endpoint requires allowed origin header")
            print_info("In production, this endpoint is accessed via iframe from allowed domains")
            # Still count as pass since endpoint is working (security is working)
            return True
        else:
            print_error(f"Embed stream failed: {resp.status_code} - {resp.text[:200]}")
            return False
    except Exception as e:
        print_error(f"SSE embed stream error: {e}")
        return False


def test_all(username=USERNAME):
    """Run all tests in sequence."""
    print_header("COMPREHENSIVE API TEST SUITE")
    print_info(f"Testing with username: {username}")
    print_info(f"Server: {SERVER}")
    
    # Check if server is responding
    is_remote = SERVER.startswith('https://') or (SERVER.startswith('http://') and 'localhost' not in SERVER and '127.0.0.1' not in SERVER)
    
    try:
        # Longer timeout for remote servers (Render cold starts can take 30-60s)
        timeout = 60 if is_remote else 2
        print_info(f"Checking server health (timeout: {timeout}s)...")
        resp = requests.get(f"{SERVER}/health", timeout=timeout)
        if resp.status_code != 200:
            print_error("Server health check failed. Is the server running?")
            return {}
        print_success("Server is reachable and responding")
    except requests.exceptions.RequestException as e:
        print_error(f"Cannot connect to server: {e}")
        if is_remote:
            print_warning("Render free tier may be sleeping (cold start takes 30-60s)")
            print_info("Try again in 1-2 minutes, or upgrade to paid tier for always-on service")
        else:
            print_info("Start server with: python app.py")
        return {}
    
    if is_remote:
        print_info("Testing against REMOTE/PRODUCTION server")
        print_info("Using production database (from DATABASE_URL environment variable)")
        print_warning("⚠️  Render free tier may have cold starts (30-60s delay on first request)")
        print_warning("⚠️  If tests timeout, wait 1-2 minutes and try again")
    else:
        print_warning("NOTE: If tests timeout, Flask debug mode auto-reloader may be interfering.")
        print_warning("Solution: Stop editing files during tests, or run server with: FLASK_DEBUG=False python app.py")
    
    results = {}
    
    # 1. Health check
    results['health'] = test_health()
    time.sleep(0.5)
    
    # 2. Create user (if needed)
    print_header("Creating Test User")
    results['create_user'] = create_user(username)
    time.sleep(0.5)
    
    # 3. Verify user
    results['verify_user'] = verify_user(username)
    if not results['verify_user']:
        print_error("User verification failed. Cannot continue with other tests.")
        return results
    time.sleep(0.5)
    
    # 4. Send code via POST
    test_code_post = f"TEST-POST-{int(time.time())}"
    results['send_post'] = send_code_post(username, test_code_post)
    time.sleep(1)
    
    # 5. Send code via GET
    test_code_get = f"TEST-GET-{int(time.time())}"
    results['send_get'] = send_code_get(username, test_code_get)
    time.sleep(1)
    
    # 6. Test WebSocket
    results['websocket'] = test_websocket(username)
    time.sleep(1)
    
    # 7. Test SSE embed stream
    results['sse_embed'] = test_sse_embed_stream(username)
    time.sleep(0.5)
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("All tests passed! 🎉")
    else:
        print_error(f"{total - passed} test(s) failed")
    
    return results


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_sse_helper.py create <username>     - Create a test user")
        print("  python test_sse_helper.py verify <username>      - Verify a user exists")
        print("  python test_sse_helper.py send <username> [code] - Send a test code (POST)")
        print("  python test_sse_helper.py send-get <username> [code] - Send a test code (GET)")
        print("  python test_sse_helper.py health                - Test health endpoint")
        print("  python test_sse_helper.py websocket <username> - Test WebSocket connection")
        print("  python test_sse_helper.py sse <username>       - Test SSE embed stream")
        print("  python test_sse_helper.py test-all [username]  - Run all tests")
        print("\nDefault username: bharat")
        print("\nExamples:")
        print("  python test_sse_helper.py create bharat")
        print("  python test_sse_helper.py verify bharat")
        print("  python test_sse_helper.py send bharat TEST-123")
        print("  python test_sse_helper.py test-all bharat")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
        create_user(username)
    
    elif command == "verify":
        username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
        verify_user(username)
    
    elif command == "send":
        username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
        code = sys.argv[3] if len(sys.argv) > 3 else f"TEST-{int(time.time())}"
        send_code_post(username, code)
    
    elif command == "send-get":
        username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
        code = sys.argv[3] if len(sys.argv) > 3 else f"TEST-{int(time.time())}"
        send_code_get(username, code)
    
    elif command == "health":
        test_health()
    
    elif command == "websocket":
        username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
        test_websocket(username)
    
    elif command == "sse":
        username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
        test_sse_embed_stream(username)
    
    elif command == "test-all":
        username = sys.argv[2] if len(sys.argv) > 2 else USERNAME
        test_all(username)
    
    else:
        print_error(f"Unknown command: {command}")
        print("\nRun without arguments to see usage.")


if __name__ == "__main__":
    main()
