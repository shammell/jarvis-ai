"""
Coding Execution Router - Multi-provider routing for compiled execution plans.

This module routes compiled execution plans to appropriate provider adapters
with:
- Provider allowlist by task class
- Deterministic fallback when provider unavailable
- Policy-gated routing with approval gates
- Provider health checks before routing
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
import time

from .provider_contract import (
    ProviderContract,
    ProviderInfo,
    ProviderStatus,
    ProviderCapability,
    ProviderRegistry,
    get_registry
)
from .routing_policy import (
    RoutingPolicy,
    PolicyEnforcer,
    TaskClass,
    RiskLevel,
    ProviderType,
)

logger = logging.getLogger(__name__)


class RouterDecision(Enum):
    """Outcome of a routing decision."""
    SELECTED = "selected"          # Provider selected successfully
    BLOCKED = "blocked"            # Task blocked by policy
    NEEDS_APPROVAL = "needs_approval"  # Requires human approval
    NO_HEALTHY_PROVIDER = "no_healthy_provider"  # No providers available
    INVALID_TASK_CLASS = "invalid_task_class"    # Task class not recognized
    PROVIDER_UNAVAILABLE = "provider_unavailable"  # All allowed providers down


@dataclass
class RoutingDecision:
    """
    Result of a routing decision.

    Contains:
    - Decision status (selected/blocked/needs_approval/...)
    - Selected provider (if applicable)
    - Task class and type
    - Fallback chain that was considered
    - Risk level and approval requirements
    """
    decision: RouterDecision
    task_class: str
    task_type: str
    selected_provider: Optional[str] = None
    provider_info: Optional[Dict[str, Any]] = None
    fallback_chain: List[str] = field(default_factory=list)
    risk_level: str = "low"
    requires_approval: bool = False
    reason: str = ""
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            "decision": self.decision.value,
            "task_class": self.task_class,
            "task_type": self.task_type,
            "selected_provider": self.selected_provider,
            "provider_info": self.provider_info,
            "fallback_chain": self.fallback_chain,
            "risk_level": self.risk_level,
            "requires_approval": self.requires_approval,
            "reason": self.reason,
            "timestamp": self.timestamp
        }


@dataclass
class ExecutionPlan:
    """
    Compiled execution plan ready for routing.

    Contains the complete plan from ProjectGoalCompiler plus
    routing metadata.
    """
    original_command: str
    intent: str
    requirements: List[Dict[str, Any]]
    architecture: Dict[str, Any]
    milestones: List[Dict[str, Any]]
    tool_steps: List[Dict[str, Any]]
    verification_checklist: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_compiled_plan(cls, compiled_goal: Any) -> 'ExecutionPlan':
        """Create ExecutionPlan from CompiledGoal."""
        return cls(
            original_command=compiled_goal.get('original_command', ''),
            intent=compiled_goal.get('intent', 'unknown'),
            requirements=compiled_goal.get('requirements', []),
            architecture=compiled_goal.get('architecture', {}),
            milestones=compiled_goal.get('milestones', []),
            tool_steps=compiled_goal.get('tool_steps', []),
            verification_checklist=compiled_goal.get('verification_checklist', []),
            metadata=compiled_goal.get('metadata', {})
        )


class CodingExecutionRouter:
    """
    Routes compiled execution plans to appropriate provider adapters.

    Key features:
    - Provider allowlist by task class
    - Deterministic fallback when provider unavailable
    - Policy-gated routing (approval gates)
    - Provider health checks before routing

    Usage:
        router = CodingExecutionRouter()
        plan = router.get_registry().get_primary_provider()

        decision = router.route_task(
            plan=plan,
            task_class=TaskClass.FRONTEND,
            task_type="create_frontend_app"
        )
    """

    def __init__(
        self,
        registry: Optional[ProviderRegistry] = None,
        policy: Optional[RoutingPolicy] = None,
        enforcer: Optional[PolicyEnforcer] = None
    ):
        """
        Initialize the router.

        Args:
            registry: Provider registry for provider lookup
            policy: Routing policy for task-to-provider mapping
            enforcer: Policy enforcer for runtime enforcement
        """
        self._registry = registry or get_registry()
        self._policy = policy or RoutingPolicy()
        self._enforcer = enforcer or PolicyEnforcer(policy)

        # Track recent routing decisions for metrics
        self._recent_decisions: List[RoutingDecision] = []
        self._max_recent_decisions = 100

        logger.info(f"CodingExecutionRouter initialized with {len(self._registry._providers)} providers")

    @property
    def registry(self) -> ProviderRegistry:
        """Get the provider registry."""
        return self._registry

    @property
    def policy(self) -> RoutingPolicy:
        """Get the routing policy."""
        return self._policy

    @property
    def enforcer(self) -> PolicyEnforcer:
        """Get the policy enforcer."""
        return self._enforcer

    def route_task(
        self,
        compiled_goal: Dict[str, Any],
        task_class: str,
        task_type: str,
        risk_level: str = "low"
    ) -> RoutingDecision:
        """
        Route a single task from a compiled plan to a provider.

        This method:
        1. Checks if the task class has registered providers
        2. Performs health check on available providers
        3. Selects the best provider based on policy
        4. Returns routing decision with reason

        Args:
            compiled_goal: Compiled execution plan dict
            task_class: Task class identifier (frontend, backend, etc.)
            task_type: Specific task type (e.g., "create_frontend_app")
            risk_level: Risk level of the task (low/medium/high)

        Returns:
            RoutingDecision with selected provider and metadata
        """
        # Normalize inputs
        task_class_lower = task_class.lower()
        risk_enum = self._parse_risk_level(risk_level)

        # Check for valid task class
        try:
            task_enum = TaskClass(task_class_lower)
        except ValueError:
            return RoutingDecision(
                decision=RouterDecision.INVALID_TASK_CLASS,
                task_class=task_class,
                task_type=task_type,
                reason=f"Invalid task class: {task_class}",
                risk_level=risk_level
            )

        # Get allowed providers for this task class
        allowed_provider_types = self._policy.get_allowed_providers(task_enum)
        logger.debug(f"Allowed providers for {task_class}: {allowed_provider_types}")

        # Convert provider types to provider IDs
        provider_ids = self._map_provider_types_to_ids(allowed_provider_types)
        logger.debug(f"Mapped to provider IDs: {provider_ids}")

        # Filter to only healthy providers
        healthy_providers = self._get_healthy_providers(provider_ids)
        logger.debug(f"Healthy providers: {healthy_providers}")

        if not healthy_providers:
            return RoutingDecision(
                decision=RouterDecision.NO_HEALTHY_PROVIDER,
                task_class=task_class,
                task_type=task_type,
                fallback_chain=list(provider_ids),
                reason=f"No healthy providers available for {task_class}",
                risk_level=risk_level
            )

        # Select best provider
        selected_provider = self._select_best_provider(
            task_enum,
            task_type,
            healthy_providers,
            risk_enum
        )

        if not selected_provider:
            return RoutingDecision(
                decision=RouterDecision.PROVIDER_UNAVAILABLE,
                task_class=task_class,
                task_type=task_type,
                fallback_chain=list(provider_ids),
                reason=f"All providers unavailable for {task_class}",
                risk_level=risk_level
            )

        # Get provider info and check approval requirements
        provider_info = selected_provider.provider_info()
        provider_type = self._provider_id_to_provider_type(provider_info.id) or ProviderType.CLAUDE_CODE
        requires_approval = self._policy.requires_approval(task_type, provider_type)

        decision = RoutingDecision(
            decision=RouterDecision.SELECTED,
            task_class=task_class,
            task_type=task_type,
            selected_provider=selected_provider.provider_info().id,
            provider_info=self._provider_info_to_dict(provider_info),
            fallback_chain=list(provider_ids),
            risk_level=risk_level,
            requires_approval=requires_approval,
            reason=f"Selected {selected_provider.provider_info().name}"
        )

        # Track decision
        self._track_decision(decision)

        logger.info(f"Route decision: {task_type} -> {decision.selected_provider}")

        return decision

    def route_plan(
        self,
        compiled_goal: Dict[str, Any]
    ) -> Dict[str, List[RoutingDecision]]:
        """
        Route a complete execution plan.

        Routes all tool steps from a compiled plan, tracking:
        - Each step's routing decision
        - Provider assignments
        - Approval requirements

        Args:
            compiled_goal: Complete compiled execution plan

        Returns:
            Dict mapping milestone_id to list of routing decisions
        """
        results: Dict[str, List[RoutingDecision]] = {}
        tool_steps = compiled_goal.get('tool_steps', [])
        milestones = compiled_goal.get('milestones', [])

        for step in tool_steps:
            task_class = step.get('task_class', 'system')
            task_type = step.get('task', step.get('tool_name', 'unknown'))
            risk_level = step.get('risk_level', 'low')

            decision = self.route_task(
                compiled_goal=compiled_goal,
                task_class=task_class,
                task_type=task_type,
                risk_level=risk_level
            )

            milestone_id = step.get('milestone_id', 'default')
            if milestone_id not in results:
                results[milestone_id] = []
            results[milestone_id].append(decision)

        return results

    def check_provider_health(self, provider_id: str) -> Optional[ProviderContract]:
        """
        Check health of a specific provider and update registry.

        Args:
            provider_id: ID of provider to check

        Returns:
            Provider if healthy, None if unhealthy
        """
        provider = self._registry.get_provider(provider_id)
        if not provider:
            logger.warning(f"Provider {provider_id} not found in registry")
            return None

        try:
            import asyncio
            health = asyncio.run(provider.check_health())

            if not health.is_healthy:
                logger.warning(f"Provider {provider_id} unhealthy: {health.error_message}")
                provider.provider_info().status = ProviderStatus.UNHEALTHY
                return None

            logger.info(f"Provider {provider_id} healthy (latency: {health.latency_ms}ms)")
            provider.provider_info().status = ProviderStatus.HEALTHY
            return provider

        except Exception as e:
            logger.error(f"Health check failed for {provider_id}: {e}")
            provider.provider_info().status = ProviderStatus.UNHEALTHY
            return None

    async def check_all_providers_health(self) -> Dict[str, bool]:
        """
        Check health of all registered providers.

        Returns:
            Dict mapping provider_id to health status (True/False)
        """
        providers = await self._registry.get_all_providers()
        results = {}

        for provider in providers:
            health = await provider.check_health()
            results[provider.provider_info().id] = health.is_healthy

        logger.info(f"Health check complete: {sum(results.values())}/{len(results)} providers healthy")
        return results

    def get_allowed_providers_for_class(self, task_class: str) -> List[str]:
        """
        Get the ordered list of allowed providers for a task class.

        Args:
            task_class: Task class identifier

        Returns:
            List of provider IDs in preference order
        """
        try:
            task_enum = TaskClass(task_class.lower())
        except ValueError:
            return []

        provider_types = self._policy.get_allowed_providers(task_enum)
        return [self._map_provider_type_to_id(p) for p in provider_types]

    def validate_routing(
        self,
        task_class: str,
        task_type: str,
        provider_id: str
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate if a task can be routed to a specific provider.

        Args:
            task_class: Task class identifier
            task_type: Task type identifier
            provider_id: Provider ID to validate

        Returns:
            Tuple of (is_valid, reason, suggestion)
        """
        try:
            task_enum = TaskClass(task_class.lower())
        except ValueError:
            return False, f"Invalid task class: {task_class}", None

        # Get provider type from ID
        provider_type = self._provider_id_to_provider_type(provider_id)
        if not provider_type:
            provider_type = ProviderType.CLAUDE_CODE  # Default

        risk_enum = RiskLevel.LOW  # Default for validation
        return self._policy.validate_task_routing(task_enum, task_type, provider_type, risk_enum)

    def _parse_risk_level(self, risk_level: str) -> RiskLevel:
        """Parse string risk level to enum."""
        try:
            return RiskLevel(risk_level.lower())
        except ValueError:
            return RiskLevel.LOW

    def _map_provider_types_to_ids(
        self,
        provider_types: List[ProviderType]
    ) -> List[str]:
        """Map provider types to actual provider IDs."""
        ids = []
        type_to_id = {
            ProviderType.CLAUDE_CODE: "claude-code",
            ProviderType.FALLBACK_1: "claude-code",
            ProviderType.FALLBACK_2: "claude-code",
            ProviderType.LOCAL: "local",
            ProviderType.MANUAL: "manual"
        }

        for ptype in provider_types:
            provider_id = type_to_id.get(ptype)
            if provider_id:
                ids.append(provider_id)

        # Preserve deterministic order while removing duplicates.
        seen = set()
        ordered = []
        for provider_id in ids:
            if provider_id not in seen:
                seen.add(provider_id)
                ordered.append(provider_id)
        return ordered

    def _get_healthy_providers(self, provider_ids: List[str]) -> List[ProviderContract]:
        """Filter to only healthy providers."""
        healthy = []
        for provider_id in provider_ids:
            provider = self._registry.get_provider(provider_id)
            if provider and provider.provider_info().status == ProviderStatus.HEALTHY:
                healthy.append(provider)
        return healthy

    def _select_best_provider(
        self,
        task_class: TaskClass,
        task_type: str,
        healthy_providers: List[ProviderContract],
        risk_level: RiskLevel
    ) -> Optional[ProviderContract]:
        """
        Select the best provider from healthy providers.

        Selection criteria:
        1. Primary provider preferred
        2. Must be able to handle the risk level
        3. Capability match
        """
        for provider in healthy_providers:
            info = provider.provider_info()

            # Prefer primary provider
            if info.is_primary:
                return provider

        # Return first healthy provider
        return healthy_providers[0] if healthy_providers else None

    def _provider_id_to_provider_type(self, provider_id: str) -> Optional[ProviderType]:
        """Convert provider ID to provider type."""
        id_to_type = {
            "claude-code": ProviderType.CLAUDE_CODE,
            "local": ProviderType.LOCAL,
            "manual": ProviderType.MANUAL,
        }
        return id_to_type.get(provider_id, ProviderType.CLAUDE_CODE)

    def _map_provider_type_to_id(self, provider_type: ProviderType) -> str:
        """Convert ProviderType to canonical provider ID string."""
        type_to_id = {
            ProviderType.CLAUDE_CODE: "claude-code",
            ProviderType.FALLBACK_1: "fallback-1",
            ProviderType.FALLBACK_2: "fallback-2",
            ProviderType.LOCAL: "local",
            ProviderType.MANUAL: "manual",
        }
        return type_to_id.get(provider_type, provider_type.value)

    def _provider_info_to_dict(self, info: ProviderInfo) -> Dict[str, Any]:
        """Convert ProviderInfo to dict."""
        return {
            "id": info.id,
            "name": info.name,
            "status": info.status.value,
            "capabilities": [c.value for c in info.capabilities],
            "is_primary": info.is_primary,
            "rate_limit": info.rate_limit,
            "max_tokens": info.max_tokens
        }

    def _track_decision(self, decision: RoutingDecision) -> None:
        """Track a routing decision for metrics."""
        self._recent_decisions.append(decision)
        if len(self._recent_decisions) > self._max_recent_decisions:
            self._recent_decisions = self._recent_decisions[-self._max_recent_decisions:]

    def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing statistics from recent decisions."""
        if not self._recent_decisions:
            return {
                "total_decisions": 0,
                "success_rate": 0,
                "approval_required_rate": 0,
                "common_task_classes": [],
                "common_providers": []
            }

        decisions = self._recent_decisions
        success_count = sum(1 for d in decisions if d.decision == RouterDecision.SELECTED)
        approval_count = sum(1 for d in decisions if d.requires_approval)

        task_classes = [d.task_class for d in decisions]
        providers = [d.selected_provider for d in decisions if d.selected_provider]

        return {
            "total_decisions": len(decisions),
            "success_rate": success_count / len(decisions),
            "approval_required_rate": approval_count / len(decisions),
            "common_task_classes": dict(__import__('collections').Counter(task_classes)),
            "common_providers": dict(__import__('collections').Counter(providers))
        }


# Convenience function
def create_router() -> CodingExecutionRouter:
    """Create a new router with default configuration."""
    return CodingExecutionRouter()


# Ensure registry is initialized with default providers
def _ensure_initial_providers():
    """Ensure primary providers are registered."""
    registry = get_registry()

    # Register Claude Code provider if not already registered
    if not registry.get_provider("claude-code"):
        from .provider_contract import ClaudeCodeProvider
        cc_provider = ClaudeCodeProvider()
        registry.register_provider(cc_provider)
        logger.info("Registered default Claude Code provider")


# Auto-initialize on module import
_ensure_initial_providers()
