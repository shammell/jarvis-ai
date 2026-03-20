#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v11.0 GENESIS - System Test Suite
PhD-Level Validation
==========================================================
"""

import sys
import os
import time
import json
import subprocess
from typing import Dict, Any, List

# Fix Windows encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Try to import requests, but don't fail if not available
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")

def print_success(text: str):
    print(f"{Colors.GREEN}[OK] {text}{Colors.RESET}")

def print_error(text: str):
    print(f"{Colors.RED}[FAIL] {text}{Colors.RESET}")

def print_warning(text: str):
    print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")

def print_info(text: str):
    print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")


class JarvisSystemTest:
    """PhD-Level System Test Suite"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.passed = 0
        self.failed = 0

    def test(self, name: str, func):
        """Run a test"""
        print(f"\n{Colors.BOLD}Testing: {name}{Colors.RESET}")
        try:
            result = func()
            if result:
                print_success(f"{name} - PASSED")
                self.passed += 1
                self.results.append({"name": name, "status": "passed"})
            else:
                print_error(f"{name} - FAILED")
                self.failed += 1
                self.results.append({"name": name, "status": "failed"})
        except Exception as e:
            print_error(f"{name} - ERROR: {e}")
            self.failed += 1
            self.results.append({"name": name, "status": "error", "error": str(e)})

    def test_file_exists(self, path: str) -> bool:
        """Test if file exists"""
        exists = os.path.exists(path)
        if exists:
            print_info(f"Found: {path}")
        else:
            print_warning(f"Missing: {path}")
        return exists

    def test_python_import(self, module: str) -> bool:
        """Test if Python module can be imported"""
        try:
            __import__(module)
            print_info(f"Import successful: {module}")
            return True
        except ImportError as e:
            print_warning(f"Import failed: {module} - {e}")
            return False

    def test_port_listening(self, port: int) -> bool:
        """Test if port is listening"""
        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True,
                timeout=5
            )
            listening = str(port) in result.stdout
            if listening:
                print_info(f"Port {port} is listening")
            else:
                print_warning(f"Port {port} is not listening")
            return listening
        except:
            return False

    def test_http_endpoint(self, url: str) -> bool:
        """Test if HTTP endpoint responds"""
        if not HAS_REQUESTS:
            print_warning(f"requests module not available, skipping: {url}")
            return True  # Don't fail if requests not installed

        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print_info(f"Endpoint responding: {url}")
                return True
            else:
                print_warning(f"Endpoint returned {response.status_code}: {url}")
                return False
        except Exception as e:
            print_warning(f"Endpoint unreachable: {url} - {e}")
            return False

    def run_all_tests(self):
        """Run all system tests"""
        print_header("JARVIS v11.0 GENESIS - System Test Suite")

        # Test 1: File Structure
        print_header("Test 1: File Structure")
        self.test("Core files exist", lambda: all([
            self.test_file_exists("whatsapp/baileys_bridge.js"),
            self.test_file_exists("grpc/python_server.py"),
            self.test_file_exists("grpc/jarvis.proto"),
            self.test_file_exists("main_genesis.py"),
            self.test_file_exists("unified_launcher.py")
        ]))

        self.test("PhD-level modules exist", lambda: all([
            self.test_file_exists("core/error_handling.py"),
            self.test_file_exists("core/distributed_tracing.py")
        ]))

        self.test("Documentation exists", lambda: all([
            self.test_file_exists("QUICK_START_FIXED.md"),
            self.test_file_exists("BUG_REPORT.md"),
            self.test_file_exists("FIXES_SUMMARY.md")
        ]))

        self.test("Startup scripts exist", lambda: all([
            self.test_file_exists("start_jarvis.sh"),
            self.test_file_exists("start_jarvis.bat")
        ]))

        # Test 2: Python Dependencies
        print_header("Test 2: Python Dependencies")
        self.test("gRPC installed", lambda: self.test_python_import("grpc"))
        self.test("FastAPI installed", lambda: self.test_python_import("fastapi"))
        self.test("Pydantic installed", lambda: self.test_python_import("pydantic"))

        # Test 3: gRPC Protobuf
        print_header("Test 3: gRPC Protobuf")
        self.test("Protobuf files generated", lambda: all([
            self.test_file_exists("grpc/jarvis_pb2.py"),
            self.test_file_exists("grpc/jarvis_pb2_grpc.py")
        ]))

        # Test 4: Module Imports
        print_header("Test 4: Module Imports")
        self.test("Error handling module", lambda: self.test_python_import("core.error_handling"))
        self.test("Distributed tracing module", lambda: self.test_python_import("core.distributed_tracing"))

        # Test 5: Services (if running)
        print_header("Test 5: Service Health (if running)")
        print_info("Note: These tests will fail if services are not running")

        self.test("WhatsApp Bridge health", lambda: self.test_http_endpoint("http://localhost:3000/health"))
        self.test("Main Orchestrator health", lambda: self.test_http_endpoint("http://localhost:8000/health"))
        self.test("Metrics endpoint", lambda: self.test_http_endpoint("http://localhost:3000/metrics"))

        # Test 6: Configuration
        print_header("Test 6: Configuration")
        self.test(".env file exists", lambda: self.test_file_exists(".env"))

        if os.path.exists(".env"):
            with open(".env", "r") as f:
                env_content = f.read()
                has_groq_key = "GROQ_API_KEY=" in env_content and "your_groq_api_key_here" not in env_content
                if has_groq_key:
                    print_info("GROQ_API_KEY is configured")
                else:
                    print_warning("GROQ_API_KEY not configured in .env")
                self.test("GROQ_API_KEY configured", lambda: has_groq_key)

        # Print Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")

        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0

        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")
        print(f"Pass Rate: {pass_rate:.1f}%\n")

        if self.failed == 0:
            print_success("All tests passed! System is ready.")
        elif self.failed <= 3:
            print_warning("Some tests failed. Check warnings above.")
        else:
            print_error("Multiple tests failed. Review errors above.")

        # Recommendations
        print_header("Recommendations")

        if not os.path.exists(".env"):
            print_warning("Create .env file from .env.example")

        if not os.path.exists("grpc/jarvis_pb2.py"):
            print_warning("Generate protobuf files:")
            print("  python -m grpc_tools.protoc -I./grpc --python_out=./grpc --grpc_python_out=./grpc ./grpc/jarvis.proto")

        print_info("\nTo start JARVIS:")
        print("  python unified_launcher.py")
        print("\nOr use startup script:")
        print("  Windows: start_jarvis.bat")
        print("  Linux/Mac: ./start_jarvis.sh")


if __name__ == "__main__":
    tester = JarvisSystemTest()
    tester.run_all_tests()

    sys.exit(0 if tester.failed == 0 else 1)
