"""
==========================================================
JARVIS - PhD-Level Error Handling & Resilience System
==========================================================
Structured error types, propagation, and recovery strategies
Based on Railway-Oriented Programming and Result types
Plus circuit breakers, retries, bulkheads, and resource pools
==========================================================
"""

from typing import Optional, Any, Callable, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import logging
import traceback
from datetime import datetime
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')
E = TypeVar('E')

# Import resilience base classes to avoid circular dependency
from .resilience_base import (
    CircuitBreaker,
    RetryPolicy,
    Bulkhead,
    WatchdogTimer,
    ResourcePool,
    ResilienceManager
)

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"           # Recoverable, no user impact
    MEDIUM = "medium"     # Degraded functionality
    HIGH = "high"         # Service disruption
    CRITICAL = "critical" # System failure


class ErrorCategory(Enum):
    """Error categories for classification"""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    PROCESSING = "processing"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    MEMORY = "memory"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


@dataclass
class JarvisError:
    """Structured error type"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Optional[str] = None
    user_message: Optional[str] = None
    timestamp: datetime = None
    traceback: Optional[str] = None
    context: Optional[dict] = None
    recoverable: bool = True

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

        if self.user_message is None:
            self.user_message = self._generate_user_message()

    def _generate_user_message(self) -> str:
        """Generate user-friendly error message"""
        if self.severity == ErrorSeverity.CRITICAL:
            return "⚠️ JARVIS is experiencing critical issues. Please try again later."
        elif self.severity == ErrorSeverity.HIGH:
            return "⚠️ I'm having trouble processing your request. Please try again."
        elif self.severity == ErrorSeverity.MEDIUM:
            return "⚠️ I encountered an issue but I'm working on it. Please wait a moment."
        else:
            return "⚠️ Minor issue detected, continuing..."

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
            "user_message": self.user_message,
            "timestamp": self.timestamp.isoformat(),
            "recoverable": self.recoverable,
            "context": self.context
        }


class Result(Generic[T, E]):
    """
    Result type for Railway-Oriented Programming
    Either Success(value) or Failure(error)
    """

    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        self._value = value
        self._error = error
        self._is_success = error is None

    @staticmethod
    def success(value: T) -> 'Result[T, E]':
        """Create success result"""
        return Result(value=value)

    @staticmethod
    def failure(error: E) -> 'Result[T, E]':
        """Create failure result"""
        return Result(error=error)

    def is_success(self) -> bool:
        """Check if result is success"""
        return self._is_success

    def is_failure(self) -> bool:
        """Check if result is failure"""
        return not self._is_success

    def unwrap(self) -> T:
        """Get value or raise exception"""
        if self._is_success:
            return self._value
        raise ValueError(f"Called unwrap on failure: {self._error}")

    def unwrap_or(self, default: T) -> T:
        """Get value or default"""
        return self._value if self._is_success else default

    def unwrap_error(self) -> E:
        """Get error or raise exception"""
        if not self._is_success:
            return self._error
        raise ValueError("Called unwrap_error on success")

    def map(self, fn: Callable[[T], Any]) -> 'Result':
        """Map success value"""
        if self._is_success:
            try:
                return Result.success(fn(self._value))
            except Exception as e:
                return Result.failure(e)
        return self

    def map_error(self, fn: Callable[[E], Any]) -> 'Result':
        """Map error value"""
        if not self._is_success:
            return Result.failure(fn(self._error))
        return self

    def and_then(self, fn: Callable[[T], 'Result']) -> 'Result':
        """Chain operations (flatMap)"""
        if self._is_success:
            try:
                return fn(self._value)
            except Exception as e:
                return Result.failure(e)
        return self


class ErrorHandler:
    """
    PhD-Level Error Handler
    - Automatic error classification
    - Recovery strategies
    - Error aggregation
    - Telemetry
    """

    def __init__(self):
        self.error_history = []
        self.max_history = 1000

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[dict] = None,
        user_facing: bool = True
    ) -> JarvisError:
        """
        Handle exception and convert to JarvisError
        """
        # Classify error
        category = self._classify_error(exception)
        severity = self._determine_severity(exception, category)

        # Create structured error
        error = JarvisError(
            category=category,
            severity=severity,
            message=str(exception),
            details=traceback.format_exc(),
            traceback=traceback.format_exc(),
            context=context,
            recoverable=self._is_recoverable(exception, category)
        )

        # Log error
        self._log_error(error)

        # Store in history
        self._store_error(error)

        return error

    def _classify_error(self, exception: Exception) -> ErrorCategory:
        """Classify error by type"""
        error_type = type(exception).__name__

        if 'Connection' in error_type or 'Network' in error_type:
            return ErrorCategory.NETWORK
        elif 'Auth' in error_type or 'Permission' in error_type:
            return ErrorCategory.AUTHENTICATION
        elif 'Validation' in error_type or 'ValueError' in error_type:
            return ErrorCategory.VALIDATION
        elif 'Timeout' in error_type:
            return ErrorCategory.TIMEOUT
        elif 'Memory' in error_type:
            return ErrorCategory.MEMORY
        elif 'API' in error_type or 'HTTP' in error_type:
            return ErrorCategory.EXTERNAL_API
        else:
            return ErrorCategory.UNKNOWN

    def _determine_severity(self, exception: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Determine error severity"""
        # Critical errors
        if category == ErrorCategory.MEMORY:
            return ErrorSeverity.CRITICAL
        if isinstance(exception, (SystemError, MemoryError)):
            return ErrorSeverity.CRITICAL

        # High severity
        if category in [ErrorCategory.AUTHENTICATION, ErrorCategory.DATABASE]:
            return ErrorSeverity.HIGH

        # Medium severity
        if category in [ErrorCategory.NETWORK, ErrorCategory.EXTERNAL_API, ErrorCategory.TIMEOUT]:
            return ErrorSeverity.MEDIUM

        # Low severity
        return ErrorSeverity.LOW

    def _is_recoverable(self, exception: Exception, category: ErrorCategory) -> bool:
        """Check if error is recoverable"""
        # Non-recoverable errors
        if isinstance(exception, (SystemError, MemoryError)):
            return False

        if category == ErrorCategory.AUTHENTICATION:
            return False

        # Most errors are recoverable with retry
        return True

    def _log_error(self, error: JarvisError):
        """Log error with appropriate level"""
        log_message = f"[{error.category.value}] {error.message}"

        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={"error": error.to_dict()})
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={"error": error.to_dict()})
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={"error": error.to_dict()})
        else:
            logger.info(log_message, extra={"error": error.to_dict()})

    def _store_error(self, error: JarvisError):
        """Store error in history"""
        self.error_history.append(error)

        # Trim history if too large
        if len(self.error_history) > self.max_history:
            self.error_history = self.error_history[-self.max_history:]

    def get_error_stats(self) -> dict:
        """Get error statistics"""
        if not self.error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recent_errors": []
            }

        # Count by category
        by_category = {}
        for error in self.error_history:
            cat = error.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

        # Count by severity
        by_severity = {}
        for error in self.error_history:
            sev = error.severity.value
            by_severity[sev] = by_severity.get(sev, 0) + 1

        # Recent errors (last 10)
        recent = [e.to_dict() for e in self.error_history[-10:]]

        return {
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": recent
        }


class ResilientErrorHandler(ErrorHandler):
    """
    Enhanced error handler with resilience patterns:
    - Circuit breakers
    - Retry policies
    - Bulkhead isolation
    - Resource pooling
    - Watchdog timers
    """

    def __init__(self):
        super().__init__()

        # Global resilience manager
        self.resilience_manager = ResilienceManager()

        # Default retry policy
        self.default_retry_policy = RetryPolicy(
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            multiplier=2.0,
            jitter=True
        )

        # Default bulkheads for different system components
        self.bulkheads = {
            'llm': Bulkhead(max_concurrent=5, max_queue_size=10),
            'memory': Bulkhead(max_concurrent=10, max_queue_size=20),
            'speculative_decoder': Bulkhead(max_concurrent=3, max_queue_size=5),
            'system2_thinking': Bulkhead(max_concurrent=2, max_queue_size=3),
            'security': Bulkhead(max_concurrent=20, max_queue_size=50),
            'workflow': Bulkhead(max_concurrent=5, max_queue_size=10),
            'default': Bulkhead(max_concurrent=15, max_queue_size=30)
        }

        # Default circuit breakers
        self.circuit_breakers = {
            'llm': CircuitBreaker(
                failure_threshold=5,
                timeout=60,
                recovery_timeout=30
            ),
            'memory': CircuitBreaker(
                failure_threshold=10,
                timeout=120,
                recovery_timeout=60
            ),
            'speculative_decoder': CircuitBreaker(
                failure_threshold=3,
                timeout=30,
                recovery_timeout=15
            ),
            'system2_thinking': CircuitBreaker(
                failure_threshold=3,
                timeout=30,
                recovery_timeout=15
            ),
            'network_call': CircuitBreaker(
                failure_threshold=5,
                timeout=60,
                recovery_timeout=30
            ),
            'default': CircuitBreaker(
                failure_threshold=5,
                timeout=60,
                recovery_timeout=30
            )
        }

        # Default watchdog timers
        self.watchdogs = {
            'llm_call': WatchdogTimer(timeout=60, grace_period=5),
            'memory_operation': WatchdogTimer(timeout=30, grace_period=2),
            'speculative_decode': WatchdogTimer(timeout=120, grace_period=10),
            'system2_reason': WatchdogTimer(timeout=300, grace_period=20),
            'workflow_execution': WatchdogTimer(timeout=600, grace_period=30),
            'default': WatchdogTimer(timeout=60, grace_period=5)
        }

        # Default resource pools
        self.resource_pools = {
            'mcts_nodes': ResourcePool(
                max_resources=100,
                acquire_timeout=5.0,
                health_check_interval=30
            ),
            'processing_slots': ResourcePool(
                max_resources=50,
                acquire_timeout=10.0,
                health_check_interval=60
            ),
            'api_connections': ResourcePool(
                max_resources=20,
                acquire_timeout=5.0,
                health_check_interval=15
            ),
            'default': ResourcePool(
                max_resources=30,
                acquire_timeout=5.0,
                health_check_interval=30
            )
        }

    def resilient_call(self, component: str = 'default', with_circuit_breaker: bool = True,
                      with_retry: bool = True, with_bulkhead: bool = True,
                      with_watchdog: bool = True):
        """
        Decorator to make a function resilient with configurable patterns
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Get appropriate resilience components
                cb = self.circuit_breakers.get(component, self.circuit_breakers['default']) if with_circuit_breaker else None
                bh = self.bulkheads.get(component, self.bulkheads['default']) if with_bulkhead else None
                wd = self.watchdogs.get(f'{component}_operation', self.watchdogs['default']) if with_watchdog else None
                retry_policy = self.default_retry_policy if with_retry else None

                # Apply bulkhead if enabled
                if bh:
                    async with bh:
                        return await self._execute_with_resilience(func, *args, **kwargs,
                                                                 circuit_breaker=cb,
                                                                 retry_policy=retry_policy,
                                                                 watchdog=wd)
                else:
                    return await self._execute_with_resilience(func, *args, **kwargs,
                                                             circuit_breaker=cb,
                                                             retry_policy=retry_policy,
                                                             watchdog=wd)

            return wrapper
        return decorator

    def bulkhead_protect(self, component: str = 'default'):
        """
        Decorator to apply bulkhead isolation to a function
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                bulkhead = self.bulkheads.get(component, self.bulkheads['default'])

                async with bulkhead:
                    return await func(*args, **kwargs)

            return wrapper
        return decorator

    def circuit_breaker_protect(self, component: str = 'default'):
        """
        Decorator to apply circuit breaker to a function
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cb = self.circuit_breakers.get(component, self.circuit_breakers['default'])

                async with cb:
                    return await func(*args, **kwargs)

            return wrapper
        return decorator

    async def _execute_with_resilience(self, func: Callable, *args,
                                     circuit_breaker: 'CircuitBreaker' = None,
                                     retry_policy: 'RetryPolicy' = None,
                                     watchdog: 'WatchdogTimer' = None,
                                     **kwargs):
        """
        Execute a function with resilience patterns
        """
        last_exception = None

        # Determine max attempts based on retry policy
        max_attempts = retry_policy.max_attempts if retry_policy else 1

        for attempt in range(max_attempts):
            try:
                # Acquire watchdog timer if enabled
                if watchdog:
                    timer_task = await watchdog.acquire_timer()

                    try:
                        # Execute the function with timeout if watchdog is enabled
                        if watchdog:
                            result = await asyncio.wait_for(
                                func(*args, **kwargs),
                                timeout=watchdog.timeout
                            )
                        else:
                            result = await func(*args, **kwargs)

                        # Release watchdog timer on success
                        if watchdog:
                            watchdog.release_timer(timer_task)

                        return result

                    except asyncio.TimeoutError:
                        # Timeout occurred, release timer and continue to retry
                        if watchdog:
                            watchdog.release_timer(timer_task)
                        raise TimeoutError(f"Operation timed out after {watchdog.timeout}s")
                else:
                    # Execute without watchdog timeout
                    if circuit_breaker:
                        async with circuit_breaker:
                            if retry_policy:
                                result = await func(*args, **kwargs)
                            else:
                                result = await func(*args, **kwargs)
                    else:
                        if retry_policy:
                            result = await func(*args, **kwargs)
                        else:
                            result = await func(*args, **kwargs)

                    return result

            except Exception as e:
                last_exception = e

                # Check if this is a retryable error
                if retry_policy and self._is_retryable_error(e):
                    if attempt < max_attempts - 1:
                        # Calculate delay with exponential backoff and jitter
                        delay = self._calculate_retry_delay(retry_policy, attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                    else:
                        # Last attempt, raise the exception
                        logger.error(f"All {max_attempts} attempts failed. Last error: {e}")
                        raise
                else:
                    # Not retryable, raise immediately
                    raise

        # This shouldn't be reached, but just in case
        if last_exception:
            raise last_exception

    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable
        """
        retryable_errors = (
            TimeoutError,
            ConnectionError,
            asyncio.TimeoutError,
        )

        # Check if it's a retryable error type
        if isinstance(error, retryable_errors):
            return True

        # Check for specific error messages that indicate retryable conditions
        error_msg = str(error).lower()
        retryable_keywords = [
            'timeout',
            'connection refused',
            'connection reset',
            'network error',
            'temporary failure',
            'rate limit',
            'throttled'
        ]

        return any(keyword in error_msg for keyword in retryable_keywords)

    def _calculate_retry_delay(self, retry_policy: 'RetryPolicy', attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff and jitter
        """
        base_delay = retry_policy.base_delay
        multiplier = retry_policy.multiplier

        # Calculate exponential backoff
        delay = base_delay * (multiplier ** attempt)

        # Cap the delay at max_delay
        delay = min(delay, retry_policy.max_delay)

        # Add jitter if enabled
        if retry_policy.jitter:
            import random
            jitter = random.uniform(-0.1, 0.1) * delay
            delay += jitter
            delay = max(0, delay)  # Ensure delay is non-negative

        return delay

    async def execute_with_resource_pool(
        self,
        resource_type: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute a function with resource pool management
        """
        resource_pool = self.resource_pools.get(resource_type)
        if not resource_pool:
            # Use default pool if specific type not found
            resource_pool = self.resource_pools.get('default')

        if not resource_pool:
            raise ValueError(f"No resource pool available for type: {resource_type}")

        resource = await resource_pool.acquire()
        try:
            result = await func(*args, **kwargs)
            resource_pool.report_success(resource)
            return result
        except Exception as e:
            resource_pool.report_failure(resource)
            raise
        finally:
            resource_pool.release(resource)

    def get_health_status(self):
        """
        Get comprehensive health status including resilience metrics
        """
        import time

        health_status = {
            'overall_status': 'healthy',
            'timestamp': time.time(),
            'components': {},
            'resilience_metrics': {
                'resource_pools': {},
                'bulkheads': {},
                'circuit_breakers': {}
            }
        }

        # Check resource pools
        for resource_type, pool in self.resource_pools.items():
            stats = pool.get_stats()
            utilization = (stats['total'] - stats['available']) / stats['total'] if stats['total'] > 0 else 0
            health_status['resilience_metrics']['resource_pools'][resource_type] = {
                'utilization': utilization,
                'available': stats['available'],
                'total': stats['total'],
                'health': 'warning' if utilization > 0.8 else 'healthy'
            }
            if utilization > 0.9:
                health_status['overall_status'] = 'degraded'

        # Check bulkheads
        for component, bulkhead in self.bulkheads.items():
            stats = bulkhead.get_stats()
            utilization = stats['concurrent'] / stats['max_concurrent'] if stats['max_concurrent'] > 0 else 0
            health_status['resilience_metrics']['bulkheads'][component] = {
                'utilization': utilization,
                'active': stats['concurrent'],
                'max': stats['max_concurrent'],
                'queue_utilization': stats['queue_size'] / stats['max_queue_size'] if stats['max_queue_size'] > 0 else 0,
                'health': 'warning' if utilization > 0.8 or stats['queue_size'] > stats['max_queue_size'] * 0.8 else 'healthy'
            }
            if utilization > 0.9 or stats['queue_size'] > stats['max_queue_size'] * 0.9:
                health_status['overall_status'] = 'degraded'

        # Check circuit breakers
        for component, cb in self.circuit_breakers.items():
            stats = cb.get_stats()
            state = "CLOSED" if cb.state == cb.State.CLOSED else "OPEN" if cb.state == cb.State.OPEN else "HALF_OPEN"
            health_status['resilience_metrics']['circuit_breakers'][component] = {
                'state': state,
                'failures': stats['failure_count'],
                'threshold': cb.failure_threshold,
                'health': 'critical' if state == 'OPEN' else 'warning' if stats['failure_count'] > cb.failure_threshold * 0.7 else 'healthy'
            }
            if state == 'OPEN':
                health_status['overall_status'] = 'degraded'

        return health_status


# Global error handler instance with resilience
error_handler = ResilientErrorHandler()


def safe_execute(fn: Callable, *args, **kwargs) -> Result:
    """
    Execute function safely and return Result
    """
    try:
        result = fn(*args, **kwargs)
        return Result.success(result)
    except Exception as e:
        error = error_handler.handle_exception(e, context={
            "function": fn.__name__,
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100]
        })
        return Result.failure(error)


async def safe_execute_async(fn: Callable, *args, **kwargs) -> Result:
    """
    Execute async function safely and return Result
    """
    try:
        result = await fn(*args, **kwargs)
        return Result.success(result)
    except Exception as e:
        error = error_handler.handle_exception(e, context={
            "function": fn.__name__,
            "args": str(args)[:100],
            "kwargs": str(kwargs)[:100]
        })
        return Result.failure(error)


def with_circuit_breaker(component: str = 'default'):
    """Decorator to add circuit breaker to a function"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.circuit_breaker_protect(component)(func)(*args, **kwargs)
        return wrapper
    return decorator


def with_bulkhead(component: str = 'default'):
    """Decorator to add bulkhead isolation to a function"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.bulkhead_protect(component)(func)(*args, **kwargs)
        return wrapper
    return decorator


def with_resilience(component: str = 'default', with_circuit_breaker: bool = True,
                  with_retry: bool = True, with_bulkhead: bool = True,
                  with_watchdog: bool = True):
    """Decorator to add full resilience to a function"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.resilient_call(
                component, with_circuit_breaker, with_retry,
                with_bulkhead, with_watchdog
            )(func)(*args, **kwargs)
        return wrapper
    return decorator


def with_resource_pool(resource_type: str):
    """Decorator to manage resource pool for a function"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await error_handler.execute_with_resource_pool(
                resource_type, func, *args, **kwargs
            )
        return wrapper
    return decorator


# Test
if __name__ == "__main__":
    # Test error handling
    def failing_function():
        raise ValueError("Test error")

    result = safe_execute(failing_function)

    if result.is_failure():
        error = result.unwrap_error()
        print(f"Error: {error.message}")
        print(f"User message: {error.user_message}")
        print(f"Category: {error.category.value}")
        print(f"Severity: {error.severity.value}")

    # Test stats
    print("\nError Stats:")
    print(error_handler.get_error_stats())
