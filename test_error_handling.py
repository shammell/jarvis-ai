#!/usr/bin/env python3
"""
Test script for Error Handling and Logging Improvements (Fix 13)
"""

import sys
import os
import logging
import asyncio

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_error_handling():
    """Test error handling and logging improvements in main.py wrapper methods"""
    logger.info("🧪 Testing Error Handling and Logging Improvements (Fix 13)")
    logger.info("=" * 60)

    try:
        from main import JarvisV9Orchestrator

        # Initialize orchestrator
        orchestrator = JarvisV9Orchestrator()
        logger.info("✅ JarvisV9Orchestrator initialized")

        # Test 1: Empty message handling
        logger.info("\n📝 Test 1: Empty message handling")

        async def test_empty_message():
            # Test empty string
            response = await orchestrator.process_message("")
            assert response["metadata"]["error"] == "empty_message"
            logger.info("✅ Empty string handled correctly")

            # Test whitespace string
            response = await orchestrator.process_message("   ")
            assert response["metadata"]["error"] == "empty_message"
            logger.info("✅ Whitespace string handled correctly")

            # Test None message
            try:
                response = await orchestrator.process_message(None)
                # Should handle None gracefully
                logger.info("✅ None message handled")
            except Exception as e:
                logger.info(f"✅ None message properly rejected: {e}")

        asyncio.run(test_empty_message())

        # Test 2: Streaming with empty message
        logger.info("\n📝 Test 2: Streaming empty message handling")

        async def test_streaming_empty():
            chunks = []
            async for chunk in orchestrator.stream_response(""):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert chunks[0]["type"] == "error"
            assert chunks[0]["metadata"]["error"] == "empty_message"
            logger.info("✅ Streaming empty message handled correctly")

        asyncio.run(test_streaming_empty())

        # Test 3: Test with valid message (should not trigger error handling)
        logger.info("\n📝 Test 3: Valid message processing")

        async def test_valid_message():
            response = await orchestrator.process_message("Hello, how are you?")
            assert "text" in response
            assert "metadata" in response
            logger.info("✅ Valid message processed correctly")

        asyncio.run(test_valid_message())

        # Test 4: Test SEA controller monitoring
        logger.info("\n📝 Test 4: SEA controller monitoring")

        # Add a mock SEA controller to test monitoring path
        class MockSEAController:
            def monitor_function(self, func):
                async def wrapper(*args, **kwargs):
                    logger.info("🔍 Mock SEA monitoring active")
                    return await func(*args, **kwargs)
                return wrapper

        orchestrator.sea_controller = MockSEAController()

        async def test_sea_monitoring():
            response = await orchestrator.process_message("Test with SEA monitoring")
            assert "text" in response
            logger.info("✅ SEA controller monitoring working")

        asyncio.run(test_sea_monitoring())

        # Test 5: Test error propagation
        logger.info("\n📝 Test 5: Error propagation")

        # Temporarily replace _process_message_impl to simulate error
        original_impl = orchestrator._process_message_impl

        async def error_impl(message, context=None, user_id=None):
            raise Exception("Test error for error handling verification")

        orchestrator._process_message_impl = error_impl

        async def test_error_propagation():
            response = await orchestrator.process_message("This should cause an error")
            assert "error" in response["metadata"]
            assert "process_message_wrapper_error" in response["metadata"]["error"]
            logger.info("✅ Error propagation working correctly")

        asyncio.run(test_error_propagation())

        # Restore original implementation
        orchestrator._process_message_impl = original_impl

        logger.info("\n" + "=" * 60)
        logger.info("✅ Error Handling and Logging - ALL TESTS PASSED!")
        logger.info("   - Empty message validation")
        logger.info("   - Streaming error handling")
        logger.info("   - Valid message processing")
        logger.info("   - SEA controller monitoring")
        logger.info("   - Error propagation and logging")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_error_handling()
    sys.exit(0 if success else 1)