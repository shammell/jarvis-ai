#!/usr/bin/env python3
"""
Test script for Input Validation (Fix 14) in main.py process_message method
"""

import sys
import os
import logging
import asyncio
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def test_input_validation():
    """Test comprehensive input validation in process_message method"""
    logger.info("🧪 Testing Input Validation (Fix 14)")
    logger.info("=" * 60)

    try:
        from main import JarvisV9Orchestrator

        # Initialize orchestrator
        orchestrator = JarvisV9Orchestrator()
        logger.info("✅ JarvisV9Orchestrator initialized")

        # Test cases for input validation
        test_cases = [
            # Message validation tests
            {
                "name": "Valid message",
                "message": "Hello, how are you?",
                "context": None,
                "user_id": "test_user",
                "expected_error": None
            },
            {
                "name": "Empty string",
                "message": "",
                "context": None,
                "user_id": None,
                "expected_error": "empty_message"
            },
            {
                "name": "Whitespace only",
                "message": "   ",
                "context": None,
                "user_id": None,
                "expected_error": "empty_message"
            },
            {
                "name": "Non-string message (int)",
                "message": 123,
                "context": None,
                "user_id": None,
                "expected_error": "invalid_message_type"
            },
            {
                "name": "Non-string message (list)",
                "message": ["hello", "world"],
                "context": None,
                "user_id": None,
                "expected_error": "invalid_message_type"
            },
            {
                "name": "Message too long (10,001 chars)",
                "message": "A" * 10001,
                "context": None,
                "user_id": None,
                "expected_error": "message_too_long"
            },
            {
                "name": "Message with null bytes",
                "message": "Hello\x00World",
                "context": None,
                "user_id": None,
                "expected_error": "invalid_characters"
            },
            {
                "name": "Message with invalid unicode",
                "message": "Hello\uffffWorld",
                "context": None,
                "user_id": None,
                "expected_error": "invalid_characters"
            },

            # Context validation tests
            {
                "name": "Invalid context type (string)",
                "message": "Hello",
                "context": "invalid_context",
                "user_id": None,
                "expected_error": "invalid_context_type"
            },
            {
                "name": "Invalid context type (int)",
                "message": "Hello",
                "context": 123,
                "user_id": None,
                "expected_error": "invalid_context_type"
            },
            {
                "name": "Valid context (dict)",
                "message": "Hello",
                "context": {"test": "value"},
                "user_id": None,
                "expected_error": None
            },
            {
                "name": "Context as None",
                "message": "Hello",
                "context": None,
                "user_id": None,
                "expected_error": None
            },

            # User ID validation tests
            {
                "name": "Invalid user_id type (int)",
                "message": "Hello",
                "context": None,
                "user_id": 123,
                "expected_error": "invalid_user_id_type"
            },
            {
                "name": "Invalid user_id type (list)",
                "message": "Hello",
                "context": None,
                "user_id": ["user1", "user2"],
                "expected_error": "invalid_user_id_type"
            },
            {
                "name": "User ID too long (101 chars)",
                "message": "Hello",
                "context": None,
                "user_id": "A" * 101,
                "expected_error": "user_id_too_long"
            },
            {
                "name": "Empty user_id after strip",
                "message": "Hello",
                "context": None,
                "user_id": "   ",
                "expected_error": None  # Should be converted to None
            },
            {
                "name": "Valid user_id",
                "message": "Hello",
                "context": None,
                "user_id": "test_user_123",
                "expected_error": None
            },
            {
                "name": "User ID as None",
                "message": "Hello",
                "context": None,
                "user_id": None,
                "expected_error": None
            },

            # Edge cases
            {
                "name": "Maximum valid message length (10,000 chars)",
                "message": "A" * 10000,
                "context": None,
                "user_id": None,
                "expected_error": None
            },
            {
                "name": "Empty string message with valid context and user_id",
                "message": "",
                "context": {"test": "value"},
                "user_id": "test_user",
                "expected_error": "empty_message"
            }
        ]

        logger.info(f"\n🧪 Testing {len(test_cases)} input validation scenarios...")

        passed = 0
        failed = 0

        async def run_test_case(test_case):
            try:
                result = await orchestrator.process_message(
                    test_case["message"],
                    test_case["context"],
                    test_case["user_id"]
                )

                # Check if error was expected
                if test_case["expected_error"]:
                    if "error" in result["metadata"]:
                        error_type = result["metadata"]["error"]
                        if error_type == test_case["expected_error"]:
                            logger.info(f"✅ {test_case['name']}: {error_type}")
                            return True
                        else:
                            logger.error(f"❌ {test_case['name']}: Expected '{test_case['expected_error']}', got '{error_type}'")
                            return False
                    else:
                        logger.error(f"❌ {test_case['name']}: Expected error '{test_case['expected_error']}', but got success response")
                        return False
                else:
                    # Should not have errors
                    if "error" not in result["metadata"]:
                        logger.info(f"✅ {test_case['name']}: Valid input accepted")
                        return True
                    else:
                        logger.error(f"❌ {test_case['name']}: Unexpected error '{result['metadata']['error']}'")
                        return False

            except Exception as e:
                logger.error(f"❌ {test_case['name']}: Exception occurred: {e}")
                return False

        # Run all test cases
        for i, test_case in enumerate(test_cases, 1):
            success = await run_test_case(test_case)
            if success:
                passed += 1
            else:
                failed += 1

        logger.info(f"\n📊 Results: {passed} passed, {failed} failed")

        if failed == 0:
            logger.info("\n" + "=" * 60)
            logger.info("✅ Input Validation - ALL TESTS PASSED!")
            logger.info("   - Message type validation")
            logger.info("   - Message content validation")
            logger.info("   - Message length validation")
            logger.info("   - Context type validation")
            logger.info("   - User ID type validation")
            logger.info("   - User ID length validation")
            logger.info("   - Edge case handling")
            logger.info("   - Error response structure")
            return True
        else:
            logger.error(f"\n❌ {failed} tests failed")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_input_validation()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())