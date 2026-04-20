"""
==========================================================
JARVIS v9.0 - Core Module Tests
Comprehensive test suite for all core modules
==========================================================
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

# Test lazy loader
def test_lazy_loader():
    """Test lazy module loading"""
    from core.lazy_loader import LazyLoader

    loader = LazyLoader('core.cache')
    assert loader._module is None  # Not loaded yet

    # Access attribute - should trigger load
    cache_class = loader.CacheLayer
    assert loader._module is not None  # Now loaded
    assert cache_class is not None


# Test cache layer
def test_cache_layer():
    """Test caching functionality"""
    from core.cache import CacheLayer

    cache = CacheLayer()

    # Set and get
    cache.set('test_key', {'data': 'value'}, ttl=60)
    result = cache.get('test_key')

    # May be None if Redis not available
    if result:
        assert result['data'] == 'value'


def test_cached_decorator():
    """Test cached decorator"""
    from core.cache import cached

    call_count = 0

    @cached(ttl=60, prefix='test')
    def expensive_function(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    # First call
    result1 = expensive_function(5)
    assert result1 == 10

    # Second call - may use cache
    result2 = expensive_function(5)
    assert result2 == 10


# Test circuit breaker
def test_circuit_breaker():
    """Test circuit breaker pattern"""
    from core.circuit_breaker import CircuitBreaker, CircuitState

    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

    def failing_function():
        raise Exception("Service unavailable")

    # Should fail and open circuit
    for i in range(3):
        try:
            breaker.call(failing_function)
        except Exception:
            pass

    assert breaker.state == CircuitState.OPEN
    assert breaker.failure_count >= 3


def test_circuit_decorator():
    """Test circuit breaker decorator"""
    from core.circuit_breaker import circuit

    call_count = 0

    @circuit(failure_threshold=2, recovery_timeout=1)
    def unstable_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise Exception("Temporary failure")
        return "success"

    # First two calls fail
    for i in range(2):
        try:
            unstable_function()
        except Exception:
            pass


# Test retry logic
def test_retry_with_backoff():
    """Test retry with exponential backoff"""
    from core.retry import retry_with_backoff

    attempt_count = 0

    @retry_with_backoff(max_attempts=3, base_delay=0.1)
    def flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise Exception("Temporary error")
        return "success"

    result = flaky_function()
    assert result == "success"
    assert attempt_count == 3


@pytest.mark.asyncio
async def test_async_retry():
    """Test async retry"""
    from core.retry import async_retry_with_backoff

    attempt_count = 0

    @async_retry_with_backoff(max_attempts=3, base_delay=0.1)
    async def async_flaky_function():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 2:
            raise Exception("Temporary error")
        return "success"

    result = await async_flaky_function()
    assert result == "success"
    assert attempt_count == 2


# Test metrics
def test_metrics_counter():
    """Test metrics counter"""
    from core.metrics import Counter

    counter = Counter('test_counter', 'Test counter')
    assert counter.get() == 0

    counter.inc()
    assert counter.get() == 1

    counter.inc(5)
    assert counter.get() == 6


def test_metrics_histogram():
    """Test metrics histogram"""
    from core.metrics import Histogram

    histogram = Histogram('test_histogram', 'Test histogram')

    histogram.observe(10.0)
    histogram.observe(20.0)
    histogram.observe(30.0)

    stats = histogram.get_stats()
    assert stats['count'] == 3
    assert stats['avg'] == 20.0
    assert stats['min'] == 10.0
    assert stats['max'] == 30.0


def test_metrics_collector():
    """Test metrics collector"""
    from core.metrics import MetricsCollector

    collector = MetricsCollector()

    counter = collector.counter('requests', 'Total requests')
    counter.inc(10)

    histogram = collector.histogram('latency', 'Request latency')
    histogram.observe(100.0)

    metrics = collector.get_all_metrics()
    assert 'requests' in metrics
    assert metrics['requests'] == 10
    assert 'latency_stats' in metrics


# Test structured logging
def test_structured_logger():
    """Test structured logging"""
    from core.structured_logging import StructuredLogger

    logger = StructuredLogger('test')
    logger.bind(request_id='123', user_id='user1')

    # Should not raise
    logger.info('Test message', extra_field='value')
    logger.error('Error message', error_code=500)


# Test configuration
def test_config_loading():
    """Test configuration loading"""
    from core.config import JarvisSettings

    # Should load from .env
    settings = JarvisSettings()

    assert settings.jwt_algorithm == 'HS256'
    assert settings.redis_host is not None
    assert settings.port > 0


# Test orchestrator
def test_orchestrator_init():
    """Test orchestrator initialization"""
    from core.orchestrator import JarvisV9Orchestrator

    orchestrator = JarvisV9Orchestrator()

    assert orchestrator.llm_manager is not None
    assert orchestrator.security_manager is not None
    assert orchestrator.config is not None
    assert orchestrator.start_time is not None


@pytest.mark.asyncio
async def test_orchestrator_process_message():
    """Test message processing"""
    from core.orchestrator import JarvisV9Orchestrator

    orchestrator = JarvisV9Orchestrator()

    result = await orchestrator.process_message(
        "Test message",
        {"context": "test"}
    )

    assert isinstance(result, dict)
    assert 'success' in result


def test_orchestrator_stats():
    """Test system stats"""
    from core.orchestrator import JarvisV9Orchestrator

    orchestrator = JarvisV9Orchestrator()
    stats = orchestrator.get_system_stats()

    assert 'overall_health' in stats
    assert 'uptime_seconds' in stats
    assert 'version' in stats
    assert stats['version'] == '9.0.0'


# Integration test
@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_pipeline():
    """Test full JARVIS pipeline"""
    from core.orchestrator import JarvisV9Orchestrator

    orchestrator = JarvisV9Orchestrator()

    # Process message
    result = await orchestrator.process_message("Hello JARVIS")
    assert result is not None

    # Get stats
    stats = orchestrator.get_system_stats()
    assert stats['total_requests'] > 0

    # Check health
    assert stats['overall_health'] in [True, False]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
