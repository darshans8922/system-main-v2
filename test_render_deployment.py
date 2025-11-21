"""
Test script for Render deployment.
Tests all endpoints to verify the server is running correctly.
"""
import requests
import json
import sys
from datetime import datetime

BASE_URL = "https://system-main-v2.onrender.com"
TEST_USER = "bharat"
TEST_CODE = f"RENDER-TEST-{int(datetime.now().timestamp())}"

def print_step(step_num, description):
    """Print a formatted test step."""
    print(f"\n{'='*60}")
    print(f"Step {step_num}: {description}")
    print('='*60)

def test_health():
    """Test the health endpoint."""
    print_step(1, "Health Check")
    try:
        # Increased timeout for Render free tier (can be slow)
        response = requests.get(f"{BASE_URL}/health", timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        return True
    except requests.exceptions.Timeout:
        print(f"❌ Timeout: Server took too long to respond (>30s)")
        print(f"   This might mean:")
        print(f"   - Server is still starting up (cold start on Render)")
        print(f"   - Server crashed during startup")
        print(f"   - Check Render logs for errors")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print(f"   This might mean:")
        print(f"   - Server is not running")
        print(f"   - DNS not resolving")
        print(f"   - Check Render dashboard for service status")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Status Code: {e.response.status_code}")
            print(f"   Response: {e.response.text[:200]}")
            if e.response.status_code == 502:
                print(f"   ⚠️  502 Bad Gateway usually means:")
                print(f"      - App crashed during startup")
                print(f"      - Check Render logs for DATABASE_URL errors")
                print(f"      - See RENDER_TROUBLESHOOTING.md for help")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

def test_verify_user():
    """Test user verification endpoint."""
    print_step(2, f"Verify User: {TEST_USER}")
    try:
        response = requests.get(f"{BASE_URL}/api/users/{TEST_USER}/verify", timeout=30)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def test_send_code():
    """Test sending a code via the ingest endpoint."""
    print_step(3, f"Send Test Code: {TEST_CODE}")
    try:
        payload = {
            "username": TEST_USER,
            "code": TEST_CODE,
            "source": "render-smoke-test"
        }
        response = requests.post(
            f"{BASE_URL}/api/ingest",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def test_sse_stats():
    """Test SSE stats endpoint."""
    print_step(4, "SSE Stats")
    try:
        response = requests.get(f"{BASE_URL}/sse-stats", timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Response: {json.dumps(data, indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"   Response: {e.response.text}")
        return False

def test_sse_test_page():
    """Test if SSE test page is accessible."""
    print_step(5, "SSE Test Page")
    try:
        response = requests.get(f"{BASE_URL}/sse-test", timeout=10)
        response.raise_for_status()
        print(f"✅ Status: {response.status_code}")
        print(f"✅ Page accessible (length: {len(response.text)} bytes)")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RENDER DEPLOYMENT TEST SUITE")
    print("="*60)
    print(f"Testing: {BASE_URL}")
    print(f"Test User: {TEST_USER}")
    print(f"Test Code: {TEST_CODE}")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("User Verify", test_verify_user()))
    results.append(("Send Code", test_send_code()))
    results.append(("SSE Stats", test_sse_stats()))
    results.append(("SSE Test Page", test_sse_test_page()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Server is running correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

