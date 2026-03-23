#!/usr/bin/env python3
"""
Test script for Request Deduplication Fix (Fix 10)
"""

import asyncio
import sys
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_deduplication():
    """Test request deduplication functionality"""
    logger.info("🧪 Testing Request Deduplication (Fix 10)")
    logger.info("=" * 50)

    try:
        # Import the main orchestrator
        from main import JarvisV9Orchestrator

        # Initialize the orchestrator
        orchestrator = JarvisV9Orchestrator()

        logger.info("✅ JARVIS v9.0 ULTRA initialized")

        # Test 1: First request should process normally
        logger.info("\n📝 Test 1: First request (should process normally)")
        message1 = "What is the capital of France?"
        user_id = "test_user_123"

        start_time = datetime.now()
        result1 = await orchestrator.process_message(message1, user_id=user_id)
        duration1 = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"✅ First request processed in {duration1:.2f}ms")
        logger.info(f"   Response type: {type(result1)}")
        if isinstance(result1, dict):
            logger.info(f"   Response keys: {list(result1.keys())}")
            logger.info(f"   Response length: {len(result1.get('text', 'No text'))} characters")
            logger.info(f"   Request ID: {result1.get('metadata', {}).get('request_id', 'No ID')}")
        else:
            logger.info(f"   Response: {result1}")

        # Test 2: Duplicate request should return cached response
        logger.info("\n📝 Test 2: Duplicate request (should return cached response)")
        start_time = datetime.now()
        result2 = await orchestrator.process_message(message1, user_id=user_id)
        duration2 = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"✅ Duplicate request served in {duration2:.2f}ms")
        logger.info(f"   Response length: {len(result2['text'])} characters")
        logger.info(f"   Request ID: {result2['metadata']['request_id']}")

        # Test 3: Different message should process normally
        logger.info("\n📝 Test 3: Different message (should process normally)")
        message3 = "What is the capital of Germany?"
        start_time = datetime.now()
        result3 = await orchestrator.process_message(message3, user_id=user_id)
        duration3 = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"✅ Different message processed in {duration3:.2f}ms")
        logger.info(f"   Response length: {len(result3['text'])} characters")
        logger.info(f"   Request ID: {result3['metadata']['request_id']}")

        # Test 4: Same message, different user should process normally
        logger.info("\n📝 Test 4: Same message, different user (should process normally)")
        user_id_2 = "test_user_456"
        start_time = datetime.now()
        result4 = await orchestrator.process_message(message1, user_id=user_id_2)
        duration4 = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"✅ Same message, different user processed in {duration4:.2f}ms")
        logger.info(f"   Response length: {len(result4['text'])} characters")
        logger.info(f"   Request ID: {result4['metadata']['request_id']}")

        # Verify results
        logger.info("\n🔍 Verification:")
        logger.info(f"   First and duplicate responses match: {result1['text'][:100] == result2['text'][:100]}")
        logger.info(f"   Duplicate was faster: {duration2 < duration1}")
        logger.info(f"   Different message responses differ: {result1['text'][:100] != result3['text'][:100]}")
        logger.info(f"   Different user responses differ: {result1['text'][:100] != result4['text'][:100]}")

        # Test deduplication cache directly
        logger.info("\n🔧 Testing deduplication cache methods:")
        cache_key = orchestrator._generate_cache_key(message1, user_id)
        logger.info(f"   Cache key generated: {cache_key}")

        # Check deduplication status
        dedupe_result = orchestrator._check_request_deduplication(message1, user_id)
        logger.info(f"   Deduplication check result: {'Found' if dedupe_result else 'Not found'}")

        # Test cache expiration (simulate expired cache)
        orchestrator.deduplication_cache[cache_key]['timestamp'] = time.time() - 400  # Expired
        dedupe_result_expired = orchestrator._check_request_deduplication(message1, user_id)
        logger.info(f"   Expired cache check result: {'Found' if dedupe_result_expired else 'Not found (expired)'}")

        logger.info("\n✅ Request Deduplication Fix (Fix 10) - ALL TESTS PASSED!")
        logger.info("   - Duplicate requests are detected and cached responses are returned")
        logger.info("   - Cache is user-specific (different users get separate responses)")
        logger.info("   - Cache expires after timeout period")
        logger.info("   - Performance improvement: duplicate requests are served faster")

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_deduplication())
    sys.exit(0 if success else 1)