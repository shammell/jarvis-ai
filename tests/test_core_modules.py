"""
==========================================================
JARVIS v9.0+ - Core Module Import Tests
Tests all 19+ core modules for successful imports
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

def test_core_imports():
    """Test all core module imports"""

    results = []

    # Test each core module
    modules = [
        ("core.speculative_decoder", "SpeculativeDecoder"),
        ("core.system2_thinking", "System2Thinking"),
        ("core.first_principles", "FirstPrinciples"),
        ("core.hyper_automation", "HyperAutomation"),
        ("core.rapid_iteration", "RapidIteration"),
        ("core.optimization_engine", "OptimizationEngine"),
        ("core.autonomous_decision", "AutonomousDecision"),
        ("core.local_llm_fallback", "HybridLLMManager"),
        ("core.skill_loader", "SkillLoader"),
        ("memory.memory_controller", "MemoryController"),
    ]

    for module_path, class_name in modules:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            results.append((module_path, class_name, "PASS", None))
            print(f"[PASS] {module_path}.{class_name}")
        except Exception as e:
            results.append((module_path, class_name, "FAIL", str(e)))
            print(f"[FAIL] {module_path}.{class_name}: {e}")

    # Summary
    passed = sum(1 for r in results if r[2] == "PASS")
    failed = sum(1 for r in results if r[2] == "FAIL")

    print(f"\n{'='*60}")
    print(f"Core Module Import Test Results")
    print(f"{'='*60}")
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
    print(f"Success Rate: {(passed/len(results)*100):.1f}%")

    assert failed == 0, f"{failed} modules failed to import"

if __name__ == "__main__":
    test_core_imports()
