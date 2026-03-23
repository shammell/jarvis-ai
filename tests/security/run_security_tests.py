#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Security Test Runner
Execute all security tests with comprehensive reporting
==========================================================
"""

import unittest
import sys
import os
import time
import json
from datetime import datetime
from io import StringIO

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all security test modules
from tests.security.test_security_manager import TestSecurityManager
from tests.security.test_input_validator import TestInputValidator
from tests.security.test_security_middleware import TestSecurityMiddleware
from tests.security.test_jwt_auth import TestJWTAuthentication
from tests.security.test_rbac import TestRBAC
from tests.security.test_rate_limiting import TestRateLimiting
from tests.security.test_security_integration import TestSecurityIntegration
from tests.security.test_security_e2e import TestSecurityE2E
from tests.security.test_security_coverage import SecurityCoverageAnalyzer


class SecurityTestRunner:
    """Comprehensive security test runner with detailed reporting"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.results = {
            'test_suites': {},
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'execution_time': 0,
            'coverage_analysis': {}
        }

    def run_all_security_tests(self):
        """Run all security test suites"""
        self.start_time = datetime.now()

        print("=" * 80)
        print("JARVIS v9.0+ - COMPREHENSIVE SECURITY TEST SUITE")
        print("=" * 80)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Define test suites
        test_suites = [
            ('Security Manager', TestSecurityManager),
            ('Input Validator', TestInputValidator),
            ('Security Middleware', TestSecurityMiddleware),
            ('JWT Authentication', TestJWTAuthentication),
            ('Role-Based Access Control', TestRBAC),
            ('Rate Limiting', TestRateLimiting),
            ('Security Integration', TestSecurityIntegration),
            ('Security End-to-End', TestSecurityE2E)
        ]

        # Run each test suite
        for suite_name, test_class in test_suites:
            print(f"\n{'='*60}")
            print(f"Running: {suite_name}")
            print(f"{'='*60}")

            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            stream = StringIO()
            runner = unittest.TextTestRunner(
                stream=stream,
                verbosity=2,
                failfast=False,
                buffer=True
            )

            result = runner.run(suite)

            # Store results
            self.results['test_suites'][suite_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
                'details': {
                    'failures': [str(f[0]) for f in result.failures],
                    'errors': [str(e[0]) for e in result.errors],
                    'skipped': [str(s[0]) for s in (getattr(result, 'skipped', []))]
                }
            }

            # Update totals
            self.results['total_tests'] += result.testsRun
            self.results['passed'] += result.testsRun - len(result.failures) - len(result.errors)
            self.results['failed'] += len(result.failures)
            self.results['errors'] += len(result.errors)

            # Print suite summary
            print(f"Tests run: {result.testsRun}")
            print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
            print(f"Failed: {len(result.failures)}")
            print(f"Errors: {len(result.errors)}")

            if result.failures:
                print(f"\nFailures:")
                for test, traceback in result.failures:
                    print(f"  - {test}")

            if result.errors:
                print(f"\nErrors:")
                for test, traceback in result.errors:
                    print(f"  - {test}")

        self.end_time = datetime.now()
        self.results['execution_time'] = (self.end_time - self.start_time).total_seconds()

        # Run coverage analysis
        print(f"\n{'='*60}")
        print("Running Coverage Analysis")
        print(f"{'='*60}")
        analyzer = SecurityCoverageAnalyzer()
        self.results['coverage_analysis'] = analyzer.run_coverage_analysis()

        # Generate final report
        self.generate_final_report()

        return self.results['failed'] == 0 and self.results['errors'] == 0

    def generate_final_report(self):
        """Generate comprehensive final report"""
        print("\n" + "=" * 80)
        print("FINAL SECURITY TEST REPORT")
        print("=" * 80)

        # Executive Summary
        print("\nEXECUTIVE SUMMARY")
        print("-" * 40)
        print(f"Total Test Suites: {len(self.results['test_suites'])}")
        print(f"Total Tests: {self.results['total_tests']}")
        print(f"Passed: {self.results['passed']}")
        print(f"Failed: {self.results['failed']}")
        print(f"Errors: {self.results['errors']}")
        print(f"Success Rate: {(self.results['passed'] / self.results['total_tests'] * 100):.1f}%")
        print(f"Execution Time: {self.results['execution_time']:.2f} seconds")

        # Suite-by-Suite Results
        print(f"\nTEST SUITE RESULTS")
        print("-" * 40)
        for suite_name, stats in self.results['test_suites'].items():
            status = "✓" if stats['failures'] == 0 and stats['errors'] == 0 else "✗"
            success_rate = ((stats['tests_run'] - stats['failures'] - stats['errors']) / stats['tests_run'] * 100) if stats['tests_run'] > 0 else 0
            print(f"{status} {suite_name}")
            print(f"   Tests: {stats['tests_run']}, Passed: {stats['tests_run'] - stats['failures'] - stats['errors']}, Failed: {stats['failures']}, Errors: {stats['errors']}")
            print(f"   Success Rate: {success_rate:.1f}%")

        # Coverage Analysis
        coverage = self.results['coverage_analysis']
        print(f"\nCOVERAGE ANALYSIS")
        print("-" * 40)
        print(f"Test Files: {coverage.get('file_coverage', 0):.1f}%")
        print(f"Classes: {coverage.get('class_coverage', 0):.1f}%")
        print(f"Overall: {coverage.get('overall_coverage', 0):.1f}%")

        # Security Assessment
        print(f"\nSECURITY ASSESSMENT")
        print("-" * 40)

        security_score = 0
        max_score = 100

        # Base score on test results
        if self.results['failed'] == 0 and self.results['errors'] == 0:
            security_score += 50
        else:
            security_score += (self.results['passed'] / self.results['total_tests']) * 50

        # Coverage score
        coverage_score = coverage.get('overall_coverage', 0) * 0.3
        security_score += coverage_score

        # Additional security checks
        if coverage.get('file_coverage', 0) >= 90:
            security_score += 10
        elif coverage.get('file_coverage', 0) >= 70:
            security_score += 5

        if coverage.get('class_coverage', 0) >= 90:
            security_score += 10
        elif coverage.get('class_coverage', 0) >= 70:
            security_score += 5

        print(f"Security Score: {security_score:.1f}/100")

        if security_score >= 90:
            print("🟢 EXCELLENT: Security testing is comprehensive and robust")
        elif security_score >= 75:
            print("🟡 GOOD: Security testing is solid with minor improvements needed")
        elif security_score >= 60:
            print("🟠 MODERATE: Security testing needs significant improvement")
        else:
            print("🔴 POOR: Security testing is insufficient for production")

        # Recommendations
        print(f"\nRECOMMENDATIONS")
        print("-" * 40)

        if self.results['failed'] > 0:
            print(f"• Fix {self.results['failed']} failing tests before deployment")
        if self.results['errors'] > 0:
            print(f"• Resolve {self.results['errors']} test errors")
        if coverage.get('overall_coverage', 0) < 80:
            print(f"• Increase test coverage to 80%+ for security-critical components")
        if coverage.get('file_coverage', 0) < 100:
            print(f"• Create missing test files to achieve complete coverage")
        if security_score < 80:
            print(f"• Conduct additional security testing and code review")

        print(f"• Run security tests regularly as part of CI/CD pipeline")
        print(f"• Consider penetration testing for production deployment")

        # Save detailed report
        report_file = f"security_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\nDetailed report saved to: {report_file}")
        print(f"Test execution completed at: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)


def main():
    """Main entry point"""
    print("Starting JARVIS v9.0+ Security Test Suite...")
    print("This may take several minutes to complete.\n")

    runner = SecurityTestRunner()
    success = runner.run_all_security_tests()

    if success:
        print("\n🎉 All security tests PASSED!")
        print("The security implementation is ready for production.")
        sys.exit(0)
    else:
        print("\n❌ Some security tests FAILED!")
        print("Please review the failures and fix issues before deployment.")
        sys.exit(1)


if __name__ == '__main__':
    main()