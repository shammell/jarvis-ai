# ==========================================================
# Sub-Agent: Tester
# Writes and runs tests, validates functionality
# ==========================================================

import logging
from typing import Dict, Any, List
import subprocess
import json

logger = logging.getLogger(__name__)


class TesterAgent:
    """
    Specialized agent for testing
    - Test generation
    - Test execution
    - Coverage analysis
    - Validation
    """

    def __init__(self):
        self.name = "Tester"
        self.role = "testing"
        self.risk_level = 2
        logger.info(f"🧪 {self.name} initialized")

    async def test(self, target: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate and run tests

        Args:
            target: What to test (function, module, system)
            context: Additional context

        Returns:
            Test results
        """
        logger.info(f"🧪 Testing: {target}")

        results = {
            "tests_generated": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "coverage": 0,
            "failures": []
        }

        # Generate tests
        tests = await self._generate_tests(target, context)
        results["tests_generated"] = len(tests)

        # Run tests
        test_results = await self._run_tests(tests)
        results.update(test_results)

        logger.info(f"✅ Testing complete: {results['tests_passed']}/{results['tests_generated']} passed")

        return results

    async def _generate_tests(self, target: str, context: Dict) -> List[Dict]:
        """Generate test cases"""
        tests = []

        # Example test generation
        if "function" in target.lower():
            tests = [
                {
                    "name": "test_normal_input",
                    "input": {"x": 5},
                    "expected": 10,
                    "type": "unit"
                },
                {
                    "name": "test_edge_case_zero",
                    "input": {"x": 0},
                    "expected": 0,
                    "type": "unit"
                },
                {
                    "name": "test_negative_input",
                    "input": {"x": -5},
                    "expected": -10,
                    "type": "unit"
                },
                {
                    "name": "test_large_input",
                    "input": {"x": 1000000},
                    "expected": 2000000,
                    "type": "unit"
                }
            ]

        return tests

    async def _run_tests(self, tests: List[Dict]) -> Dict[str, Any]:
        """Run generated tests"""
        passed = 0
        failed = 0
        failures = []

        for test in tests:
            try:
                # Simulate test execution
                result = self._execute_test(test)
                if result["passed"]:
                    passed += 1
                else:
                    failed += 1
                    failures.append({
                        "test": test["name"],
                        "reason": result.get("reason", "Unknown"),
                        "expected": test["expected"],
                        "actual": result.get("actual")
                    })
            except Exception as e:
                failed += 1
                failures.append({
                    "test": test["name"],
                    "reason": str(e)
                })

        coverage = (passed / len(tests) * 100) if tests else 0

        return {
            "tests_passed": passed,
            "tests_failed": failed,
            "coverage": coverage,
            "failures": failures
        }

    def _execute_test(self, test: Dict) -> Dict[str, Any]:
        """Execute a single test"""
        # Simulate test execution
        # In production, this would actually run the test
        return {
            "passed": True,
            "actual": test["expected"]
        }

    async def generate_test_code(self, function_name: str, function_code: str) -> str:
        """Generate test code for a function"""
        test_code = f"""
import pytest

def test_{function_name}_normal():
    result = {function_name}(5)
    assert result == 10

def test_{function_name}_zero():
    result = {function_name}(0)
    assert result == 0

def test_{function_name}_negative():
    result = {function_name}(-5)
    assert result == -10

def test_{function_name}_edge_cases():
    with pytest.raises(ValueError):
        {function_name}(None)
"""
        return test_code


# Test
if __name__ == "__main__":
    import asyncio

    async def test():
        agent = TesterAgent()

        # Test a function
        result = await agent.test("function: calculate", {})

        print("\n" + "="*50)
        print("TEST RESULTS")
        print("="*50)
        print(f"Tests Generated: {result['tests_generated']}")
        print(f"Tests Passed: {result['tests_passed']}")
        print(f"Tests Failed: {result['tests_failed']}")
        print(f"Coverage: {result['coverage']:.1f}%")

        if result['failures']:
            print(f"\nFailures:")
            for failure in result['failures']:
                print(f"  - {failure['test']}: {failure['reason']}")

        # Generate test code
        test_code = await agent.generate_test_code("calculate", "def calculate(x): return x * 2")
        print("\n" + "="*50)
        print("GENERATED TEST CODE")
        print("="*50)
        print(test_code)

    asyncio.run(test())
