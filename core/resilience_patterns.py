"""
JARVIS v9.0 - PhD-Level Resilience Patterns Implementation
Phase 6: Robustness & Resilience

Implements circuit breaker, retry mechanisms, bulkhead isolation,
and watchdog patterns for system resilience.
"""

import asyncio
import time
import logging
import random
from typing import Callable, Any, Optional, Dict, List, Awaitable
from functools import wraps
from threading import Lock
from .registry import register_module

from .resilience_base import (
    CircuitState,
    CircuitMetrics,
    CircuitBreaker,
    RetryPolicy,
    Bulkhead,
    WatchdogTimer,
    ResourcePool,
    ResilienceManager as BaseResilienceManager
)

from .error_handling import error_handler, JarvisError, ErrorCategory, ErrorSeverity, Result, safe_execute, safe_execute_async

logger = logging.getLogger(__name__)

class ResilienceDecorator:
    """
    Decorator for applying resilience patterns to functions
    """

    def __init__(
        self,
        circuit_breaker: Optional[CircuitBreaker] = None,
        retry_policy: Optional[RetryPolicy] = None,
        timeout_seconds: Optional[float] = None
    ):
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.retry_policy = retry_policy or RetryPolicy()
        self.timeout_seconds = timeout_seconds

    def __call__(self, func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            return self._async_wrapper(func)
        else:
            return self._sync_wrapper(func)

    def _sync_wrapper(self, func: Callable) -> Callable:
        """Wrapper for synchronous functions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(self.retry_policy.max_attempts):
                try:
                    # In a real sync circuit breaker we'd need a sync __enter__/__exit__
                    # but for now we simulate with the call() method if it exists
                    # or just execute directly if not
                    if hasattr(self.circuit_breaker, 'call'):
                         result = self.circuit_breaker.call(func, *args, **kwargs)
                         if result.is_success():
                             return result.unwrap()
                         else:
                             error = result.unwrap_error()
                             last_error = error
                    else:
                        return func(*args, **kwargs)

                except Exception as e:
                    last_error = error_handler.handle_exception(e)
                    if (attempt < self.retry_policy.max_attempts - 1 and
                        self.retry_policy.calculate_delay(attempt)): # Simplification
                        delay = self.retry_policy.calculate_delay(attempt)
                        logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                        time.sleep(delay)
                        continue
                    else:
                        break

            # All retries exhausted
            if last_error:
                raise Exception(f"All retry attempts failed for {func.__name__}: {str(last_error)}")
            else:
                raise Exception(f"Unknown error in {func.__name__}")

        return wrapper

    def _async_wrapper(self, func: Callable) -> Callable:
        """Wrapper for asynchronous functions"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None

            for attempt in range(self.retry_policy.max_attempts):
                try:
                    async with self.circuit_breaker:
                        if self.timeout_seconds:
                            return await asyncio.wait_for(func(*args, **kwargs), timeout=self.timeout_seconds)
                        else:
                            return await func(*args, **kwargs)

                except asyncio.TimeoutError:
                    last_error = "Timeout occurred"
                    if attempt < self.retry_policy.max_attempts - 1:
                        delay = self.retry_policy.calculate_delay(attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
                except Exception as e:
                    last_error = e
                    if attempt < self.retry_policy.max_attempts - 1:
                        delay = self.retry_policy.calculate_delay(attempt)
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break

            # All retries exhausted
            raise Exception(f"All retry attempts failed for {func.__name__}: {str(last_error)}")

        return wrapper

@register_module(name="resilience_manager", metadata={"tier": "core", "critical": True})
class ResilienceManager(BaseResilienceManager):
    """
    Enhanced ResilienceManager with JARVIS specific integration
    """
    pass

# Global resilience manager instance
resilience_manager = ResilienceManager()

# Convenience decorators
def circuit_breaker(name: str = "default", **cb_kwargs):
    """Decorator for applying circuit breaker pattern"""
    circuit_breaker_instance = resilience_manager.get_circuit_breaker(name, **cb_kwargs)
    return ResilienceDecorator(circuit_breaker=circuit_breaker_instance)

def retry_policy(**rp_kwargs):
    """Decorator for applying retry policy"""
    retry_policy_instance = RetryPolicy(**rp_kwargs)
    return ResilienceDecorator(retry_policy=retry_policy_instance)

def bulkhead(name: str = "default", max_concurrent: int = 10, **kwargs):
    """Decorator for applying bulkhead pattern"""
    bulkhead_instance = resilience_manager.get_bulkhead(name, max_concurrent=max_concurrent, **kwargs)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with bulkhead_instance:
                return await func(*args, **kwargs)
        return wrapper
    return decorator

def watchdog(name: str = "default", timeout: float = 60.0, **kwargs):
    """Decorator for applying watchdog monitoring"""
    watchdog_instance = resilience_manager.get_watchdog(name, timeout=timeout, **kwargs)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            timer = await watchdog_instance.acquire_timer()
            try:
                return await func(*args, **kwargs)
            finally:
                watchdog_instance.release_timer(timer)
        return wrapper
    return decorator
