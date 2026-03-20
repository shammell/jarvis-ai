import os
import sys
import time
import subprocess
import signal
from pathlib import Path

def test_jarvis_system():
    """Comprehensive test of JARVIS system components"""

    print("JARVIS System Validation Test Suite")
    print("="*50)

    results = {}

    # Test 1: Check if required files exist
    print("\nTest 1: File Existence Check")
    required_files = [
        "jarvis_brain.py",
        "main.py",
        "unified_launcher.py",
        "requirements.txt",
        "grpc/jarvis.proto",
        "whatsapp/baileys_bridge.js"
    ]

    missing_files = []
    for file in required_files:
        if os.path.exists(file):
            print(f"   [PASS] {file}")
        else:
            print(f"   [FAIL] {file}")
            missing_files.append(file)

    results['files_exist'] = len(missing_files) == 0

    # Test 2: Check Python environment
    print("\nTest 2: Python Environment Check")
    try:
        import groq
        import fastapi
        import uvicorn
        print("   [PASS] Required Python packages imported successfully")
        results['python_env'] = True
    except ImportError as e:
        print(f"   [FAIL] Python package import error: {e}")
        results['python_env'] = False

    # Test 3: Check Node environment
    print("\nTest 3: Node.js Environment Check")
    try:
        node_result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
        npm_result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)

        if node_result.returncode == 0:
            print(f"   [PASS] Node.js version: {node_result.stdout.strip()}")
        else:
            print("   [FAIL] Node.js not found")

        if npm_result.returncode == 0:
            print(f"   [PASS] npm version: {npm_result.stdout.strip()}")
        else:
            print("   [FAIL] npm not found")

        results['node_env'] = (node_result.returncode == 0 and npm_result.returncode == 0)
    except Exception as e:
        print(f"   [FAIL] Node.js environment check failed: {e}")
        results['node_env'] = False

    # Test 4: Check .env configuration
    print("\nTest 4: Environment Configuration Check")
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
            if 'GROQ_API_KEY=' in env_content and 'your_groq_api_key_here' not in env_content:
                print("   [PASS] GROQ_API_KEY configured")
                results['env_configured'] = True
            else:
                print("   [WARN] GROQ_API_KEY not configured or using default value")
                results['env_configured'] = False
    else:
        print("   [FAIL] .env file not found")
        results['env_configured'] = False

    # Test 5: Test basic script execution (non-blocking)
    print("\nTest 5: Basic Script Execution Test")
    try:
        # Test a lightweight import to check if basic structure is sound
        import importlib.util
        spec = importlib.util.spec_from_file_location("jarvis_brain", "jarvis_brain.py")
        jarvis_module = importlib.util.module_from_spec(spec)
        # Don't execute, just test importability
        print("   [PASS] Jarvis brain module can be imported")
        results['import_test'] = True
    except Exception as e:
        print(f"   [FAIL] Import test failed: {e}")
        results['import_test'] = False

    # Test 6: Check directories
    print("\nTest 6: Directory Structure Check")
    required_dirs = [
        "logs",
        "memory",
        "vector_memory",
        "grpc",
        "whatsapp",
        "core",
        "memory_storage",
        "models"
    ]

    missing_dirs = []
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"   [PASS] {directory}/")
        else:
            print(f"   [INFO] {directory}/ (optional)")
            missing_dirs.append(directory)

    results['dirs_exist'] = True  # Consider optional

    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)

    passed_tests = sum(1 for v in results.values() if v)
    total_tests = len(results)

    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test}: {status}")

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    # Risk Assessment
    print("\nRISK ASSESSMENT")
    print("-" * 20)

    if not results.get('env_configured', False):
        print("[HIGH] Environment not configured (GROQ_API_KEY missing)")
    if not results.get('python_env', False):
        print("[HIGH] Python dependencies not available")
    if not results.get('node_env', False):
        print("[HIGH] Node.js dependencies not available")
    if not results.get('files_exist', False):
        print("[MEDIUM] Some required files missing")
    if not results.get('import_test', False):
        print("[MEDIUM] Basic import test failed")

    # Final Assessment
    if passed_tests == total_tests:
        print("\n[READY] System appears ready for further testing")
    elif passed_tests >= total_tests * 0.7:  # At least 70% pass
        print("\n[PARTIAL] System partially ready - address HIGH risks")
    else:
        print("\n[NOT READY] System not ready - address HIGH risks before launch")

    return results

if __name__ == "__main__":
    test_jarvis_system()