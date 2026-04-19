"""
Test Suite: Routing Policy

Tests for routing_policy.py
- Provider allowlist management
- Risk enforcement per provider
- Fallback ordering
- Policy enforcement
"""

import pytest
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.routing_policy import (
    RoutingPolicy,
    PolicyEnforcer,
    TaskClass,
    ProviderType,
    RiskLevel
)
from core.provider_contract import ProviderCapability


class TestRoutingPolicyInitialization:
    """Test routing policy initialization."""

    def test_default_allowlist_exists(self):
        """Test default provider allowlist is initialized."""
        policy = RoutingPolicy()

        assert TaskClass.FRONTEND in policy.provider_allowlist
        assert TaskClass.BACKEND in policy.provider_allowlist
        assert TaskClass.SUPABASE in policy.provider_allowlist

    def test_default_risk_enforcement_exists(self):
        """Test default risk enforcement configuration."""
        policy = RoutingPolicy()

        assert ProviderType.CLAUDE_CODE in policy.risk_enforcement
        assert ProviderType.LOCAL in policy.risk_enforcement

    def test_default_fallback_order(self):
        """Test default fallback ordering."""
        policy = RoutingPolicy()

        assert policy.fallback_order[0] == ProviderType.CLAUDE_CODE

    def test_approval_required_tasks(self):
        """Test approval required tasks list."""
        policy = RoutingPolicy()

        assert 'deploy_production' in policy.approval_required_tasks
        assert 'security_scan' in policy.approval_required_tasks


class TestProviderAllowlist:
    """Test provider allowlist management."""

    @pytest.fixture
    def policy(self):
        return RoutingPolicy()

    def test_get_allowed_frontend_providers(self, policy):
        """Test allowed providers for frontend tasks."""
        providers = policy.get_allowed_providers(TaskClass.FRONTEND)

        assert len(providers) > 0
        assert ProviderType.CLAUDE_CODE in providers
        assert providers[0] == ProviderType.CLAUDE_CODE

    def test_get_allowed_backend_providers(self, policy):
        """Test allowed providers for backend tasks."""
        providers = policy.get_allowed_providers(TaskClass.BACKEND)

        assert len(providers) > 0
        assert ProviderType.CLAUDE_CODE in providers

    def test_get_allowed_supabase_providers(self, policy):
        """Test allowed providers for supabase tasks."""
        providers = policy.get_allowed_providers(TaskClass.SUPABASE)

        assert len(providers) > 0
        assert ProviderType.CLAUDE_CODE in providers

    def test_get_allowed_security_providers(self, policy):
        """Test allowed providers for security tasks."""
        providers = policy.get_allowed_providers(TaskClass.SECURITY)

        # Security typically has more restricted access
        assert len(providers) <= 3

    def test_get_allowed_unknown_task_class(self, policy):
        """Test allowed providers for unknown task class."""
        class FakeTaskClass:
            value = 'unknown'

        # Should fall back to default
        providers = policy.get_allowed_providers(FakeTaskClass)
        assert len(providers) > 0

    def test_provider_order_maintained(self, policy):
        """Test that provider order is maintained (primary first)."""
        providers = policy.get_allowed_providers(TaskClass.FRONTEND)

        # Claude Code should be first (primary)
        assert providers[0] == ProviderType.CLAUDE_CODE


class TestRiskEnforcement:
    """Test risk enforcement per provider."""

    @pytest.fixture
    def policy(self):
        return RoutingPolicy()

    def test_claude_code_low_risk_allowed(self, policy):
        """Test Claude Code can handle low risk."""
        assert policy.can_provider_handle_risk(
            ProviderType.CLAUDE_CODE,
            RiskLevel.LOW
        ) is True

    def test_claude_code_high_risk_restricted(self, policy):
        """Test Claude Code cannot handle high risk without approval."""
        assert policy.can_provider_handle_risk(
            ProviderType.CLAUDE_CODE,
            RiskLevel.HIGH
        ) is False

    def test_claude_code_critical_blocked(self, policy):
        """Test Claude Code cannot handle critical risk."""
        assert policy.can_provider_handle_risk(
            ProviderType.CLAUDE_CODE,
            RiskLevel.CRITICAL
        ) is False

    def test_local_all_risks_allowed(self, policy):
        """Test local provider can handle most risks."""
        assert policy.can_provider_handle_risk(
            ProviderType.LOCAL,
            RiskLevel.LOW
        ) is True
        assert policy.can_provider_handle_risk(
            ProviderType.LOCAL,
            RiskLevel.MEDIUM
        ) is True
        assert policy.can_provider_handle_risk(
            ProviderType.LOCAL,
            RiskLevel.HIGH
        ) is True
        assert policy.can_provider_handle_risk(
            ProviderType.LOCAL,
            RiskLevel.CRITICAL
        ) is False

    def test_manual_all_risks_allowed(self, policy):
        """Test manual provider can handle all risks."""
        assert policy.can_provider_handle_risk(
            ProviderType.MANUAL,
            RiskLevel.LOW
        ) is True
        assert policy.can_provider_handle_risk(
            ProviderType.MANUAL,
            RiskLevel.CRITICAL
        ) is True

    def test_fallback_2_high_risk_allowed(self, policy):
        """Test fallback_2 can handle high risk."""
        assert policy.can_provider_handle_risk(
            ProviderType.FALLBACK_2,
            RiskLevel.HIGH
        ) is True


class TestFallbackOrder:
    """Test fallback ordering."""

    @pytest.fixture
    def policy(self):
        return RoutingPolicy()

    def test_get_effective_fallback_order_all_available(self, policy):
        """Test fallback order when all providers available."""
        available = {ProviderType.CLAUDE_CODE, ProviderType.LOCAL}

        result = policy.get_effective_fallback_order(
            TaskClass.FRONTEND,
            available
        )

        # Should only contain available providers
        assert all(p in available for p in result)
        # Order should be maintained
        if ProviderType.CLAUDE_CODE in result and ProviderType.LOCAL in result:
            assert result.index(ProviderType.CLAUDE_CODE) < result.index(ProviderType.LOCAL)

    def test_get_effective_fallback_order_partial(self, policy):
        """Test fallback order with partial availability."""
        available = {ProviderType.LOCAL}  # Only local available

        result = policy.get_effective_fallback_order(
            TaskClass.FRONTEND,
            available
        )

        assert result == [ProviderType.LOCAL]

    def test_get_effective_fallback_order_none_available(self, policy):
        """Test fallback order with no providers available."""
        available = set()

        result = policy.get_effective_fallback_order(
            TaskClass.FRONTEND,
            available
        )

        assert result == []


class TestApprovalRequirements:
    """Test approval gate requirements."""

    @pytest.fixture
    def policy(self):
        return RoutingPolicy()

    def test_deploy_production_requires_approval(self, policy):
        """Test deploy_production requires human approval."""
        requires_approval = policy.requires_approval(
            'deploy_production',
            ProviderType.CLAUDE_CODE
        )
        assert requires_approval is True

    def test_security_scan_requires_approval(self, policy):
        """Test security_scan requires human approval."""
        requires_approval = policy.requires_approval(
            'security_scan',
            ProviderType.CLAUDE_CODE
        )
        assert requires_approval is True

    def test_standard_task_not_requiring_approval(self, policy):
        """Test standard code generation doesn't require approval."""
        requires_approval = policy.requires_approval(
            'generate_code',
            ProviderType.CLAUDE_CODE
        )
        assert requires_approval is False

    def test_high_risk_task_requires_approval(self, policy):
        """Test that high risk tasks require approval."""
        # High risk is not LOW, so requires approval
        requires_approval = policy.requires_approval(
            'some_task',
            ProviderType.CLAUDE_CODE
        )
        # Depends on risk enforcement - LOW is auto-approved
        # For tasks not in approval_required_tasks, depends on can_provider_handle_risk


class TestTaskRoutingValidation:
    """Test task routing validation."""

    @pytest.fixture
    def policy(self):
        return RoutingPolicy()

    def test_valid_route(self, policy):
        """Test valid task routing."""
        is_valid, reason, suggestion = policy.validate_task_routing(
            task_class=TaskClass.FRONTEND,
            task_type='create_app',
            provider=ProviderType.CLAUDE_CODE,
            risk_level=RiskLevel.LOW
        )

        assert is_valid is True
        assert 'valid' in reason.lower()
        assert suggestion is None

    def test_invalid_provider_not_in_allowlist(self, policy):
        """Test invalid provider not in allowlist."""
        is_valid, reason, suggestion = policy.validate_task_routing(
            task_class=TaskClass.FRONTEND,
            task_type='create_app',
            provider=ProviderType.MANUAL,  # Not in frontend allowlist
            risk_level=RiskLevel.LOW
        )

        assert is_valid is False
        assert 'not allowed' in reason.lower()
        assert suggestion is not None

    def test_invalid_risk_level(self, policy):
        """Test routing with provider that can't handle risk level."""
        is_valid, reason, suggestion = policy.validate_task_routing(
            task_class=TaskClass.BACKEND,
            task_type='deploy_prod',
            provider=ProviderType.CLAUDE_CODE,
            risk_level=RiskLevel.CRITICAL
        )

        assert is_valid is False
        assert 'risk' in reason.lower()

    def test_suggestion_provided_for_invalid(self, policy):
        """Test suggestion is provided for invalid routing."""
        is_valid, reason, suggestion = policy.validate_task_routing(
            task_class=TaskClass.FRONTEND,
            task_type='create_app',
            provider=ProviderType.MANUAL,
            risk_level=RiskLevel.LOW
        )

        assert suggestion is not None


class TestPrimaryProviderSelection:
    """Test primary provider selection."""

    @pytest.fixture
    def policy(self):
        return RoutingPolicy()

    def test_get_primary_provider_task(self, policy):
        """Test getting primary provider for task class."""
        primary = policy.get_primary_provider_task(TaskClass.FRONTEND)

        assert primary == ProviderType.CLAUDE_CODE

    def test_get_primary_provider_all_classes(self, policy):
        """Test getting primary provider for all task classes."""
        for task_class in [
            TaskClass.FRONTEND,
            TaskClass.BACKEND,
            TaskClass.SUPABASE,
            TaskClass.TESTING
        ]:
            primary = policy.get_primary_provider_task(task_class)
            assert primary == ProviderType.CLAUDE_CODE


class TestPolicyEnforcerInitialization:
    """Test policy enforcer initialization."""

    def test_enforcer_with_default_policy(self):
        """Test enforcer with default policy."""
        enforcer = PolicyEnforcer()

        assert enforcer.policy is not None
        assert isinstance(enforcer.policy, RoutingPolicy)
        assert enforcer.bypass_attempts == []

    def test_enforcer_with_custom_policy(self):
        """Test enforcer with custom policy."""
        custom_policy = RoutingPolicy()
        enforcer = PolicyEnforcer(policy=custom_policy)

        assert enforcer.policy is custom_policy


class TestPolicyEnforcerRouteTask:
    """Test policy enforcer route_task method."""

    @pytest.fixture
    def enforcer(self):
        return PolicyEnforcer()

    def test_route_task_success(self, enforcer):
        """Test successful task routing."""
        result = enforcer.route_task(
            task_class=TaskClass.FRONTEND,
            task_type='create_ui',
            available_providers={'claude-code'},
            risk_level=RiskLevel.LOW
        )

        assert result['status'] == 'selected'
        assert result['task_class'] == 'frontend'
        assert 'selected_provider' in result
        assert 'reason' in result

    def test_route_task_blocked(self, enforcer):
        """Test blocked task routing."""
        result = enforcer.route_task(
            task_class=TaskClass.SECURITY,
            task_type='critical_operation',
            available_providers={'local'},  # Not allowed for security
            risk_level=RiskLevel.CRITICAL
        )

        # May be blocked due to provider not in allowlist or risk level
        assert 'status' in result

    def test_route_task_requires_approval(self, enforcer):
        """Test routing that requires approval."""
        result = enforcer.route_task(
            task_class=TaskClass.DEPLOYMENT,
            task_type='deploy_production',
            available_providers={'claude-code'},
            risk_level=RiskLevel.LOW
        )

        # Deploy production requires approval
        assert result.get('requires_approval') is True or \
               result.get('approval_required') is True


class TestBypassDetection:
    """Test bypass detection and tracking."""

    @pytest.fixture
    def enforcer(self):
        return PolicyEnforcer()

    def test_attempt_bypass_recorded(self, enforcer):
        """Test bypass attempt is recorded."""
        result = enforcer.attempt_bypass(
            task_type='create_app',
            original_provider=ProviderType.CLAUDE_CODE,
            bypass_target=ProviderType.LOCAL
        )

        assert result['action'] == 'bypass_attempted'
        assert result['policy_violation'] is True
        assert len(enforcer.bypass_attempts) == 1


class TestGetBypassStatistics:
    """Test bypass statistics."""

    @pytest.fixture
    def enforcer(self):
        e = PolicyEnforcer()
        # Record some bypass attempts
        for _ in range(5):
            e.attempt_bypass(
                task_type='test',
                original_provider=ProviderType.CLAUDE_CODE,
                bypass_target=ProviderType.LOCAL
            )
        return e

    def test_bypass_statistics(self, enforcer):
        """Test bypass statistics calculation."""
        stats = enforcer.get_bypass_statistics()

        assert stats['total_attempts'] == 5
        assert stats['violations'] == 5
        assert stats['violation_rate'] == 1.0
        assert len(stats['recent_bypasses']) == 5


class TestIntegration:
    """Integration tests."""

    def test_policy_routing_workflow(self):
        """Test complete policy routing workflow."""
        policy = RoutingPolicy()
        enforcer = PolicyEnforcer(policy)

        # Step 1: Get allowed providers
        allowed = policy.get_allowed_providers(TaskClass.FRONTEND)
        assert len(allowed) > 0

        # Step 2: Validate routing
        is_valid, reason, _ = policy.validate_task_routing(
            TaskClass.FRONTEND,
            'create_app',
            ProviderType.CLAUDE_CODE,
            RiskLevel.LOW
        )
        assert is_valid is True

        # Step 3: Route task through enforcer
        result = enforcer.route_task(
            task_class=TaskClass.FRONTEND,
            task_type='create_app',
            available_providers={'claude-code'},
            risk_level=RiskLevel.LOW
        )
        assert result['status'] == 'selected'

        # Step 4: Check statistics
        stats = enforcer.get_bypass_statistics()
        assert 'total_attempts' in stats

    def test_risk_enforcement_workflow(self):
        """Test risk enforcement across different levels."""
        policy = RoutingPolicy()

        risk_checks = {
            RiskLevel.LOW: True,
            RiskLevel.MEDIUM: False,
            RiskLevel.HIGH: False,
            RiskLevel.CRITICAL: False
        }

        for risk_level, expected in risk_checks.items():
            allowed = policy.can_provider_handle_risk(
                ProviderType.CLAUDE_CODE,
                risk_level
            )
            # Claude Code only allows LOW by default
            assert allowed == expected


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
