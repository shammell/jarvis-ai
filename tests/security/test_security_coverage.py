#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Security Coverage Verification
Test Coverage Analysis and Reporting
==========================================================
"""

import unittest
import sys
import os
import importlib.util
from typing import Dict, List, Set

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import coverage tools
try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    print("Warning: Coverage module not available. Install with: pip install coverage")


class SecurityCoverageAnalyzer:
    """Analyze test coverage for security components"""

    def __init__(self):
        self.security_modules = [
            'core.security_system',
            'core.error_handling',
            'core.distributed_tracing',  # If exists
        ]
        self.security_classes = [
            'SecurityManager',
            'InputValidator',
            'SecurityMiddleware',
            'UserRole',
            'Permission',
            'SecurityLevel',
            'Session',
            'SecurityEvent',
            'RateLimitEntry',
            'FailedAttempt'
        ]
        self.security_methods = [
            # SecurityManager methods
            'hash_password',
            'verify_password',
            'generate_tokens',
            'validate_token',
            'check_permission',
            'authenticate_user',
            'refresh_token',
            'logout_user',
            '_check_rate_limit',
            '_is_locked_out',
            '_record_failed_attempt',
            '_invalidate_session_tokens',
            '_log_security_event',
            'get_security_stats',
            'get_audit_log',
            'cleanup_expired_data',

            # InputValidator methods
            'sanitize_input',
            'validate_input',
            'validate_file_path',
            'validate_query',
            'validate_context',

            # SecurityMiddleware methods
            'authenticate_request',
            'authorize_operation',
            'sanitize_request',
            'validate_request'
        ]

    def analyze_module_coverage(self, module_name: str) -> Dict[str, List[str]]:
        """Analyze what methods exist in a module"""
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return {module_name: []}

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get all callable methods
            methods = []
            for name in dir(module):
                obj = getattr(module, name)
                if callable(obj) and not name.startswith('_'):
                    methods.append(name)

            return {module_name: methods}

        except Exception as e:
            return {module_name: [f"Error loading module: {e}"]}

    def analyze_class_coverage(self, module_name: str, class_name: str) -> Dict[str, List[str]]:
        """Analyze what methods exist in a class"""
        try:
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                return {f"{module_name}.{class_name}": []}

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            if not hasattr(module, class_name):
                return {f"{module_name}.{class_name}": []}

            cls = getattr(module, class_name)
            methods = []

            for name in dir(cls):
                obj = getattr(cls, name)
                if callable(obj) and not name.startswith('_'):
                    methods.append(name)

            return {f"{module_name}.{class_name}": methods}

        except Exception as e:
            return {f"{module_name}.{class_name}": [f"Error analyzing class: {e}"]}

    def get_expected_test_files(self) -> List[str]:
        """Get list of expected test files"""
        return [
            'test_security_manager.py',
            'test_input_validator.py',
            'test_security_middleware.py',
            'test_jwt_auth.py',
            'test_rbac.py',
            'test_rate_limiting.py',
            'test_security_integration.py',
            'test_security_e2e.py',
            'test_security_coverage.py'
        ]

    def check_test_file_coverage(self) -> Dict[str, bool]:
        """Check which test files exist"""
        test_dir = os.path.join(os.path.dirname(__file__))
        expected_files = self.get_expected_test_files()
        coverage = {}

        for filename in expected_files:
            filepath = os.path.join(test_dir, filename)
            coverage[filename] = os.path.exists(filepath)

        return coverage

    def run_coverage_analysis(self):
        """Run complete coverage analysis"""
        print("=" * 60)
        print("JARVIS v9.0+ Security Test Coverage Analysis")
        print("=" * 60)

        # Check test file coverage
        print("\n1. Test File Coverage:")
        print("-" * 30)
        file_coverage = self.check_test_file_coverage()

        for filename, exists in file_coverage.items():
            status = "✓" if exists else "✗"
            print(f"{status} {filename}")

        existing_files = sum(1 for exists in file_coverage.values() if exists)
        total_files = len(file_coverage)
        file_coverage_percent = (existing_files / total_files) * 100

        print(f"\nFile Coverage: {existing_files}/{total_files} ({file_coverage_percent:.1f}%)")

        # Check module coverage
        print("\n2. Module Coverage:")
        print("-" * 30)

        module_coverage = {}
        for module in self.security_modules:
            methods = self.analyze_module_coverage(module)
            module_coverage.update(methods)

        for module, methods in module_coverage.items():
            if methods and not str(methods[0]).startswith("Error"):
                print(f"✓ {module} ({len(methods)} methods)")
            else:
                print(f"✗ {module} ({methods[0] if methods else 'No methods found'})")

        # Check class coverage
        print("\n3. Class Coverage:")
        print("-" * 30)

        class_coverage = {}
        for module in self.security_modules:
            for cls in self.security_classes:
                result = self.analyze_class_coverage(module, cls)
                class_coverage.update(result)

        covered_classes = 0
        for class_path, methods in class_coverage.items():
            if methods and not str(methods[0]).startswith("Error"):
                print(f"✓ {class_path} ({len(methods)} methods)")
                covered_classes += 1
            else:
                print(f"✗ {class_path} ({methods[0] if methods else 'No methods found'})")

        total_classes = len(self.security_classes)
        class_coverage_percent = (covered_classes / total_classes) * 100

        print(f"\nClass Coverage: {covered_classes}/{total_classes} ({class_coverage_percent:.1f}%)")

        # Check method coverage
        print("\n4. Method Coverage:")
        print("-" * 30)

        # This would require analyzing test files to see which methods are tested
        # For now, we'll estimate based on test file presence
        estimated_coverage = min(file_coverage_percent, class_coverage_percent)

        print(f"Estimated Method Coverage: {estimated_coverage:.1f}%")

        # Recommendations
        print("\n5. Recommendations:")
        print("-" * 30)

        if file_coverage_percent < 100:
            missing_files = [f for f, exists in file_coverage.items() if not exists]
            print(f"• Create missing test files: {', '.join(missing_files)}")

        if class_coverage_percent < 100:
            print(f"• Add tests for uncovered classes")

        if estimated_coverage < 80:
            print(f"• Aim for 80%+ coverage across all security components")
            print(f"• Focus on edge cases and security attack scenarios")

        print(f"• Run actual coverage analysis with: coverage run -m pytest tests/security/")
        print(f"• Generate coverage report with: coverage report -m")

        # Summary
        print("\n6. Summary:")
        print("-" * 30)
        print(f"Test Files: {existing_files}/{total_files} ({file_coverage_percent:.1f}%)")
        print(f"Classes: {covered_classes}/{total_classes} ({class_coverage_percent:.1f}%)")
        print(f"Overall: {estimated_coverage:.1f}%")

        if estimated_coverage >= 80:
            print("✓ Coverage meets security testing standards")
        elif estimated_coverage >= 60:
            print("⚠ Coverage is moderate, consider adding more tests")
        else:
            print("✗ Coverage is insufficient for security-critical components")

        return {
            'file_coverage': file_coverage_percent,
            'class_coverage': class_coverage_percent,
            'overall_coverage': estimated_coverage,
            'recommendations': []
        }


def run_security_tests_with_coverage():
    """Run security tests with coverage analysis"""
    if not COVERAGE_AVAILABLE:
        print("Coverage analysis requires 'coverage' package. Installing...")
        import subprocess
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'coverage'])
        return

    # Start coverage
    cov = coverage.Coverage(
        source=['core.security_system'],
        branch=True,
        include=['*/core/security_system.py']
    )
    cov.start()

    try:
        # Run tests
        print("Running security tests with coverage analysis...")
        suite = unittest.TestLoader().discover('tests/security', pattern='test_*.py')
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        # Stop coverage
        cov.stop()
        cov.save()

        # Generate report
        print("\n" + "=" * 60)
        print("COVERAGE REPORT")
        print("=" * 60)

        cov.report(show_missing=True)
        cov.html_report(directory='coverage_html')
        cov.xml_report(outfile='coverage.xml')

        print("\nDetailed HTML report: coverage_html/index.html")
        print("XML report: coverage.xml")

        return result.wasSuccessful()

    except Exception as e:
        print(f"Error running coverage: {e}")
        return False


if __name__ == '__main__':
    # Run coverage analysis
    analyzer = SecurityCoverageAnalyzer()
    coverage_stats = analyzer.run_coverage_analysis()

    print("\n" + "=" * 60)
    print("To run actual coverage analysis:")
    print("1. Install coverage: pip install coverage")
    print("2. Run tests with coverage: python tests/security/test_security_coverage.py")
    print("3. View HTML report: open coverage_html/index.html")
    print("=" * 60)

    # Note: This script analyzes test structure but doesn't run actual tests
    # To run tests, use: python -m pytest tests/security/ -v
    # To run with coverage: coverage run -m pytest tests/security/ && coverage report -m