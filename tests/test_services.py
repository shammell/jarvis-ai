"""
==========================================================
JARVIS v9.0+ - Service Startup Tests
Tests individual service startup and health
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

import subprocess
import time
import requests
import psutil

def is_port_in_use(port):
    """Check if a port is already in use"""
    for conn in psutil.net_connections():
        if conn.laddr.port == port:
            return True
    return False

def test_main_orchestrator():
    """Test main orchestrator startup"""
    print("\n[TEST] Main Orchestrator (port 8000)")

    if is_port_in_use(8000):
        print("[INFO] Port 8000 already in use, checking if it's JARVIS...")
        try:
            resp = requests.get("http://localhost:8000/health", timeout=5)
            if resp.status_code == 200:
                print("[PASS] Main orchestrator already running and healthy")
                return True
        except:
            print("[WARN] Port 8000 in use but not responding to health check")
            return False

    print("[INFO] Starting main orchestrator...")
    print("[INFO] This test requires manual startup. Run: python main.py")
    return None

def test_grpc_server():
    """Test gRPC server startup"""
    print("\n[TEST] gRPC Server (port 50051)")

    if is_port_in_use(50051):
        print("[PASS] gRPC server is running on port 50051")
        return True
    else:
        print("[INFO] gRPC server not running. Run: python grpc_service/python_server.py")
        return None

def test_whatsapp_bridge():
    """Test WhatsApp bridge startup"""
    print("\n[TEST] WhatsApp Bridge (port 3000)")

    if is_port_in_use(3000):
        print("[INFO] Port 3000 in use, checking if it's WhatsApp bridge...")
        try:
            resp = requests.get("http://localhost:3000/health", timeout=5)
            if resp.status_code == 200:
                print("[PASS] WhatsApp bridge running and healthy")
                return True
        except:
            print("[WARN] Port 3000 in use but not responding")
            return False
    else:
        print("[INFO] WhatsApp bridge not running. Run: node whatsapp/baileys_bridge.js")
        return None

def main():
    """Run all service tests"""
    print("="*60)
    print("JARVIS v9.0+ Service Startup Tests")
    print("="*60)

    results = {
        "Main Orchestrator": test_main_orchestrator(),
        "gRPC Server": test_grpc_server(),
        "WhatsApp Bridge": test_whatsapp_bridge(),
    }

    print(f"\n{'='*60}")
    print("Service Status Summary")
    print(f"{'='*60}")

    for service, status in results.items():
        if status is True:
            print(f"[RUNNING] {service}")
        elif status is False:
            print(f"[ERROR] {service}")
        else:
            print(f"[NOT STARTED] {service}")

    running = sum(1 for s in results.values() if s is True)
    print(f"\nServices Running: {running}/{len(results)}")

if __name__ == "__main__":
    main()
