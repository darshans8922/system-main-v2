"""
Helper script for testing SSE endpoints.
Run this to create test users and send test codes.
"""
import requests
import sys
import json

SERVER = "http://localhost:5000"

def create_user(username):
    """Create a test user in the database."""
    from app.database import db_session
    from app.models import User
    
    try:
        with db_session() as session:
            # Check if user exists
            existing = session.query(User).filter(User.username == username).first()
            if existing:
                print(f"✅ User '{username}' already exists (ID: {existing.id})")
                return True
            
            # Create new user
            user = User(username=username)
            session.add(user)
            session.commit()
            print(f"✅ User '{username}' created successfully!")
            return True
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False

def verify_user(username):
    """Verify if a user exists."""
    try:
        resp = requests.get(f"{SERVER}/api/users/{username}/verify")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ User '{username}' verified: {data}")
            return True
        else:
            print(f"❌ User '{username}' not found: {resp.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error verifying user: {e}")
        return False

def send_code(username, code="TEST-CODE-123", source="test-script"):
    """Send a test code via API."""
    try:
        data = {
            "username": username,
            "code": code,
            "source": source,
            "type": "default",
            "metadata": {
                "test": True
            }
        }
        
        resp = requests.post(
            f"{SERVER}/api/ingest",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"✅ Code sent successfully: {result}")
            return True
        else:
            print(f"❌ Failed to send code: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Error sending code: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_sse_helper.py create <username>     - Create a test user")
        print("  python test_sse_helper.py verify <username>    - Verify a user exists")
        print("  python test_sse_helper.py send <username> [code] - Send a test code")
        print("\nExample:")
        print("  python test_sse_helper.py create bharat")
        print("  python test_sse_helper.py verify bharat")
        print("  python test_sse_helper.py send bharat TEST-123")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 3:
            print("❌ Please provide a username")
            return
        username = sys.argv[2]
        create_user(username)
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("❌ Please provide a username")
            return
        username = sys.argv[2]
        verify_user(username)
    
    elif command == "send":
        if len(sys.argv) < 3:
            print("❌ Please provide a username")
            return
        username = sys.argv[2]
        code = sys.argv[3] if len(sys.argv) > 3 else "TEST-CODE-123"
        send_code(username, code)
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()

