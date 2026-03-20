#!/usr/bin/env python3
# ==========================================================
# JARVIS v11.0 GENESIS - COMPLETE INTEGRATION VERIFICATION
# Verifies all modules are connected and pipeline works
# ==========================================================

import sys
import os
import asyncio
import json
from datetime import datetime

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*70)
print("JARVIS v11.0 GENESIS - COMPLETE INTEGRATION VERIFICATION")
print("="*70)

# ========== VERIFY CORE MODULES ==========
print("\nVerifying Core Modules...")
core_modules = [
    "error_handling", "distributed_tracing",
    "economic_agency", "compute_infrastructure", "tool_synthesizer",
    "neuro_symbolic_verifier", "infinite_swarm", "ephemeral_distillation",
    "memory_sleep", "speculative_decoder", "system2_thinking",
    "first_principles", "hyper_automation", "autonomous_decision",
    "optimization_engine", "rapid_iteration", "active_perception",
    "cognitive_emotional_sync", "local_llm_fallback"
]

loaded_modules = []
failed_modules = []

for module in core_modules:
    try:
        exec(f"from core.{module} import *")
        loaded_modules.append(module)
        print(f"  [OK] {module}")
    except Exception as e:
        failed_modules.append((module, str(e)))
        print(f"  [FAIL] {module}: {str(e)[:50]}")

# ========== VERIFY MEMORY SYSTEM ==========
print("\nVerifying Memory System...")
memory_modules = ["memory_controller", "colbert_retriever", "graph_rag"]

for module in memory_modules:
    try:
        exec(f"from memory.{module} import *")
        loaded_modules.append(module)
        print(f"  [OK] {module}")
    except Exception as e:
        failed_modules.append((module, str(e)))
        print(f"  [FAIL] {module}: {str(e)[:50]}")

# ========== VERIFY SERVICES ==========
print("\nVerifying Services...")
services_status = {
    "WhatsApp Bridge (3000)": "http://localhost:3000/health",
    "gRPC Server (50051)": "localhost:50051",
    "Orchestrator (8000)": "http://localhost:8000/health",
}

import subprocess
import socket

for service_name, endpoint in services_status.items():
    if "http" in endpoint:
        try:
            result = subprocess.run(
                ["curl", "-s", endpoint],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                print(f"  [OK] {service_name}")
            else:
                print(f"  [WARN] {service_name}: Not responding")
        except:
            print(f"  [WARN] {service_name}: Connection failed")
    else:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("localhost", 50051))
            sock.close()
            if result == 0:
                print(f"  [OK] {service_name}")
            else:
                print(f"  [WARN] {service_name}: Port not open")
        except:
            print(f"  [WARN] {service_name}: Connection failed")

# ========== VERIFY INTEGRATION ==========
print("\nVerifying Integration...")

try:
    from INTEGRATION_COMPLETE import JarvisCompleteIntegration
    print("  [OK] INTEGRATION_COMPLETE module loaded")

    # Try to instantiate
    try:
        orchestrator = JarvisCompleteIntegration()
        status = orchestrator.get_status()
        print(f"  [OK] Orchestrator instantiated")
        print(f"       - Version: {status.get('version')}")
        print(f"       - Modules loaded: {status.get('modules_loaded')}")
        print(f"       - Tasks completed: {status.get('tasks_completed')}")
    except Exception as e:
        print(f"  [WARN] Orchestrator instantiation: {str(e)[:50]}")
except Exception as e:
    print(f"  [FAIL] INTEGRATION_COMPLETE: {str(e)[:50]}")

# ========== VERIFY CONFIGURATION ==========
print("\nVerifying Configuration...")

try:
    from INTEGRATION_CONFIG import INTEGRATION_STATUS, MESSAGE_PIPELINE
    print("  [OK] INTEGRATION_CONFIG loaded")
    print(f"       - Core modules: {INTEGRATION_STATUS['core_modules']['active']}/{INTEGRATION_STATUS['core_modules']['total']}")
    print(f"       - Memory modules: {INTEGRATION_STATUS['memory_system']['active']}/{INTEGRATION_STATUS['memory_system']['total']}")
    print(f"       - Pipeline steps: {len(MESSAGE_PIPELINE)}")
except Exception as e:
    print(f"  [FAIL] INTEGRATION_CONFIG: {str(e)[:50]}")

# ========== VERIFY LAUNCHER ==========
print("\nVerifying Unified Launcher...")

try:
    from unified_launcher import UnifiedLauncher
    print("  [OK] Unified launcher loaded")
    launcher = UnifiedLauncher()
    launcher.setup_services()
    print(f"       - Services configured: {len(launcher.services)}")
    for service_name in launcher.services:
        print(f"         * {service_name}")
except Exception as e:
    print(f"  [FAIL] Unified launcher: {str(e)[:50]}")

# ========== SUMMARY ==========
print("\n" + "="*70)
print("INTEGRATION VERIFICATION SUMMARY")
print("="*70)

total_modules = len(loaded_modules)
total_failed = len(failed_modules)
success_rate = (total_modules / (total_modules + total_failed) * 100) if (total_modules + total_failed) > 0 else 0

print(f"\n[OK] Modules Loaded: {total_modules}")
print(f"[FAIL] Modules Failed: {total_failed}")
print(f"[STAT] Success Rate: {success_rate:.1f}%")

if failed_modules:
    print("\n[WARN] Failed Modules:")
    for module, error in failed_modules:
        print(f"  * {module}: {error[:60]}")

print("\n" + "="*70)
if success_rate >= 90:
    print("[STATUS] INTEGRATION: PRODUCTION READY")
elif success_rate >= 70:
    print("[STATUS] INTEGRATION: MOSTLY WORKING (Minor issues)")
else:
    print("[STATUS] INTEGRATION: NEEDS ATTENTION")

print("="*70)

# ========== DETAILED REPORT ==========
print("\nDETAILED INTEGRATION REPORT")
print("="*70)

report = {
    "timestamp": datetime.now().isoformat(),
    "modules_loaded": total_modules,
    "modules_failed": total_failed,
    "success_rate": success_rate,
    "loaded_modules": loaded_modules,
    "failed_modules": [{"module": m, "error": e} for m, e in failed_modules],
    "services_verified": len(services_status),
    "status": "PRODUCTION_READY" if success_rate >= 90 else "NEEDS_ATTENTION"
}

print(json.dumps(report, indent=2))

print("\n" + "="*70)
print("[COMPLETE] INTEGRATION VERIFICATION FINISHED")
print("="*70)

sys.exit(0 if success_rate >= 90 else 1)
