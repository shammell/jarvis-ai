"""
Routing Policy - Task classification and provider mapping system.

This module defines the policy framework for:
- Task class → provider mapping
- Risk enforcement per provider type
- Deterministic fallback ordering
- Approval gate enforcement
"""

from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Any, Dict, List, Optional, Set, Tuple

from .provider_contract import ProviderCapability, ProviderContract, ProviderStatus


class TaskClass(PyEnum):
    """Classification of task types for routing purposes."""
    # Development tasks
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    SUPABASE = "supabase"

    # Infrastructure tasks
    DEPLOYMENT = "deployment"
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"

    # Quality tasks
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"

    # System tasks
    SYSTEM = "system"
    MONITORING = "monitoring"
    DIAGNOSTICS = "diagnostics"


class RiskLevel(PyEnum):
    """Risk classification for task routing."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProviderType(PyEnum):
    """Types of providers available for routing."""
    CLAUDE_CODE = "claude_code"  # Primary AI coding assistant
    FALLBACK_1 = "fallback_1"     # Secondary AI provider
    FALLBACK_2 = "fallback_2"     # Tertiary provider
    LOCAL = "local"               # Local execution (fallback)
    MANUAL = "manual"             # Requires human intervention


@dataclass
class RoutingPolicy:
    """
    Defines routing policy for task class → provider mapping.

    Features:
    - Task class to allowed provider mapping
    - Risk enforcement per provider
    - Deterministic fallback ordering
    - Approval gate enforcement
    """

    # Task class → allowed providers (ordered by preference)
    provider_allowlist: Dict[TaskClass, List[ProviderType]] = field(
        default_factory=lambda: {
            TaskClass.FRONTEND: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.FALLBACK_2
            ],
            TaskClass.BACKEND: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.FALLBACK_2
            ],
            TaskClass.DATABASE: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL
            ],
            TaskClass.SUPABASE: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL
            ],
            TaskClass.DEPLOYMENT: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL,
                ProviderType.MANUAL
            ],
            TaskClass.INFRASTRUCTURE: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL,
                ProviderType.MANUAL
            ],
            TaskClass.CONFIGURATION: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL
            ],
            TaskClass.TESTING: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL
            ],
            TaskClass.SECURITY: [
                ProviderType.CLAUDE_CODE,
                ProviderType.MANUAL
            ],
            TaskClass.PERFORMANCE: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL
            ],
            TaskClass.SYSTEM: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL
            ],
            TaskClass.MONITORING: [
                ProviderType.CLAUDE_CODE,
                ProviderType.LOCAL
            ],
            TaskClass.DIAGNOSTICS: [
                ProviderType.CLAUDE_CODE,
                ProviderType.FALLBACK_1,
                ProviderType.LOCAL
            ]
        }
    )

    # Risk level enforcement per provider type
    risk_enforcement: Dict[ProviderType, Dict[RiskLevel, bool]] = field(
        default_factory=lambda: {
            ProviderType.CLAUDE_CODE: {
                RiskLevel.LOW: True,     # Auto-approve
                RiskLevel.MEDIUM: False,  # Requires approval
                RiskLevel.HIGH: False,    # Requires approval
                RiskLevel.CRITICAL: False # Always blocked
            },
            ProviderType.FALLBACK_1: {
                RiskLevel.LOW: True,
                RiskLevel.MEDIUM: False,
                RiskLevel.HIGH: False,
                RiskLevel.CRITICAL: False
            },
            ProviderType.FALLBACK_2: {
                RiskLevel.LOW: True,
                RiskLevel.MEDIUM: False,
                RiskLevel.HIGH: True,    # Allowed for high risk
                RiskLevel.CRITICAL: False
            },
            ProviderType.LOCAL: {
                RiskLevel.LOW: True,
                RiskLevel.MEDIUM: True,
                RiskLevel.HIGH: True,
                RiskLevel.CRITICAL: False
            },
            ProviderType.MANUAL: {
                RiskLevel.LOW: True,
                RiskLevel.MEDIUM: True,
                RiskLevel.HIGH: True,
                RiskLevel.CRITICAL: True
            }
        }
    )

    # Default fallback order (independent of task class)
    fallback_order: List[ProviderType] = field(
        default_factory=lambda: [
            ProviderType.CLAUDE_CODE,
            ProviderType.FALLBACK_1,
            ProviderType.FALLBACK_2,
            ProviderType.LOCAL,
            ProviderType.MANUAL
        ]
    )

    # Tasks that require human approval regardless of provider
    approval_required_tasks: Set[str] = field(
        default_factory=lambda: {
            "deploy_production",
            "delete_data",
            "modify_infrastructure",
            "security_scan",
            "system_restart"
        }
    )

    def get_allowed_providers(self, task_class: TaskClass) -> List[ProviderType]:
        """
        Get the ordered list of allowed providers for a task class.

        Args:
            task_class: Classification of the task

        Returns:
            List of provider types in preference order
        """
        return self.provider_allowlist.get(
            task_class,
            self.fallback_order
        )

    def get_effective_fallback_order(
        self,
        task_class: TaskClass,
        available_providers: Set[ProviderType]
    ) -> List[ProviderType]:
        """
        Get fallback order considering available providers.

        Args:
            task_class: Classification of the task
            available_providers: Set of currently available providers

        Returns:
            Filtered fallback order with only available providers
        """
        allowed = self.get_allowed_providers(task_class)
        ordered = [p for p in allowed if p in available_providers]

        # If none of the allowlisted providers are available, gracefully
        # degrade to any available provider in deterministic fallback order.
        if not ordered and available_providers:
            ordered = [p for p in self.fallback_order if p in available_providers]

        return ordered

    def can_provider_handle_risk(
        self,
        provider: ProviderType,
        risk_level: RiskLevel
    ) -> bool:
        """
        Check if a provider is allowed to handle a given risk level.

        Args:
            provider: Provider type to check
            risk_level: Risk level of the task

        Returns:
            True if provider can handle this risk level
        """
        enforcement = self.risk_enforcement.get(provider, {})
        return enforcement.get(risk_level, False)

    def requires_approval(
        self,
        task_type: str,
        provider: ProviderType
    ) -> bool:
        """
        Check if a task requires human approval.

        Args:
            task_type: Type of task to check
            provider: Provider type that would execute

        Returns:
            True if human approval is required
        """
        # Check explicit approval required tasks
        if task_type in self.approval_required_tasks:
            return True

        # Check risk enforcement
        # For now, assume medium-high risk requires approval
        return not self.can_provider_handle_risk(provider, RiskLevel.LOW)

    def validate_task_routing(
        self,
        task_class: TaskClass,
        task_type: str,
        provider: ProviderType,
        risk_level: RiskLevel
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate if a task can be routed to a specific provider.

        Args:
            task_class: Classification of the task
            task_type: Type of task
            provider: Provider type to route to
            risk_level: Risk level of the task

        Returns:
            Tuple of (is_valid, reason, suggestion)
        """
        # Check if provider is in allowlist
        allowed = self.get_allowed_providers(task_class)
        if provider not in allowed:
            return (
                False,
                f"Provider {provider.value} not allowed for {task_class.value}",
                allowed[0].value if allowed else None
            )

        # Check risk enforcement
        if not self.can_provider_handle_risk(provider, risk_level):
            if provider == ProviderType.CLAUDE_CODE:
                return (
                    False,
                    f"Risk level {risk_level.value} requires approval for {provider.value}",
                    "request_approval"
                )
            return (
                False,
                f"Provider {provider.value} cannot handle {risk_level.value} risk",
                ProviderType.LOCAL.value
            )

        return True, "Valid routing", None

    def get_primary_provider_task(self, task_class: TaskClass) -> Optional[ProviderType]:
        """
        Get the primary (first) provider for a task class.

        Args:
            task_class: Classification of the task

        Returns:
            Primary provider type or None if no providers allowed
        """
        allowed = self.get_allowed_providers(task_class)
        return allowed[0] if allowed else None


class PolicyEnforcer:
    """
    Runtime enforcer for routing policies.

    Responsibilities:
    - Route compiled tasks to appropriate providers
    - Enforce approval gates
    - Manage fallback behavior
    - Track bypass attempts
    """

    def __init__(self, policy: Optional[RoutingPolicy] = None):
        self.policy = policy or RoutingPolicy()
        self.bypass_attempts: List[Dict[str, Any]] = []

    def route_task(
        self,
        task_class: TaskClass,
        task_type: str,
        available_providers: Set[str],
        risk_level: RiskLevel = RiskLevel.LOW
    ) -> Dict[str, Any]:
        """
        Route a task to the best available provider.

        Args:
            task_class: Classification of the task
            task_type: Type of task (for approval checks)
            available_providers: Set of available provider IDs
            risk_level: Risk level of the task

        Returns:
            Routing decision with selected provider and rationale
        """
        # Map string provider IDs to ProviderType enum
        provider_types = set()
        for pid in available_providers:
            try:
                provider_types.add(ProviderType(pid))
            except ValueError:
                # Try to match by substring
                for pt in ProviderType:
                    if pt.value in pid.lower():
                        provider_types.add(pt)
                        break

        # Convert to ProviderType if needed
        provider_type_set: Set[ProviderType] = provider_types
        if not provider_type_set:
            provider_type_set = {ProviderType.CLAUDE_CODE}

        # Get effective fallback order
        fallback_order = self.policy.get_effective_fallback_order(
            task_class,
            provider_type_set
        )

        # Validate each provider in order
        selected_provider = None
        selection_reason = None

        for provider in fallback_order:
            is_valid, reason, suggestion = self.policy.validate_task_routing(
                task_class,
                task_type,
                provider,
                risk_level
            )

            if is_valid:
                selected_provider = provider
                selection_reason = f"Selected as {reason}"
                break

        if not selected_provider:
            # No valid provider found
            return {
                "status": "blocked",
                "reason": f"No valid provider for {task_class.value} at {risk_level.value} risk",
                "required_capability": task_class.value,
                "available_providers": list(provider_type_set),
                "suggested_action": "request_manual_intervention"
            }

        # Check if approval required
        requires_approval = self.policy.requires_approval(task_type, selected_provider)

        return {
            "status": "selected",
            "task_class": task_class.value,
            "task_type": task_type,
            "selected_provider": selected_provider.value,
            "risk_level": risk_level.value,
            "requires_approval": requires_approval,
            "reason": selection_reason,
            "fallback_chain": [p.value for p in fallback_order],
            "approval_required": requires_approval
        }

    def attempt_bypass(
        self,
        task_type: str,
        original_provider: ProviderType,
        bypass_target: ProviderType
    ) -> Dict[str, Any]:
        """
        Record and evaluate a bypass attempt.

        Bypassing is when a task is routed to a provider outside
        the normal policy (potentially risky behavior).

        Args:
            task_type: Type of task being bypassed
            original_provider: Provider that should have been used
            bypass_target: Provider actually used

        Returns:
            Evaluation of the bypass attempt
        """
        bypass_record = {
            "task_type": task_type,
            "original_provider": original_provider.value,
            "bypass_target": bypass_target.value,
            "timestamp": __import__('time').time(),
            "blocked_by_policy": original_provider != bypass_target
        }

        self.bypass_attempts.append(bypass_record)

        # Check if this is a policy violation
        policy_violation = original_provider != bypass_target

        return {
            "action": "bypass_attempted",
            "policy_violation": policy_violation,
            "bypass_record": bypass_record,
            "allowed": not policy_violation,
            "warning": "Policy bypass detected" if policy_violation else None
        }

    def get_bypass_statistics(self) -> Dict[str, Any]:
        """Get statistics about bypass attempts."""
        violations = sum(1 for b in self.bypass_attempts if b.get("blocked_by_policy"))

        return {
            "total_attempts": len(self.bypass_attempts),
            "violations": violations,
            "violation_rate": violations / max(1, len(self.bypass_attempts)),
            "recent_bypasses": self.bypass_attempts[-10:] if self.bypass_attempts else []
        }


def get_routing_policy() -> RoutingPolicy:
    """Get the default routing policy instance."""
    return RoutingPolicy()


def get_policy_enforcer() -> PolicyEnforcer:
    """Get the default policy enforcer instance."""
    return PolicyEnforcer()
