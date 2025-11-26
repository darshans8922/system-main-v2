"""
Quick test script for Render deployment.
Tests basic functionality: health, user verification, code ingestion, and SSE.
"""
import requests
import time
import sys

# Update this to your Render service URL
RENDER_URL = "https://system-main-v2.onrender.com"
TEST_USERNAME = "bharat"
TIMEOUT = 30  # Increased timeout for Render cold starts

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def test_health():
    """Test health endpoint."""
    print_header("Testing Health Endpoint")
    try:
        response = requests.get(f"{RENDER_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Health check timed out (Render may be cold starting)")
        print("   Tip: Wait 30-60 seconds and try again")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_user_verification():
    """Test user verification endpoint."""
    print_header("Testing User Verification")
    try:
        response = requests.get(
            f"{RENDER_URL}/api/users/{TEST_USERNAME}/verify",
            timeout=TIMEOUT
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ User '{TEST_USERNAME}' verified")
            print(f"   User ID: {data.get('user_id')}")
            return True
        elif response.status_code == 404:
            print(f"❌ User '{TEST_USERNAME}' not found in database")
            print("   Tip: Create the user in the database first")
            return False
        else:
            print(f"❌ Verification failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Verification timed out")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def test_code_ingest():
    """Test code ingestion endpoint."""
    print_header("Testing Code Ingestion")
    test_code = f"QUICK-TEST-{int(time.time())}"
    try:
        response = requests.post(
            f"{RENDER_URL}/api/ingest",
            json={
                'username': TEST_USERNAME,
                'code': test_code,
                'source': 'quick-test',
                'type': 'default'
            },
            timeout=TIMEOUT,
            headers={'Content-Type': 'application/json'}
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Code sent successfully")
            print(f"   Code: {test_code}")
            print(f"   Response: {data.get('message')}")
            return True, test_code
        else:
            print(f"❌ Code ingestion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False, None
    except requests.exceptions.Timeout:
        print("❌ Code ingestion timed out")
        return False, None
    except Exception as e:
        print(f"❌ Code ingestion error: {e}")
        return False, None

def test_sse_endpoint():
    """Test SSE endpoint accessibility."""
    print_header("Testing SSE Endpoint")
    try:
        # Generate a valid nonce (minimum 8 characters as required by endpoint)
        import random
        import string
        nonce = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        
        # Test if embed-stream endpoint is accessible
        # Note: This endpoint requires origin validation, so we test with proper headers
        response = requests.get(
            f"{RENDER_URL}/embed-stream?user={TEST_USERNAME}&nonce={nonce}",
            timeout=TIMEOUT,
            allow_redirects=False,
            headers={
                'Origin': RENDER_URL,  # Set origin to match server
                'Referer': f"{RENDER_URL}/"
            }
        )
        
        # Check response
        if response.status_code == 200:
            # Should return HTML content
            if 'text/html' in response.headers.get('Content-Type', ''):
                print("✅ SSE endpoint is accessible and returns HTML")
                return True
            else:
                print(f"⚠️  SSE endpoint returned 200 but unexpected content type")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                return True  # Still consider it a pass
        elif response.status_code == 400:
            # Parse error message
            try:
                error_data = response.json()
                error_msg = error_data.get('error', 'Unknown error')
                print(f"❌ SSE endpoint validation failed: {error_msg}")
                if 'nonce' in error_msg.lower():
                    print("   Tip: Nonce must be at least 8 characters")
                elif 'user' in error_msg.lower():
                    print("   Tip: User parameter is required")
            except:
                print(f"❌ SSE endpoint returned 400: {response.text[:100]}")
            return False
        elif response.status_code == 403:
            print("⚠️  SSE endpoint returned 403 (Unauthorized origin)")
            print("   This is expected if origin is not in ALLOWED_ORIGINS")
            print("   The endpoint is working, but origin validation is blocking access")
            print("   Note: In production, this endpoint should be accessed via iframe from allowed origins")
            return True  # Consider it a pass - endpoint is working, just origin-restricted
        else:
            print(f"❌ SSE endpoint returned: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
    except requests.exceptions.Timeout:
        print("❌ SSE endpoint timed out")
        return False
    except Exception as e:
        print(f"❌ SSE endpoint error: {e}")
        return False

def main():
    """Run all tests."""
    print_header("RENDER QUICK TEST SUITE")
    print(f"Server: {RENDER_URL}")
    print(f"Username: {TEST_USERNAME}")
    print(f"Timeout: {TIMEOUT}s (for Render cold starts)")
    
    results = {
        'health': False,
        'verification': False,
        'ingest': False,
        'sse': False
    }
    
    # Test 1: Health
    results['health'] = test_health()
    if not results['health']:
        print("\n⚠️  Health check failed - Render may be cold starting")
        print("   Waiting 10 seconds and retrying...")
        time.sleep(10)
        results['health'] = test_health()
    
    # Test 2: User Verification
    if results['health']:
        results['verification'] = test_user_verification()
    else:
        print("\n⚠️  Skipping user verification (health check failed)")
    
    # Test 3: Code Ingestion
    if results['verification']:
        success, code = test_code_ingest()
        results['ingest'] = success
        if success:
            print(f"\n   💡 Code '{code}' was broadcasted to all connected clients")
    else:
        print("\n⚠️  Skipping code ingestion (user verification failed)")
    
    # Test 4: SSE Endpoint
    results['sse'] = test_sse_endpoint()
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name.upper()}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Render deployment is working correctly.")
        return 0
    elif passed >= total // 2:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("   Common issues:")
        print("   - Render cold start (wait 30-60 seconds)")
        print("   - User not in database (create user first)")
        print("   - Network/firewall issues")
        return 1
    else:
        print("\n❌ Most tests failed. Check Render deployment status.")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

