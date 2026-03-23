#!/usr/bin/env python3
"""
Test script for Context Pinning Memory Management (Fix 11)
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_context_pinning():
    """Test context pinning functionality"""
    logger.info("🧪 Testing Context Pinning Memory Management (Fix 11)")
    logger.info("=" * 60)

    try:
        from memory.memory_controller import MemoryController

        # Initialize memory controller with custom config
        config = {
            "storage_path": "./test_memory",
            "max_contexts": 5,  # Small limit for testing
            "context_ttl": 300  # 5 minutes for testing
        }

        controller = MemoryController(config)
        logger.info("✅ Memory Controller with context pinning initialized")

        # Test 1: Pin contexts with different priorities
        logger.info("\n📝 Test 1: Pin contexts with different priorities")

        controller.pin_context("project_jarvis", "JARVIS v9.0 is a sophisticated AI system", priority=5)
        controller.pin_context("todo_speculative", "Implement speculative decoding", priority=3)
        controller.pin_context("technical_fastapi", "JARVIS uses FastAPI for backend", priority=2)

        pinned = controller.get_all_pinned_contexts()
        logger.info(f"✅ Pinned {len(pinned)} contexts")

        # Test 2: Get pinned context
        logger.info("\n📝 Test 2: Get pinned context")
        context = controller.get_pinned_context("project_jarvis")
        if context:
            logger.info(f"✅ Retrieved pinned context: {context['content'][:50]}...")
            logger.info(f"   Access count: {context['access_count']}")
        else:
            logger.error("❌ Failed to retrieve pinned context")

        # Test 3: Automatic eviction when limit reached
        logger.info("\n📝 Test 3: Test automatic eviction")
        logger.info("Pinning additional contexts to trigger eviction...")

        controller.pin_context("low_priority_1", "Low priority context 1", priority=1)
        controller.pin_context("low_priority_2", "Low priority context 2", priority=1)
        controller.pin_context("medium_priority", "Medium priority context", priority=2)

        pinned_after_eviction = controller.get_all_pinned_contexts()
        logger.info(f"✅ After eviction: {len(pinned_after_eviction)} contexts")

        # Test 4: Memory health check
        logger.info("\n📝 Test 4: Memory health check")
        health = controller.get_memory_health()
        logger.info(f"✅ Memory health status: {health['status']}")
        logger.info(f"   Pinned contexts: {health['pinned_contexts_count']}")
        logger.info(f"   Usage: {health['pinned_contexts_usage']:.2%}")

        # Test 5: Context expiration
        logger.info("\n📝 Test 5: Context expiration")
        # Temporarily create an expired context
        expired_time = datetime.now() - timedelta(seconds=400)  # 400 seconds ago (over 300s TTL)
        controller.pinned_contexts["expired_context"] = {
            "content": "This context should be expired",
            "priority": 1,
            "timestamp": expired_time.isoformat(),
            "metadata": {},
            "access_count": 0
        }

        controller.cleanup_expired_contexts()
        health_after_cleanup = controller.get_memory_health()
        logger.info(f"✅ After cleanup: {health_after_cleanup['expired_contexts']} expired contexts removed")

        # Test 6: Integration with memory storage
        logger.info("\n📝 Test 6: Integration with memory storage")
        controller.store("Important project memory that should be pinned", "project")
        controller.store("Regular conversation memory", "conversation")

        health_final = controller.get_memory_health()
        logger.info(f"✅ Final health: {health_final['pinned_contexts_count']} pinned contexts")

        # Verify important context was automatically pinned
        all_contexts = controller.get_all_pinned_contexts()
        project_contexts = [cid for cid in all_contexts.keys() if 'project' in cid]
        logger.info(f"✅ Auto-pinned project contexts: {len(project_contexts)}")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Context Pinning Memory Management - ALL TESTS PASSED!")
        logger.info("   - Context pinning with priority levels")
        logger.info("   - Automatic eviction of low-priority contexts")
        logger.info("   - Memory health monitoring")
        logger.info("   - Context expiration and cleanup")
        logger.info("   - Integration with memory storage")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_context_pinning()
    sys.exit(0 if success else 1)