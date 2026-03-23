#!/usr/bin/env python3
"""
Test script for Enhanced State Management (Fix 15) in main.py
"""

import sys
import os
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_enhanced_state_management():
    """
    Test comprehensive state management in main.py __init__ method
    """
    logger.info("🧪 Testing Enhanced State Management (Fix 15)")
    logger.info("=" * 60)

    try:
        from main import JarvisV9Orchestrator

        # Initialize orchestrator
        orchestrator = JarvisV9Orchestrator()
        logger.info("✅ JarvisV9Orchestrator initialized")

        # Test 1: System State Tracking
        logger.info("\n📝 Test 1: System State Tracking")
        required_state_fields = [
            "start_time",
            "request_count",
            "last_request_time",
            "total_processing_time",
            "error_count",
            "success_count",
            "uptime_seconds",
            "component_health",
            "performance_metrics",
            "deduplication_cache",
            "deduplication_stats",
            "recovery_attempts",
            "degraded_mode",
            "last_health_check",
            "config",
            "initialization_status"
        ]

        for field in required_state_fields:
            if hasattr(orchestrator, field):
                logger.info(f"✅ {field}: Present")
            else:
                logger.error(f"❌ {field}: Missing")
                return False

        # Test 2: Component Health Tracking
        logger.info("\n📝 Test 2: Component Health Tracking")
        required_components = [
            "llm_manager",
            "speculative_decoder",
            "system2_thinking",
            "memory",
            "first_principles",
            "hyper_automation",
            "rapid_iteration",
            "optimization_engine",
            "autonomous_decision",
            "skill_loader",
            "quality_scorer",
            "profiler",
            "sea_controller"
        ]

        for component in required_components:
            if component in orchestrator.component_health:
                health_status = orchestrator.component_health[component]
                logger.info(f"✅ {component}: Health status = {health_status}")
            else:
                logger.error(f"❌ {component}: Health status missing")
                return False

        # Test 3: Performance Metrics
        logger.info("\n📝 Test 3: Performance Metrics")
        required_metrics = [
            "avg_response_time",
            "success_rate",
            "throughput",
            "error_rate",
            "memory_usage",
            "cpu_usage",
            "active_requests",
            "queue_depth"
        ]

        for metric in required_metrics:
            if metric in orchestrator.performance_metrics:
                value = orchestrator.performance_metrics[metric]
                logger.info(f"✅ {metric}: {value}")
            else:
                logger.error(f"❌ {metric}: Missing from performance metrics")
                return False

        # Test 4: System Resilience
        logger.info("\n📝 Test 4: System Resilience")

        resilience_fields = [
            "recovery_attempts",
            "degraded_mode",
            "last_health_check"
        ]

        for field in resilience_fields:
            if hasattr(orchestrator, field):
                value = getattr(orchestrator, field)
                logger.info(f"✅ {field}: {value}")
            else:
                logger.error(f"❌ {field}: Missing from system resilience")
                return False

        # Test 5: Configuration State
        logger.info("\n📝 Test 5: Configuration State")

        config_fields = [
            "max_concurrent_requests",
            "request_timeout",
            "retry_attempts",
            "health_check_enabled",
            "metrics_collection_enabled",
            "autonomous_mode",
            "sea_enabled"
        ]

        for field in config_fields:
            if field in orchestrator.config:
                value = orchestrator.config[field]
                logger.info(f"✅ {field}: {value}")
            else:
                logger.error(f"❌ {field}: Missing from configuration state")
                return False

        # Test 6: State Updates During Processing
        logger.info("\n📝 Test 6: State Updates During Processing")

        # Get initial state
        initial_request_count = orchestrator.request_count
        initial_error_count = orchestrator.error_count
        initial_success_count = orchestrator.success_count

        # Process a few messages
        test_messages = [
            "Hello, how are you?",
            "What is the weather today?",
            "Tell me a joke"
        ]

        for i, message in enumerate(test_messages):
            try:
                result = await orchestrator.process_message(message, None, "test_user")
                logger.info(f"✅ Message {i+1}: Processed successfully")
                # Verify state was updated
                if orchestrator.request_count > initial_request_count + i:
                    logger.info(f"✅ Request count updated: {orchestrator.request_count}")
                else:
                    logger.error("❌ Request count not properly updated")
                    return False
            except Exception as e:
                logger.error(f"❌ Message {i+1} failed: {e}")
                return False

        # Test 7: Health Monitoring
        logger.info("\n📝 Test 7: Health Monitoring")

        # Test basic health state checking
        if "llm_manager" in orchestrator.component_health:
            initial_health = orchestrator.component_health["llm_manager"]
            logger.info(f"✅ Initial component health: llm_manager = {initial_health}")
        else:
            logger.error("❌ Component health tracking not working")
            return False

        # Test 8: Performance Tracking
        logger.info("\n📝 Test 8: Performance Tracking")

        # Measure processing time
        start_time = time.time()
        await orchestrator.process_message("Performance test message", None, "test_user")
        processing_time = time.time() - start_time

        # Verify performance metrics were updated
        if orchestrator.performance_metrics["avg_response_time"] > 0:
            logger.info(f"✅ Average response time tracked: {orchestrator.performance_metrics['avg_response_time']}")
        else:
            logger.error("❌ Average response time not tracked")
            return False

        # Test 9: System Statistics
        logger.info("\n📝 Test 9: System Statistics")

        # Check that stats methods exist
        if hasattr(orchestrator, 'get_system_stats'):
            stats = orchestrator.get_system_stats()
            required_stats = [
                "uptime_seconds",
                "total_requests",
                "success_rate",
                "avg_response_time",
                "memory_usage",
                "active_components",
                "total_components"
            ]

            for stat in required_stats:
                if stat in stats:
                    value = stats[stat]
                    logger.info(f"✅ {stat}: {value}")
                else:
                    logger.error(f"❌ {stat}: Missing from system stats")
                    return False
        else:
            logger.error("❌ get_system_stats method not found")
            return False

        # Test 10: Health Check
        logger.info("\n📝 Test 10: Health Check")

        # Check that health methods exist
        if hasattr(orchestrator, 'get_health_status'):
            health_status = orchestrator.get_health_status()
            health_components = [
                "system_overall",
                "components",
                "performance",
                "memory",
                "uptime"
            ]

            for component in health_components:
                if component in health_status:
                    status = health_status[component]
                    logger.info(f"✅ {component} health: {status}")
                else:
                    logger.error(f"❌ {component}: Missing from health status")
                    return False
        else:
            logger.error("❌ get_health_status method not found")
            return False

        logger.info("\n" + "=" * 60)
        logger.info("✅ Enhanced State Management - ALL TESTS PASSED!")
        logger.info("   - System state tracking")
        logger.info("   - Component health monitoring")
        logger.info("   - Performance metrics tracking")
        logger.info("   - System resilience mechanisms")
        logger.info("   - Configuration state management")
        logger.info("   - State update verification")
        logger.info("   - Health monitoring and recovery")
        logger.info("   - Performance tracking")
        logger.info("   - System statistics reporting")
        logger.info("   - Comprehensive health checks")

        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    success = await test_enhanced_state_management()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())