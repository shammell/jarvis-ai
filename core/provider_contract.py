"""
Provider Contracts - Abstract base classes for provider adapters and registry.

This module defines the contract interface that all providers must implement,
enabling deterministic multi-target provider routing for compiled execution plans.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Health status of a provider."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ProviderCapability(Enum):
    """Capabilities a provider can execute."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    SUPABASE = "supabase"
    DEPLOYMENT = "deployment"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"
    SYSTEM = "system"
    SECURITY = "security"


@dataclass
class ProviderInfo:
    """Information about a provider."""
    id: str
    name: str
    status: ProviderStatus = ProviderStatus.HEALTHY
    capabilities: Set[ProviderCapability] = field(default_factory=set)
    is_primary: bool = False
    rate_limit: Optional[int] = None  # Requests per minute
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __hash__(self):
        return hash(self.id)


@dataclass
class ProviderHealthCheck:
    """Health check result for a provider."""
    provider_id: str
    is_healthy: bool
    latency_ms: Optional[float] = None
    error_message: Optional[str] = None
    timestamp: float = field(default_factory=lambda: __import__('time').time())


class ProviderContract(ABC):
    """
    Abstract base class defining the contract all provider adapters must implement.

    Providers are responsible for executing specific types of tasks:
    - Frontend development
    - Backend development
    - Database operations
    - Supabase-specific operations
    - Deployment tasks
    - Testing
    - Infrastructure management
    - System operations
    - Security operations
    """

    @abstractmethod
    def provider_info(self) -> ProviderInfo:
        """
        Return information about this provider.

        RATIONALE: Centralized provider metadata is required for the
        CodingExecutionRouter to make health-aware and capability-based
        routing decisions in multi-agent workflows.

        Returns:
            ProviderInfo with id, name, status, capabilities, and metadata
        """
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a compiled task from the execution plan.

        RATIONALE: Standardized task execution allows for deterministic
        behavior across different provider implementations (Claude, local, etc).

        Args:
            task: Compiled task dict with 'type', 'params', and 'context'

        Returns:
            Execution result dict with 'success', 'output', and 'metrics'

        Raises:
            ProviderUnavailableError: If provider cannot execute the task
            ProviderError: If execution fails
        """
        pass

    @abstractmethod
    async def check_health(self) -> ProviderHealthCheck:
        """
        Perform health check on the provider.

        RATIONALE: Real-time health monitoring prevents the router from
        assigning critical tasks to degraded or offline providers.

        Returns:
            ProviderHealthCheck with status and latency information
        """
        pass

    @abstractmethod
    def can_handle(self, task_type: str) -> bool:
        """
        Check if this provider can handle a specific task type.

        RATIONALE: Capability-based filtering ensures that providers only
        receive tasks they are technically equipped to handle.

        Args:
            task_type: Type identifier (e.g., 'frontend', 'backend', 'supabase')

        Returns:
            True if provider can handle this task type
        """
        pass

    @abstractmethod
    async def get_quota(self) -> Dict[str, Any]:
        """
        Get current quota information for rate limiting.

        RATIONALE: Active quota tracking prevents 429 Rate Limit errors by
        allowing the system to switch providers before exhaustion.

        Returns:
            Dict with 'remaining', 'limit', 'reset_at' keys
        """
        pass


class ClaudeCodeProvider(ProviderContract):
    """
    Primary provider implementation for Claude Code operations.

    This is the default provider for most development tasks when Claude Code
    runtime is available. It handles frontend, backend, Supabase, and system tasks.

    Features:
    - Primary provider with full capability set
    - Health-aware routing decisions
    - Quota tracking for rate limiting
    - Deterministic fallback behavior
    """

    def __init__(
        self,
        provider_id: str = "claude-code",
        name: str = "Claude Code Provider",
        is_primary: bool = True,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self._info = ProviderInfo(
            id=provider_id,
            name=name,
            is_primary=is_primary,
            capabilities=set(
                ProviderCapability(c.lower()) for c in capabilities or [
                    "frontend", "backend", "supabase", "system",
                    "testing", "infrastructure"
                ]
            ),
            metadata=metadata or {}
        )
        self._quota = {
            "remaining": 1000,
            "limit": 1000,
            "reset_at": __import__('time').time() + 3600
        }
        self._last_health_check: Optional[ProviderHealthCheck] = None

    def provider_info(self) -> ProviderInfo:
        """Return provider information."""
        return self._info

    def can_handle(self, task_type: str) -> bool:
        """Check if provider can handle task type."""
        capability = ProviderCapability(task_type.lower())
        return capability in self._info.capabilities

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a compiled task.

        This is a mock implementation for routing - actual execution
        happens through the orchestrator's tool execution system.
        """
        task_type = task.get("type", "unknown")
        params = task.get("params", {})

        logger.info(f"ClaudeCodeProvider executing task: {task_type}")

        # Simulate task execution
        return {
            "success": True,
            "provider_id": self._info.id,
            "task_id": task.get("id"),
            "output": {
                "status": "completed",
                "task_type": task_type,
                "params_used": params,
                "execution_time_ms": params.get("estimated_time_ms", 100)
            },
            "metrics": {
                "tokens_used": 0,
                "steps_completed": 1
            },
            "timestamp": __import__('time').time()
        }

    async def check_health(self) -> ProviderHealthCheck:
        """
        Perform health check.

        Simulates health check - in production this would verify
        actual Claude Code connectivity.
        """
        import time

        # Simulate health check latency
        latency = 25.0  # 25ms

        self._last_health_check = ProviderHealthCheck(
            provider_id=self._info.id,
            is_healthy=True,
            latency_ms=latency,
            timestamp=time.time()
        )

        self._info.status = ProviderStatus.HEALTHY if latency < 100 else ProviderStatus.DEGRADED
        return self._last_health_check

    async def get_quota(self) -> Dict[str, Any]:
        """Return current quota information."""
        return self._quota.copy()


class ProviderRegistry:
    """
    Central registry for provider discovery and lookup.

    Manages:
    - Provider registration/unregistration
    - Health-aware provider selection
    - Capability-based routing
    - Deterministic fallback chains
    """

    _instance: Optional['ProviderRegistry'] = None

    def __new__(cls):
        """Singleton pattern for registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, '_initialized', False):
            return

        import threading
        self._lock = threading.Lock()
        self._providers: Dict[str, ProviderContract] = {}
        self._by_capability: Dict[ProviderCapability, List[str]] = {
            cap: [] for cap in ProviderCapability
        }
        self._initialized = True

    def register_provider(self, provider: ProviderContract) -> None:
        """
        Register a provider in the registry.

        Args:
            provider: Provider implementing ProviderContract
        """
        info = provider.provider_info()

        with self._lock:
            self._providers[info.id] = provider

            # Index by capability
            for cap in info.capabilities:
                self._by_capability[cap].append(info.id)

            logger.info(f"Registered provider: {info.name} ({info.id})")

    def unregister_provider(self, provider_id: str) -> bool:
        """
        Unregister a provider from the registry.

        Args:
            provider_id: ID of provider to unregister

        Returns:
            True if provider was found and unregistered
        """
        with self._lock:
            if provider_id not in self._providers:
                return False

            provider = self._providers.pop(provider_id)
            info = provider.provider_info()

            # Remove from capability index
            for cap in info.capabilities:
                if info.id in self._by_capability[cap]:
                    self._by_capability[cap].remove(info.id)

            logger.info(f"Unregistered provider: {info.name}")
            return True

    def get_provider(self, provider_id: str) -> Optional[ProviderContract]:
        """
        Get a provider by ID.

        Args:
            provider_id: ID of provider to retrieve

        Returns:
            Provider instance or None if not found
        """
        return self._providers.get(provider_id)

    def get_providers_for_capability(
        self,
        capability: ProviderCapability,
        healthy_only: bool = True
    ) -> List[ProviderContract]:
        """
        Get all providers that can handle a specific capability.

        Args:
            capability: Capability to filter by
            healthy_only: If True, only return healthy providers

        Returns:
            List of providers ordered by preference
        """
        with self._lock:
            provider_ids = self._by_capability.get(capability, [])

        if not provider_ids:
            return []

        providers = []
        for pid in provider_ids:
            provider = self._providers.get(pid)
            if provider and (not healthy_only or provider.provider_info().status == ProviderStatus.HEALTHY):
                providers.append(provider)

        # Sort: primary provider first, then by status
        def sort_key(p: ProviderContract):
            info = p.provider_info()
            if info.is_primary:
                return (0,)
            elif info.status == ProviderStatus.HEALTHY:
                return (1,)
            elif info.status == ProviderStatus.DEGRADED:
                return (2,)
            return (3,)

        return sorted(providers, key=sort_key)

    async def select_primary_provider(
        self,
        task_type: str
    ) -> Optional[ProviderContract]:
        """
        Select the primary (preferred) provider for a task type.

        Implements deterministic selection:
        1. Must support the required capability
        2. Must be healthy
        3. Primary provider preferred over fallbacks

        Args:
            task_type: Type of task to route

        Returns:
            Best provider for the task or None
        """
        try:
            capability = ProviderCapability(task_type.lower())
        except ValueError:
            return None

        providers = self.get_providers_for_capability(capability, healthy_only=True)

        for provider in providers:
            if provider.provider_info().is_primary:
                return provider

        # Return first healthy provider if no primary
        return providers[0] if providers else None

    async def get_all_providers(self) -> List[ProviderContract]:
        """Get all registered providers."""
        return list(self._providers.values())

    async def health_check_all(self) -> Dict[str, ProviderHealthCheck]:
        """
        Perform health checks on all providers.

        Returns:
            Dict mapping provider_id to health check result
        """
        results = {}
        for provider in await self.get_all_providers():
            health = await provider.check_health()
            results[provider.provider_info().id] = health
        return results

    def get_primary_provider(self) -> Optional[ProviderContract]:
        """
        Get the global primary provider (for tasks without specific requirements).

        Returns:
            Primary provider or None
        """
        for provider in self._providers.values():
            if provider.provider_info().is_primary:
                return provider
        return None


# Singleton instance
_registry: Optional[ProviderRegistry] = None


def get_registry() -> ProviderRegistry:
    """Get the global registry instance (thread-safe)."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry
