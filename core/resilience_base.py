# ==========================================================
# JARVIS v9.0 - Resilience Base Classes
# Base implementation of resilience patterns without dependencies
# ==========================================================

import asyncio
import time
import logging
import random
from enum import Enum
from typing import Callable, Any, Optional, Dict, List, Awaitable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock

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
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: float = 60.0,
        recovery_timeout: float = 30.0,
        success_threshold: int = 3,
        error_ratio_threshold: float = 0.5,
        name: str = "default",
        **kwargs
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout  # Alias for compatibility
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.error_ratio_threshold = error_ratio_threshold

        self.state = CircuitState.CLOSED
        self.metrics = CircuitMetrics()
        self.lock = Lock()
        self.recent_requests = []
        self.max_recent_requests = 100

    def _should_trip(self) -> bool:
        if self.metrics.consecutive_failures >= self.failure_threshold:
            return True
        total = self.metrics.total_requests
        if total >= 10:
            error_ratio = self.metrics.failure_count / total
            if error_ratio >= self.error_ratio_threshold:
                return True
        return False

    def _should_reset(self) -> bool:
        if self.state != CircuitState.OPEN:
            return False
        if (self.metrics.opened_time and
            datetime.now() - self.metrics.opened_time >= timedelta(seconds=self.timeout_seconds)):
            return True
        return False

    def _trip_circuit(self):
        self.state = CircuitState.OPEN
        self.metrics.opened_time = datetime.now()
        logger.warning(f"⚠️ Circuit breaker {self.name} TRIPPED - now OPEN")

    def _reset_circuit(self):
        self.state = CircuitState.HALF_OPEN
        logger.info(f"🔄 Circuit breaker {self.name} transitioning to HALF_OPEN")

    def _handle_success(self):
        self.state = CircuitState.CLOSED
        self.metrics.success_count += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_failure_time = None

    def _handle_failure(self):
        self.metrics.failure_count += 1
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure_time = datetime.now()
        if self._should_trip():
            self._trip_circuit()

    def _record_request(self, success: bool):
        self.metrics.total_requests += 1
        self.recent_requests.append({'success': success, 'timestamp': time.time()})
        if len(self.recent_requests) > self.max_recent_requests:
            self.recent_requests = self.recent_requests[-self.max_recent_requests:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'state': self.state.value,
            'metrics': {
                'success_count': self.metrics.success_count,
                'failure_count': self.metrics.failure_count,
                'consecutive_failures': self.metrics.consecutive_failures,
                'total_requests': self.metrics.total_requests,
                'success_rate': self.metrics.success_count / max(1, self.metrics.total_requests) if self.metrics.total_requests > 0 else 0,
                'opened_time': self.metrics.opened_time.isoformat() if self.metrics.opened_time else None
            }
        }

    async def __aenter__(self):
        with self.lock:
            if self.state == CircuitState.OPEN and self._should_reset():
                self._reset_circuit()
            if self.state == CircuitState.OPEN:
                raise Exception(f"Circuit breaker {self.name} is OPEN")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        with self.lock:
            if exc_type is None:
                self._handle_success()
                self._record_request(True)
            else:
                self._handle_failure()
                self._record_request(False)

class RetryPolicy:
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        retryable_errors: Optional[List[Any]] = None,
        **kwargs
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retryable_errors = retryable_errors

    def calculate_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (self.multiplier ** attempt), self.max_delay)
        if self.jitter:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        return max(0, delay)

class Bulkhead:
    def __init__(self, name: str = "default", max_concurrent: int = 10, max_queue_size: int = 10, **kwargs):
        self.name = name
        self.max_concurrent = max_concurrent
        self.max_queue_size = max_queue_size
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def __aenter__(self):
        await self.semaphore.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.semaphore.release()

    def get_usage_stats(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'max_concurrent': self.max_concurrent,
            'available_permits': self.semaphore._value if hasattr(self.semaphore, '_value') else 0,
            'utilization': (self.max_concurrent - (self.semaphore._value if hasattr(self.semaphore, '_value') else 0)) / self.max_concurrent if self.max_concurrent > 0 else 0
        }

class WatchdogTimer:
    def __init__(self, timeout: float = 60.0, grace_period: float = 5.0, name: str = "watchdog", **kwargs):
        self.timeout = timeout
        self.timeout_seconds = timeout # Alias
        self.grace_period = grace_period
        self.name = name
        self.timer_task: Optional[asyncio.Task] = None
        self.is_running = False

    async def acquire_timer(self):
        self.is_running = True
        self.timer_task = asyncio.create_task(asyncio.sleep(self.timeout))
        return self.timer_task

    def release_timer(self, task):
        self.is_running = False
        if task:
            task.cancel()

class ResourcePool:
    def __init__(self, name: str = "default", max_size: int = 10, max_resources: int = 10, create_func: Optional[Callable] = None, **kwargs):
        self.name = name
        self.max_size = max_resources # Prefer max_resources if provided
        self.create_func = create_func
        self.pool = asyncio.Queue(maxsize=self.max_size)

    async def acquire(self):
        async with self.lock:
            if self.pool.empty() and self.created_count < self.max_size:
                resource = await self._create_resource()
                self.created_count += 1
                self.checked_out_count += 1
                return resource
            else:
                resource = await self.pool.get()
                self.checked_out_count += 1
                return resource

    async def release(self, resource):
        async with self.lock:
            try:
                self.pool.put_nowait(resource)
                self.checked_out_count -= 1
            except asyncio.QueueFull:
                self.created_count -= 1
                self.checked_out_count -= 1

    async def _create_resource(self):
        if self.create_func:
            return await self.create_func() if asyncio.iscoroutinefunction(self.create_func) else self.create_func()
        return object()

    def get_stats(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'max_size': self.max_size,
            'current_size': getattr(self, 'created_count', 0),
            'checked_out': getattr(self, 'checked_out_count', 0),
            'available': self.pool.qsize()
        }

# Global resilience managers
class ResilienceManager:
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.bulkheads: Dict[str, Bulkhead] = {}
        self.watchdogs: Dict[str, WatchdogTimer] = {}
        self.resource_pools: Dict[str, ResourcePool] = {}
        self.health_indicators: Dict[str, Dict[str, Any]] = {}

    def get_circuit_breaker(self, name: str, **kwargs) -> CircuitBreaker:
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(name=name, **kwargs)
        return self.circuit_breakers[name]

    def get_bulkhead(self, name: str, max_concurrent: int = 10, **kwargs) -> Bulkhead:
        if name not in self.bulkheads:
            self.bulkheads[name] = Bulkhead(name=name, max_concurrent=max_concurrent, **kwargs)
        return self.bulkheads[name]

    def get_watchdog(self, name: str, timeout: float = 60.0, **kwargs) -> WatchdogTimer:
        if name not in self.watchdogs:
            self.watchdogs[name] = WatchdogTimer(timeout=timeout, name=name, **kwargs)
        return self.watchdogs[name]

    def get_resource_pool(self, name: str, max_size: int = 10, create_func: Optional[Callable] = None, **kwargs) -> ResourcePool:
        if name not in self.resource_pools:
            self.resource_pools[name] = ResourcePool(name=name, max_size=max_size, create_func=create_func, **kwargs)
        return self.resource_pools[name]

    def update_health_indicator(self, name: str, value: float, max_value: float = 100.0):
        current_time = datetime.now()
        self.health_indicators[name] = {
            'value': value,
            'max_value': max_value,
            'normalized_value': min(100.0, (value / max_value) * 100.0),
            'timestamp': current_time,
            'status': 'healthy' if value <= max_value * 0.8 else 'warning' if value <= max_value * 0.95 else 'critical'
        }

    def get_overall_health(self) -> float:
        if not self.health_indicators:
            return 100.0
        total_health = sum(indicator['normalized_value'] for indicator in self.health_indicators.values())
        avg_health = total_health / len(self.health_indicators)
        return 100.0 - avg_health

    def get_system_status(self) -> Dict[str, Any]:
        return {
            'circuit_breakers': {name: cb.get_stats() for name, cb in self.circuit_breakers.items()},
            'bulkheads': {name: bh.get_usage_stats() for name, bh in self.bulkheads.items()},
            'resource_pools': {name: rp.get_stats() for name, rp in self.resource_pools.items()},
            'health_indicators': self.health_indicators,
            'overall_health_score': self.get_overall_health()
        }
