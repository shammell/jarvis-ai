import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def test_jarvis_jwt():
    print("\n--- Testing JARVIS Internal JWT ---")
    secret = os.getenv("JWT_SECRET")
    if not secret:
        print("[FAIL] JWT_SECRET not found in .env")
        return

    payload = {
        "user_id": "admin",
        "role": "admin",
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow()
    }

    try:
        token = jwt.encode(payload, secret, algorithm="HS256")
        print(f"[OK] Generated token: {token[:20]}...")

        decoded = jwt.decode(token, secret, algorithms=["HS256"])
        print(f"[OK] Decoded successfully: {decoded['user_id']}")
    except Exception as e:
        print(f"[FAIL] JARVIS JWT Error: {e}")

def test_supabase_jwt():
    print("\n--- Testing Supabase JWT ---")
    secret = os.getenv("SUPABASE_JWT_SECRET")
    if not secret:
        print("[FAIL] SUPABASE_JWT_SECRET not found in .env")
        return

    # Typical Supabase payload
    payload = {
        "sub": "test-user-id",
        "email": "test@example.com",
        "role": "authenticated",
        "aud": "authenticated",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }

    try:
        # Note: api/auth.py uses algorithms=["HS256"]
        token = jwt.encode(payload, secret, algorithm="HS256")
        print(f"[OK] Generated token: {token[:20]}...")

        # Simulating verify_token logic from api/auth.py
        decode_kwargs = {
            "algorithms": ["HS256"],
            "audience": "authenticated",
            "options": {"require": ["sub", "exp"]}
        }
        decoded = jwt.decode(token, secret, **decode_kwargs)
        print(f"[OK] Decoded successfully: {decoded['sub']}")
    except Exception as e:
        print(f"[FAIL] Supabase JWT Error: {e}")

if __name__ == "__main__":
    test_jarvis_jwt()
    test_supabase_jwt()
