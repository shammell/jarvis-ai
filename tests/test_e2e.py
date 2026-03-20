"""
==========================================================
JARVIS v9.0+ - End-to-End Integration Test
Tests complete system workflow via API endpoints
==========================================================
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

import asyncio
import httpx
import pytest

BASE_URL = "http://localhost:8000"

@pytest.mark.asyncio
async def test_health_check():
    """Test health endpoint"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        print(f"[PASS] Health check: {data}")

@pytest.mark.asyncio
async def test_system_stats():
    """Test system stats endpoint"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/stats")
        assert resp.status_code == 200
        stats = resp.json()
        assert "version" in stats
        print(f"[PASS] System stats: version={stats.get('version')}")

@pytest.mark.asyncio
async def test_simple_message():
    """Test simple message processing"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BASE_URL}/api/message",
            json={"message": "What is 2+2?", "user_id": "test_user"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "text" in data
        print(f"[PASS] Simple message response: {data['text'][:100]}...")

@pytest.mark.asyncio
async def test_first_principles():
    """Test first principles analysis"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{BASE_URL}/api/first-principles",
            json={"message": "How does a battery work?"}
        )
        assert resp.status_code == 200
        data = resp.json()
        print(f"[PASS] First principles analysis completed")

@pytest.mark.asyncio
async def test_automations():
    """Test automation suggestions"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/automations")
        assert resp.status_code == 200
        data = resp.json()
        print(f"[PASS] Automations endpoint: {len(data.get('automations', []))} suggestions")

@pytest.mark.asyncio
async def test_decision_making():
    """Test autonomous decision making"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/decision",
            json={
                "action": "test_action",
                "context": {"risk": "low"},
                "confidence": 0.8
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "approved" in data
        print(f"[PASS] Decision making: approved={data.get('approved')}")

async def run_all_tests():
    """Run all E2E tests"""
    print("\n" + "="*60)
    print("JARVIS v9.0+ End-to-End Integration Tests")
    print("="*60 + "\n")

    tests = [
        ("Health Check", test_health_check),
        ("System Stats", test_system_stats),
        ("Simple Message", test_simple_message),
        ("First Principles", test_first_principles),
        ("Automations", test_automations),
        ("Decision Making", test_decision_making),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"\nRunning: {name}...")
            await test_func()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"E2E Test Results")
    print(f"{'='*60}")
    print(f"Total: {len(tests)} | Passed: {passed} | Failed: {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")

    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
