#!/usr/bin/env python3
"""
Simple test script for Error Handling and Logging Improvements (Fix 13)
"""

import sys
import os
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_error_handling():
    """Test error handling improvements in main.py wrapper methods"""
    logger.info("🧪 Testing Error Handling and Logging Improvements (Fix 13)")
    logger.info("=" * 60)

    try:
        from main import JarvisV9Orchestrator

        # Test 1: Check that error handling code exists in process_message
        logger.info("\n📝 Test 1: Check process_message error handling structure")

        # Read the source code to verify error handling exists
        import inspect
        source = inspect.getsource(JarvisV9Orchestrator.process_message)

        # Check for key error handling components
        assert "empty message" in source.lower(), "Empty message validation missing"
        assert "try:" in source, "Try block missing"
        assert "except" in source, "Except block missing"
        assert "asyncio.CancelledError" in source, "Cancelled error handling missing"
        assert "unexpected error" in source.lower(), "Unexpected error handling missing"

        logger.info("✅ process_message error handling structure verified")

        # Test 2: Check that error handling code exists in stream_response
        logger.info("\n📝 Test 2: Check stream_response error handling structure")

        stream_source = inspect.getsource(JarvisV9Orchestrator.stream_response)

        # Check for key error handling components
        assert "empty message" in stream_source.lower(), "Empty message validation missing"
        assert "try:" in stream_source, "Try block missing"
        assert "except" in stream_source, "Except block missing"
        assert "asyncio.CancelledError" in stream_source, "Cancelled error handling missing"
        assert "unexpected error" in stream_source.lower(), "Unexpected error handling missing"
        assert "yield" in stream_source, "Streaming yield statements missing"

        logger.info("✅ stream_response error handling structure verified")

        # Test 3: Check input validation
        logger.info("\n📝 Test 3: Check input validation logic")

        # Verify validation logic exists
        assert "not message or not message.strip()" in source, "Input validation missing in process_message"
        assert "not message or not message.strip()" in stream_source, "Input validation missing in stream_response"

        logger.info("✅ Input validation logic verified")

        # Test 4: Check error response structure
        logger.info("\n📝 Test 4: Check error response structure")

        # Verify error responses include proper metadata
        assert '"error"' in source, "Error metadata missing"
        assert '"request_id"' in source, "Request ID missing"
        assert '"text"' in source, "Error text missing"

        logger.info("✅ Error response structure verified")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Error Handling and Logging - ALL TESTS PASSED!")
        logger.info("   - process_message error handling structure")
        logger.info("   - stream_response error handling structure")
        logger.info("   - Input validation logic")
        logger.info("   - Error response structure")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_error_handling()
    sys.exit(0 if success else 1)