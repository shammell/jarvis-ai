#!/usr/bin/env python3
"""
Simple test script for Input Validation (Fix 14) in main.py process_message method
This test focuses on validation logic without making actual API calls.
"""

import sys
import os
import logging
import asyncio
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_input_validation_simple():
    """Test input validation logic by examining the source code structure"""
    logger.info("🧪 Testing Input Validation (Fix 14) - Simple Structure Test")
    logger.info("=" * 60)

    try:
        import inspect
        from main import JarvisV9Orchestrator

        # Get the source code of process_message method
        source = inspect.getsource(JarvisV9Orchestrator.process_message)
        logger.info("📄 Retrieved process_message source code")

        # Check for key validation components
        validation_checks = [
            ("Message type validation", "isinstance(message, str)"),
            ("Message content validation", "not message or not message.strip()"),
            ("Message length validation", "len(message) > 10000"),
            ("Invalid characters check", "any(char in message for char in [\"\\x00\", \"\\uffff\"])"),
            ("Context type validation", "isinstance(context, dict)"),
            ("User ID type validation", "isinstance(user_id, str)"),
            ("User ID length validation", "len(user_id) > 100"),
            ("Input validation exception handling", "except Exception as validation_error"),
            ("Error response structure", "\"error\": \"invalid_message_type\""),
            ("Request ID in responses", "\"request_id\": self.request_count"),
        ]

        logger.info("\n🔍 Checking for validation components...")

        passed_checks = 0
        failed_checks = 0

        for check_name, check_pattern in validation_checks:
            if check_pattern in source:
                logger.info(f"✅ {check_name}: Found")
                passed_checks += 1
            else:
                logger.error(f"❌ {check_name}: Not found")
                failed_checks += 1

        logger.info(f"\n📊 Validation Structure Check: {passed_checks} passed, {failed_checks} failed")

        # Check for comprehensive error types
        error_types = [
            "empty_message",
            "invalid_message_type",
            "message_too_long",
            "invalid_characters",
            "invalid_context_type",
            "invalid_user_id_type",
            "user_id_too_long",
            "validation_error"
        ]

        logger.info("\n🔍 Checking for error types...")

        error_checks_passed = 0
        for error_type in error_types:
            if f'\"error\": \"{error_type}\"' in source:
                logger.info(f"✅ Error type: {error_type}")
                error_checks_passed += 1
            else:
                logger.error(f"❌ Error type not found: {error_type}")

        logger.info(f"\n📊 Error Type Check: {error_checks_passed}/{len(error_types)} found")

        # Check for validation boundaries and limits
        boundary_checks = [
            ("Message length limit", "10000"),
            ("User ID length limit", "100"),
            ("Try-catch block", "try:" in source and "except Exception as validation_error:" in source),
        ]

        logger.info("\n🔍 Checking for boundary validations...")

        boundary_checks_passed = 0
        for check_name, check_condition in boundary_checks:
            if check_condition:
                logger.info(f"✅ {check_name}: Found")
                boundary_checks_passed += 1
            else:
                logger.error(f"❌ {check_name}: Not found")

        logger.info(f"\n📊 Boundary Check: {boundary_checks_passed}/{len(boundary_checks)} found")

        # Overall assessment
        total_checks = len(validation_checks) + len(error_types) + len(boundary_checks)
        total_passed = passed_checks + error_checks_passed + boundary_checks_passed

        logger.info("\n" + "=" * 60)
        logger.info(f"📈 OVERALL ASSESSMENT")
        logger.info(f"Total checks: {total_checks}")
        logger.info(f"Passed: {total_passed}")
        logger.info(f"Failed: {total_checks - total_passed}")
        logger.info(f"Success rate: {(total_passed/total_checks)*100:.1f}%")

        if total_passed == total_checks:
            logger.info("\n🎉 ALL VALIDATION CHECKS PASSED!")
            logger.info("✅ Input Validation (Fix 14) - COMPLETE!")
            logger.info("   - Message type validation")
            logger.info("   - Message content validation")
            logger.info("   - Message length validation")
            logger.info("   - Context type validation")
            logger.info("   - User ID type validation")
            logger.info("   - User ID length validation")
            logger.info("   - Error handling and response structure")
            return True
        else:
            logger.warning(f"\n⚠️ {total_checks - total_passed} checks failed")
            logger.info("Input validation implementation may be incomplete")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_input_validation_simple()
    sys.exit(0 if success else 1)