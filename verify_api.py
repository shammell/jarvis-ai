import os
import httpx
import asyncio
import json
from dotenv import load_dotenv

load_dotenv()

async def test_api_health():
    print("\n--- Testing API Health ---")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8080/health")
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
        except Exception as e:
            print(f"Error: {e} (Is the server running?)")

async def attempt_login():
    print("\n--- Attempting Admin Login ---")
    url = "http://localhost:8080/api/auth/login"
    password = os.getenv("ADMIN_PASSWORD", "admin123")
    data = {"username": "admin", "password": password}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                tokens = response.json()
                print("✅ Login Successful")
                return tokens.get("access_token")
            else:
                print(f"❌ Login Failed: {response.text}")
        except Exception as e:
            print(f"Error: {e}")
    return None

async def test_auth_me(token):
    if not token:
        return
    print("\n--- Testing /api/auth/me ---")
    url = "http://localhost:8080/api/auth/me"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Body: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

async def main():
    await test_api_health()
    token = await attempt_login()
    if token:
        await test_auth_me(token)

if __name__ == "__main__":
    asyncio.run(main())
