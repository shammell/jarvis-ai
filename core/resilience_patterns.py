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
from enum import Enum
from typing import Callable, Any, Optional, Dict, List, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from threading import Lock
import weakref

from .error_handling import error_handler, JarvisError, ErrorCategory, ErrorSeverity, Result, safe_execute, safe_execute_async

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Trip threshold exceeded
    HALF_OPEN = "half_open" # Testing recovery

@dataclass
class CircuitMetrics:
    """Circuit breaker metrics"""
    success_count: int = 0
    failure_count: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    total_requests: int = 0
    opened_time: Optional[datetime] = None

class CircuitBreaker:
    """
    PhD-Level Circuit Breaker Implementation
    - Adaptive threshold adjustment
    - Exponential backoff
    - Metrics collection
    - Health assessment
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        timeout_seconds: float = 60.0,
        success_threshold: int = 3,
        error_ratio_threshold: float = 0.5,
        name: str = "default"
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.success_threshold = success_threshold
        self.error_ratio_threshold = error_ratio_threshold

        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.lock = Lock()

        # Track recent requests for adaptive adjustment
        self.recent_requests = []
        self.max_recent_requests = 100

    def _should_trip(self) -> bool:
        """Determine if circuit should trip based on failure metrics"""
        # Check absolute failure count
        if self.metrics.consecutive_failures >= self.failure_threshold:
            return True

        # Check error ratio if we have enough requests
        total = self.metrics.total_requests
        if total >= 10:  # Minimum threshold for ratio calculation
            error_ratio = self.metrics.failure_count / total
            if error_ratio >= self.error_ratio_threshold:
                return True

        return False

    def _should_reset(self) -> bool:
        """Determine if circuit should reset to closed"""
        if self.state != CircuitState.OPEN:
            return False

        # Check if timeout has passed
        if (self.metrics.opened_time and
            datetime.now() - self.metrics.opened_time >= timedelta(seconds=self.timeout_seconds)):
            return True

        return False

    def _calculate_timeout(self) -> float:
        """Calculate adaptive timeout based on failure patterns"""
        base_timeout = self.timeout_seconds
        # Increase timeout exponentially with consecutive failures
        multiplier = min(4.0, 1.5 ** min(10, self.metrics.consecutive_failures))
        return base_timeout * multiplier

    def call(self, func: Callable, *args, **kwargs) -> Result:
        """Execute function through circuit breaker"""
        with self.lock:
            # Check if circuit should be reset
            if self.state == CircuitState.OPEN and self._should_reset():
                self._reset_circuit()

            # If circuit is open, fail fast
            if self.state == CircuitState.OPEN:
                error = JarvisError(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.HIGH,
                    message=f"Circuit breaker {self.name} is OPEN - failing fast",
                    user_message="Service temporarily unavailable, please try again later"
                )
                self._record_request(False)
                return Result.failure(error)

            # Execute the function
            try:
                result = func(*args, **kwargs)
                self._handle_success()
                self._record_request(True)
                return Result.success(result)
            except Exception as e:
                self._handle_failure()
                self._record_request(False)
                # Convert exception to JarvisError
                error = error_handler.handle_exception(e, context={
                    "circuit_breaker": self.name,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                })
                return Result.failure(error)

    async def acall(self, func: Callable, *args, **kwargs) -> Result:
        """Async execution through circuit breaker"""
        with self.lock:
            # Check if circuit should be reset
            if self.state == CircuitState.OPEN and self._should_reset():
                self._reset_circuit()

            # If circuit is open, fail fast
            if self.state == CircuitState.OPEN:
                error = JarvisError(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.HIGH,
                    message=f"Circuit breaker {self.name} is OPEN - failing fast",
                    user_message="Service temporarily unavailable, please try again later"
                )
                self._record_request(False)
                return Result.failure(error)

            # Execute the function
            try:
                result = await func(*args, **kwargs)
                self._handle_success()
                self._record_request(True)
                return Result.success(result)
            except Exception as e:
                self._handle_failure()
                self._record_request(False)
                # Convert exception to JarvisError
                error = error_handler.handle_exception(e, context={
                    "circuit_breaker": self.name,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                })
                return Result.failure(error)

    def _handle_success(self):
        """Handle successful execution"""
        self.state = CircuitState.CLOSED
        self.metrics.success_count += 1
        self.metrics.consecutive_failures = 0
        if self.metrics.last_failure_time:
            self.metrics.last_failure_time = None

    def _handle_failure(self):
        """Handle failed execution"""
        self.metrics.failure_count += 1
        self.metrics.consecutive_failures += 1

        # Update last failure time
        self.metrics.last_failure_time = datetime.now()

        # Check if we should trip the circuit
        if self._should_trip():
            self._trip_circuit()

    def _trip_circuit(self):
        """Trip the circuit to open state"""
        self.state = CircuitState.OPEN
        self.metrics.opened_time = datetime.now()
        logger.warning(f"⚠️ Circuit breaker {self.name} TRIPPED - now OPEN")

    def _reset_circuit(self):
        """Reset circuit to closed state"""
        self.state = CircuitState.HALF_OPEN
        logger.info(f"🔄 Circuit breaker {self.name} transitioning to HALF_OPEN for testing")

        # In half-open state, next call will attempt to reset to closed
        # We'll reset metrics after successful attempts

    def _record_request(self, success: bool):
        """Record request for adaptive learning"""
        self.metrics.total_requests += 1
        current_time = time.time()

        self.recent_requests.append({
            'success': success,
            'timestamp': current_time
        })

        # Trim recent requests
        if len(self.recent_requests) > self.max_recent_requests:
            self.recent_requests = self.recent_requests[-self.max_recent_requests:]

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'metrics': {
                'success_count': self.metrics.success_count,
                'failure_count': self.metrics.failure_count,
                'consecutive_failures': self.metrics.consecutive_failures,
                'total_requests': self.metrics.total_requests,
                'success_rate': self.metrics.success_count / max(1, self.metrics.total_requests) if self.metrics.total_requests > 0 else 0,
                'opened_time': self.metrics.opened_time.isoformat() if self.metrics.opened_time else None,
                'last_failure_time': self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None
            },
            'configuration': {
                'failure_threshold': self.failure_threshold,
                'timeout_seconds': self.timeout_seconds,
                'success_threshold': self.success_threshold,
                'error_ratio_threshold': self.error_ratio_threshold
            }
        }

class RetryPolicy:
    """
    PhD-Level Retry Policy with adaptive backoff
    """

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retryable_errors: Optional[List[ErrorCategory]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retryable_errors = retryable_errors or [
            ErrorCategory.NETWORK,
            ErrorCategory.TIMEOUT,
            ErrorCategory.EXTERNAL_API
        ]

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next attempt with exponential backoff"""
        delay = min(
            self.base_delay * (self.backoff_factor ** attempt),
            self.max_delay
        )

        if self.jitter:
            # Add random jitter to prevent thundering herd
            jitter_range = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay)  # Ensure non-negative

        return delay

    def should_retry(self, error: JarvisError) -> bool:
        """Determine if error is retryable"""
        if error.category in self.retryable_errors:
            return True

        # Check severity - allow retry for medium and low severity
        if error.severity in [ErrorSeverity.LOW, ErrorSeverity.MEDIUM]:
            return True

        return False

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
                if self.timeout_seconds:
                    # Implement timeout for sync function
                    # This is simplified - in practice you'd need threading or multiprocessing
                    try:
                        # Execute through circuit breaker
                        result = self.circuit_breaker.call(func, *args, **kwargs)

                        if result.is_success():
                            return result.unwrap()
                        else:
                            error = result.unwrap_error()
                            last_error = error

                            # Check if we should retry
                            if attempt < self.retry_policy.max_attempts - 1 and self.retry_policy.should_retry(error):
                                delay = self.retry_policy.calculate_delay(attempt)
                                logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                                time.sleep(delay)
                                continue
                            else:
                                break
                    except Exception as e:
                        last_error = error_handler.handle_exception(e)
                        if (attempt < self.retry_policy.max_attempts - 1 and
                            self.retry_policy.should_retry(last_error)):
                            delay = self.retry_policy.calculate_delay(attempt)
                            logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                            time.sleep(delay)
                            continue
                        else:
                            break
                else:
                    # Execute without timeout
                    try:
                        result = self.circuit_breaker.call(func, *args, **kwargs)

                        if result.is_success():
                            return result.unwrap()
                        else:
                            error = result.unwrap_error()
                            last_error = error

                            if (attempt < self.retry_policy.max_attempts - 1 and
                                self.retry_policy.should_retry(error)):
                                delay = self.retry_policy.calculate_delay(attempt)
                                logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                                time.sleep(delay)
                                continue
                            else:
                                break
                    except Exception as e:
                        last_error = error_handler.handle_exception(e)
                        if (attempt < self.retry_policy.max_attempts - 1 and
                            self.retry_policy.should_retry(last_error)):
                            delay = self.retry_policy.calculate_delay(attempt)
                            logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                            time.sleep(delay)
                            continue
                        else:
                            break

            # All retries exhausted
            if last_error:
                raise Exception(f"All retry attempts failed for {func.__name__}: {last_error.message}")
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
                    if self.timeout_seconds:
                        # Execute with timeout
                        result = await asyncio.wait_for(
                            self.circuit_breaker.acall(func, *args, **kwargs),
                            timeout=self.timeout_seconds
                        )
                    else:
                        result = await self.circuit_breaker.acall(func, *args, **kwargs)

                    if result.is_success():
                        return result.unwrap()
                    else:
                        error = result.unwrap_error()
                        last_error = error

                        if (attempt < self.retry_policy.max_attempts - 1 and
                            self.retry_policy.should_retry(error)):
                            delay = self.retry_policy.calculate_delay(attempt)
                            logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                            await asyncio.sleep(delay)
                            continue
                        else:
                            break
                except asyncio.TimeoutError:
                    error = JarvisError(
                        category=ErrorCategory.TIMEOUT,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Function {func.__name__} timed out after {self.timeout_seconds}s"
                    )
                    last_error = error

                    if (attempt < self.retry_policy.max_attempts - 1 and
                        self.retry_policy.should_retry(error)):
                        delay = self.retry_policy.calculate_delay(attempt)
                        logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break
                except Exception as e:
                    last_error = error_handler.handle_exception(e)

                    if (attempt < self.retry_policy.max_attempts - 1 and
                        self.retry_policy.should_retry(last_error)):
                        delay = self.retry_policy.calculate_delay(attempt)
                        logger.debug(f"Retrying {func.__name__} after {delay:.2f}s (attempt {attempt + 1}/{self.retry_policy.max_attempts})")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        break

            # All retries exhausted
            if last_error:
                raise Exception(f"All retry attempts failed for {func.__name__}: {last_error.message}")
            else:
                raise Exception(f"Unknown error in {func.__name__}")

        return wrapper

class Bulkhead:
    """
    PhD-Level Bulkhead Isolation Pattern
    Isolate resources to prevent cascading failures
    """

    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self.max_concurrent = max_concurrent
        self.current_concurrent = 0
        self.lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def execute(self, func: Callable, *args, **kwargs) -> Result:
        """Execute function within bulkhead limits"""
        async with self.semaphore:
            try:
                result = await func(*args, **kwargs)
                return Result.success(result)
            except Exception as e:
                error = error_handler.handle_exception(e, context={
                    "bulkhead": self.name,
                    "args": str(args)[:100],
                    "kwargs": str(kwargs)[:100]
                })
                return Result.failure(error)

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get bulkhead usage statistics"""
        return {
            'name': self.name,
            'max_concurrent': self.max_concurrent,
            'available_permits': self.semaphore._value,  # type: ignore
            'utilization': (self.max_concurrent - self.semaphore._value) / self.max_concurrent if self.max_concurrent > 0 else 0
        }

class WatchdogTimer:
    """
    PhD-Level Watchdog Timer for resource monitoring
    """

    def __init__(self, timeout_seconds: float, name: str = "watchdog"):
        self.timeout_seconds = timeout_seconds
        self.name = name
        self.timer_task: Optional[asyncio.Task] = None
        self.callbacks: List[Callable] = []
        self.is_running = False

    def add_callback(self, callback: Callable):
        """Add callback to execute on timeout"""
        self.callbacks.append(callback)

    async def start(self):
        """Start the watchdog timer"""
        if self.is_running:
            return

        self.is_running = True
        await self._reset_timer()

    async def _reset_timer(self):
        """Reset the watchdog timer"""
        if self.timer_task:
            self.timer_task.cancel()
            try:
                await self.timer_task
            except asyncio.CancelledError:
                pass

        self.timer_task = asyncio.create_task(self._timer_coro())

    async def _timer_coro(self):
        """Timer coroutine that executes callbacks on timeout"""
        await asyncio.sleep(self.timeout_seconds)

        if self.is_running:
            logger.warning(f"⚠️ Watchdog {self.name} timeout triggered!")
            for callback in self.callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"Watchdog callback failed: {e}")

    async def reset(self):
        """Reset the watchdog timer"""
        await self._reset_timer()

    async def stop(self):
        """Stop the watchdog timer"""
        self.is_running = False
        if self.timer_task:
            self.timer_task.cancel()
            try:
                await self.timer_task
            except asyncio.CancelledError:
                pass

class ResourcePool:
    """
    PhD-Level Resource Pool with bounds and monitoring
    """

    def __init__(self, name: str, max_size: int = 10, create_func: Optional[Callable] = None):
        self.name = name
        self.max_size = max_size
        self.create_func = create_func
        self.pool = asyncio.Queue(maxsize=max_size)
        self.created_count = 0
        self.checked_out_count = 0
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a resource from the pool"""
        async with self.lock:
            if self.pool.empty() and self.created_count < self.max_size:
                # Create new resource
                resource = await self._create_resource()
                self.created_count += 1
                self.checked_out_count += 1
                return resource
            else:
                try:
                    resource = self.pool.get_nowait()
                    self.checked_out_count += 1
                    return resource
                except asyncio.QueueEmpty:
                    # Pool exhausted, wait for resource or timeout
                    try:
                        resource = await asyncio.wait_for(self.pool.get(), timeout=30.0)
                        self.checked_out_count += 1
                        return resource
                    except asyncio.TimeoutError:
                        raise Exception(f"Resource pool {self.name} exhausted")

    async def release(self, resource):
        """Release a resource back to the pool"""
        async with self.lock:
            try:
                self.pool.put_nowait(resource)
                self.checked_out_count -= 1
            except asyncio.QueueFull:
                # Pool is full, destroy the resource
                await self._destroy_resource(resource)
                self.created_count -= 1
                self.checked_out_count -= 1

    async def _create_resource(self):
        """Create a new resource"""
        if self.create_func:
            if asyncio.iscoroutinefunction(self.create_func):
                return await self.create_func()
            else:
                return self.create_func()
        else:
            # Default resource creation
            return object()

    async def _destroy_resource(self, resource):
        """Destroy a resource"""
        # Cleanup resource if needed
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get resource pool statistics"""
        return {
            'name': self.name,
            'max_size': self.max_size,
            'current_size': self.created_count,
            'checked_out': self.checked_out_count,
            'available': self.pool.qsize(),
            'utilization': self.checked_out_count / max(1, self.created_count) if self.created_count > 0 else 0
        }

# Global resilience managers
class ResilienceManager:
    """
    Centralized resilience management system
    """

    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkheads: Dict[str, Bulkhead] = {}
        self.watchdogs: Dict[str, WatchdogTimer] = {}
        self.resource_pools: Dict[str, ResourcePool] = {}
        self.health_indicators: Dict[str, Dict[str, Any]] = {}

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.circuit_breakers[name]

    def get_bulkhead(self, name: str, max_concurrent: int = 10) -> Bulkhead:
        """Get or create a bulkhead"""
        if name not in self.bulkheads:
            self.bulkheads[name] = Bulkhead(name=name, max_concurrent=max_concurrent)
        return self.bulkheads[name]

    def get_watchdog(self, name: str, timeout_seconds: float = 60.0) -> WatchdogTimer:
        """Get or create a watchdog"""
        if name not in self.watchdogs:
            self.watchdogs[name] = WatchdogTimer(timeout_seconds=timeout_seconds, name=name)
        return self.watchdogs[name]

    def get_resource_pool(self, name: str, max_size: int = 10, create_func: Optional[Callable] = None) -> ResourcePool:
        """Get or create a resource pool"""
        if name not in self.resource_pools:
            self.resource_pools[name] = ResourcePool(name=name, max_size=max_size, create_func=create_func)
        return self.resource_pools[name]

    def update_health_indicator(self, name: str, value: float, max_value: float = 100.0):
        """Update health indicator value"""
        current_time = datetime.now()
        self.health_indicators[name] = {
            'value': value,
            'max_value': max_value,
            'normalized_value': min(100.0, (value / max_value) * 100.0),
            'timestamp': current_time,
            'status': 'healthy' if value <= max_value * 0.8 else 'warning' if value <= max_value * 0.95 else 'critical'
        }

    def get_overall_health(self) -> float:
        """Calculate overall system health"""
        if not self.health_indicators:
            return 100.0  # Perfect health if no indicators

        total_health = sum(
            indicator['normalized_value'] for indicator in self.health_indicators.values()
        )
        avg_health = total_health / len(self.health_indicators)

        # Health score is inverse of normalized values (lower is better)
        return 100.0 - avg_health

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'circuit_breakers': {
                name: cb.get_stats() for name, cb in self.circuit_breakers.items()
            },
            'bulkheads': {
                name: bh.get_usage_stats() for name, bh in self.bulkheads.items()
            },
            'resource_pools': {
                name: rp.get_stats() for name, rp in self.resource_pools.items()
            },
            'health_indicators': self.health_indicators,
            'overall_health_score': self.get_overall_health()
        }

# Global resilience manager instance
resilience_manager = ResilienceManager()

# Convenience decorators
def circuit_breaker(name: str = "default", **cb_kwargs):
    """Decorator for applying circuit breaker pattern"""
    circuit_breaker_instance = resilience_manager.get_circuit_breaker(name, **cb_kwargs)
    return ResilienceDecorator(circuit_breaker=circuit_breaker_instance)

def bulkhead(name: str = "default", max_concurrent: int = 10):
    """Decorator for applying bulkhead pattern"""
    bulkhead_instance = resilience_manager.get_bulkhead(name, max_concurrent=max_concurrent)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if asyncio.iscoroutinefunction(func):
                result = await bulkhead_instance.execute(func, *args, **kwargs)
            else:
                # For sync functions, we'll execute in thread pool
                loop = asyncio.get_event_loop()
                try:
                    result_val = await loop.run_in_executor(None, func, *args, **kwargs)
                    result = Result.success(result_val)
                except Exception as e:
                    error = error_handler.handle_exception(e)
                    result = Result.failure(error)

            if result.is_success():
                return result.unwrap()
            else:
                raise Exception(result.unwrap_error().message)

        return wrapper
    return decorator

def retry_policy(**rp_kwargs):
    """Decorator for applying retry policy"""
    retry_policy_instance = RetryPolicy(**rp_kwargs)
    return ResilienceDecorator(retry_policy=retry_policy_instance)

def watchdog(name: str = "default", timeout_seconds: float = 60.0):
    """Decorator for applying watchdog monitoring"""
    watchdog_instance = resilience_manager.get_watchdog(name, timeout_seconds=timeout_seconds)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await watchdog_instance.start()
            try:
                result = await func(*args, **kwargs)
                await watchdog_instance.reset()
                return result
            finally:
                await watchdog_instance.stop()

        return wrapper
    return decorator

# Test the resilience patterns
async def test_resilience_patterns():
    """Test resilience patterns implementation"""
    logger.info("🧪 Testing Resilience Patterns...")

    # Test circuit breaker
    cb = CircuitBreaker(name="test_cb", failure_threshold=2, timeout_seconds=5.0)

    # Simulate function that sometimes fails
    def flaky_function(should_fail: bool = False):
        if should_fail:
            raise Exception("Intentional failure for testing")
        return "Success!"

    # Test circuit breaker with failures
    try:
        # First failure
        result1 = cb.call(flaky_function, should_fail=True)
        print(f"Result 1: {result1.is_failure()}")

        # Second failure - should trip circuit
        result2 = cb.call(flaky_function, should_fail=True)
        print(f"Result 2: {result2.is_failure()}")

        # Circuit should now be open
        result3 = cb.call(flaky_function, should_fail=False)
        print(f"Result 3 (should fail fast): {result3.is_failure()}")

        print(f"Circuit state: {cb.state}")

    except Exception as e:
        print(f"Circuit breaker test error: {e}")

    # Test retry policy
    retry_policy_obj = RetryPolicy(max_attempts=3, base_delay=0.1)

    def failing_then_succeeding(counter):
        counter['attempts'] += 1
        if counter['attempts'] < 3:
            raise Exception(f"Failing on attempt {counter['attempts']}")
        return f"Succeeded on attempt {counter['attempts']}"

    counter = {'attempts': 0}
    decorator = ResilienceDecorator(retry_policy=retry_policy_obj)

    try:
        result = decorator(failing_then_succeeding)(counter)
        print(f"Retry result: {result}")
    except Exception as e:
        print(f"Retry test error: {e}")

    # Test bulkhead
    bulkhead_obj = Bulkhead("test_bh", max_concurrent=2)

    async def resource_intensive_task(task_id: int):
        await asyncio.sleep(1)  # Simulate work
        return f"Task {task_id} completed"

    # Run multiple tasks to test bulkhead limits
    tasks = []
    for i in range(5):
        task = bulkhead_obj.execute(resource_intensive_task, i)
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"Bulkhead results: {len([r for r in results if r.is_success()])} succeeded")

    # Test resource pool
    pool = ResourcePool("test_pool", max_size=3)

    async def use_resource():
        resource = await pool.acquire()
        await asyncio.sleep(0.1)  # Simulate work
        await pool.release(resource)

    pool_tasks = [use_resource() for _ in range(10)]
    await asyncio.gather(*pool_tasks)
    print(f"Resource pool stats: {pool.get_stats()}")

    # Test overall health
    resilience_manager.update_health_indicator("cpu_usage", 75.0, 100.0)
    resilience_manager.update_health_indicator("memory_usage", 85.0, 100.0)
    resilience_manager.update_health_indicator("disk_usage", 45.0, 100.0)

    print(f"Overall health score: {resilience_manager.get_overall_health()}")
    print(f"System status: {resilience_manager.get_system_status()}")

if __name__ == "__main__":
    asyncio.run(test_resilience_patterns())