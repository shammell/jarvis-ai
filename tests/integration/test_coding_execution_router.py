"""
Test Suite: Coding Execution Router

Tests for coding_execution_router.py
- Route compiled execution plans to providers
- Provider selection and routing decisions
- Health check handling
- Fallback behavior
"""

import pytest
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from core.provider_contract import (
    ProviderContract,
    ProviderInfo,
    ProviderStatus,
    ProviderCapability,
    ProviderRegistry,
    ProviderHealthCheck,
    ClaudeCodeProvider
)
from core.routing_policy import (
    TaskClass,
    ProviderType,
    RoutingPolicy,
    PolicyEnforcer,
    RiskLevel
)
from core.coding_execution_router import (
    CodingExecutionRouter,
    RoutingDecision,
    RouterDecision,
    ExecutionPlan,
    create_router
)


class TestRouterInitialization:
    """Test router initialization."""

    def test_create_router(self):
        """Test create_router convenience function."""
        router = create_router()
        assert isinstance(router, CodingExecutionRouter)

    def test_router_with_custom_registry(self):
        """Test router initialization with custom registry."""
        registry = ProviderRegistry()
        router = CodingExecutionRouter(registry=registry)
        assert router.registry is registry

    def test_router_with_custom_policy(self):
        """Test router initialization with custom policy."""
        policy = RoutingPolicy()
        router = CodingExecutionRouter(policy=policy)
        assert router.policy is policy

    def test_router_property_access(self):
        """Test router property accessors."""
        router = create_router()

        assert isinstance(router.registry, ProviderRegistry)
        assert isinstance(router.policy, RoutingPolicy)
        assert isinstance(router.enforcer, PolicyEnforcer)


class TestRouteTask:
    """Test single task routing."""

    @pytest.fixture
    def router(self):
        router = create_router()
        # Register default provider
        provider = ClaudeCodeProvider()
        router.registry.register_provider(provider)
        return router

    def test_route_frontend_task(self, router):
        """Test routing frontend task."""
        compiled_goal = {
            'requirements': [{'task_class': 'frontend'}],
            'architecture': {},
            'milestones': [],
            'tool_steps': []
        }

        decision = router.route_task(
            compiled_goal=compiled_goal,
            task_class='frontend',
            task_type='create_frontend_app',
            risk_level='low'
        )

        assert decision.decision == RouterDecision.SELECTED
        assert decision.task_class == 'frontend'
        assert decision.task_type == 'create_frontend_app'
        assert decision.selected_provider is not None

    def test_route_backend_task(self, router):
        """Test routing backend task."""
        decision = router.route_task(
            compiled_goal={},
            task_class='backend',
            task_type='build_api',
            risk_level='low'
        )

        assert decision.decision == RouterDecision.SELECTED
        assert decision.task_class == 'backend'

    def test_route_supabase_task(self, router):
        """Test routing supabase task."""
        decision = router.route_task(
            compiled_goal={},
            task_class='supabase',
            task_type='configure_supabase',
            risk_level='low'
        )

        assert decision.decision == RouterDecision.SELECTED
        assert decision.task_class == 'supabase'

    def test_route_invalid_task_class(self, router):
        """Test routing with invalid task class."""
        decision = router.route_task(
            compiled_goal={},
            task_class='invalid_task_xyz',
            task_type='some_task',
            risk_level='low'
        )

        assert decision.decision == RouterDecision.INVALID_TASK_CLASS
        assert 'invalid' in decision.reason.lower()

    def test_route_with_high_risk(self, router):
        """Test routing with high risk level."""
        decision = router.route_task(
            compiled_goal={},
            task_class='security',
            task_type='security_scan',
            risk_level='high'
        )

        # High risk may require approval
        assert decision.decision in [RouterDecision.SELECTED, RouterDecision.NEEDS_APPROVAL]

    def test_route_with_no_healthy_provider(self, router):
        """Test routing when no healthy provider available."""
        # Unregister all providers
        for provider in router.registry._providers.values():
            provider.provider_info().status = ProviderStatus.UNHEALTHY

        decision = router.route_task(
            compiled_goal={},
            task_class='frontend',
            task_type='create_app',
            risk_level='low'
        )

        assert decision.decision == RouterDecision.NO_HEALTHY_PROVIDER
        assert 'healthy provider' in decision.reason.lower()


class TestRoutingDecision:
    """Test routing decision data structure."""

    def test_routing_decision_to_dict(self):
        """Test RoutingDecision serialization."""
        decision = RoutingDecision(
            decision=RouterDecision.SELECTED,
            task_class='frontend',
            task_type='create_ui',
            selected_provider='claude-code',
            fallback_chain=['claude-code', 'fallback'],
            risk_level='low',
            requires_approval=False,
            reason='Selected primary provider'
        )

        decision_dict = decision.to_dict()

        assert decision_dict['decision'] == 'selected'
        assert decision_dict['task_class'] == 'frontend'
        assert decision_dict['selected_provider'] == 'claude-code'
        assert 'timestamp' in decision_dict

    def test_routing_decision_defaults(self):
        """Test RoutingDecision default values."""
        decision = RoutingDecision(
            decision=RouterDecision.SELECTED,
            task_class='backend',
            task_type='build_api'
        )

        assert decision.selected_provider is None
        assert decision.fallback_chain == []
        assert decision.risk_level == 'low'
        assert decision.requires_approval is False


class TestProviderHealthChecks:
    """Test provider health checking."""

    @pytest.fixture
    def router(self):
        return create_router()

    def test_check_provider_health_healthy(self, router):
        """Test health check for healthy provider."""
        # Register a provider
        provider = ClaudeCodeProvider()
        router.registry.register_provider(provider)

        result = router.check_provider_health('claude-code')

        assert result is not None
        assert result.provider_info().status == ProviderStatus.HEALTHY

    def test_check_provider_health_unavailable(self, router):
        """Test health check for non-existent provider."""
        result = router.check_provider_health('nonexistent')

        assert result is None

    @pytest.mark.asyncio
    async def test_check_all_providers_health(self, router):
        """Test health check for all providers."""
        # Register providers
        provider = ClaudeCodeProvider()
        router.registry.register_provider(provider)

        results = await router.check_all_providers_health()

        assert 'claude-code' in results
        assert isinstance(results['claude-code'], bool)


class TestFallbackBehavior:
    """Test fallback behavior when primary provider unavailable."""

    @pytest.fixture
    def router(self):
        return create_router()

    def test_fallback_chain_included(self, router):
        """Test fallback chain is included in decision."""
        provider = ClaudeCodeProvider()
        router.registry.register_provider(provider)

        decision = router.route_task(
            compiled_goal={},
            task_class='frontend',
            task_type='create_app',
            risk_level='low'
        )

        assert 'fallback_chain' in decision.__dict__

    def test_fallback_when_primary_unavailable(self, router):
        """Test fallback when primary is unavailable."""
        # Set primary as unhealthy
        provider = router.registry.get_provider('claude-code')
        if provider:
            provider.provider_info().status = ProviderStatus.UNHEALTHY

        decision = router.route_task(
            compiled_goal={},
            task_class='frontend',
            task_type='create_app',
            risk_level='low'
        )

        # Should either find another provider or indicate no healthy option
        assert decision.decision in [RouterDecision.SELECTED, RouterDecision.NO_HEALTHY_PROVIDER]


class TestRoutingPlan:
    """Test routing complete execution plans."""

    @pytest.fixture
    def router(self):
        return create_router()

    def test_route_plan_multiple_milestones(self, router):
        """Test routing a complete execution plan."""
        compiled_goal = {
            'original_command': 'build frontend + backend',
            'intent': 'fullstack app',
            'requirements': [
                {'task_class': 'frontend', 'priority': 70},
                {'task_class': 'backend', 'priority': 75}
            ],
            'architecture': {'type': 'fullstack'},
            'milestones': [
                {'id': 'M001', 'name': 'Foundation', 'phase': 'foundation'},
                {'id': 'M002', 'name': 'Frontend', 'phase': 'development'},
                {'id': 'M003', 'name': 'Backend', 'phase': 'development'}
            ],
            'tool_steps': [
                {
                    'step_id': 'STP0001',
                    'milestone_id': 'M001',
                    'task': 'Initialize project',
                    'task_class': 'system',
                    'risk_level': 'low'
                },
                {
                    'step_id': 'STP0002',
                    'milestone_id': 'M002',
                    'task': 'Create components',
                    'task_class': 'frontend',
                    'risk_level': 'low'
                }
            ],
            'verification_checklist': ['Build passes', 'Tests pass']
        }

        results = router.route_plan(compiled_goal)

        # Should have results grouped by milestone
        assert len(results) > 0
        assert any('M001' in k or 'M002' in k for k in results.keys())

    def test_route_plan_empty(self, router):
        """Test routing empty plan."""
        compiled_goal = {
            'requirements': [],
            'architecture': {},
            'milestones': [],
            'tool_steps': []
        }

        results = router.route_plan(compiled_goal)

        assert results == {}


class TestAllowedProviders:
    """Test allowed providers for task classes."""

    @pytest.fixture
    def router(self):
        return create_router()

    def test_get_allowed_frontend_providers(self, router):
        """Test allowed providers for frontend."""
        providers = router.get_allowed_providers_for_class('frontend')

        assert len(providers) > 0
        assert 'claude-code' in providers

    def test_get_allowed_backend_providers(self, router):
        """Test allowed providers for backend."""
        providers = router.get_allowed_providers_for_class('backend')

        assert len(providers) > 0

    def test_get_allowed_invalid_task_class(self, router):
        """Test allowed providers for invalid task class."""
        providers = router.get_allowed_providers_for_class('invalid_xyz')

        assert len(providers) == 0


class TestValidation:
    """Test routing validation."""

    @pytest.fixture
    def router(self):
        return create_router()

    def test_validate_valid_routing(self, router):
        """Test validation of valid routing."""
        registry = router.registry
        provider = ClaudeCodeProvider()
        registry.register_provider(provider)

        is_valid, reason, suggestion = router.validate_routing(
            task_class='frontend',
            task_type='create_app',
            provider_id='claude-code'
        )

        assert is_valid is True
        assert 'valid' in reason.lower()

    def test_validate_invalid_task_class(self, router):
        """Test validation with invalid task class."""
        is_valid, reason, suggestion = router.validate_routing(
            task_class='invalid_xyz',
            task_type='create_app',
            provider_id='claude-code'
        )

        assert is_valid is False
        assert 'invalid' in reason.lower()


class TestRoutingStatistics:
    """Test routing statistics."""

    @pytest.fixture
    def router(self):
        return create_router()

    def test_routing_statistics_empty(self, router):
        """Test statistics with no decisions."""
        stats = router.get_routing_statistics()

        assert stats['total_decisions'] == 0
        assert stats['success_rate'] == 0

    def test_routing_statistics_with_decisions(self, router):
        """Test statistics after routing decisions."""
        # Make some decisions
        for _ in range(10):
            router.route_task(
                compiled_goal={},
                task_class='frontend',
                task_type='test_task',
                risk_level='low'
            )

        stats = router.get_routing_statistics()

        assert stats['total_decisions'] == 10
        assert stats['success_rate'] == 1.0  # All should succeed
        assert 'frontend' in stats['common_task_classes']
        assert 'common_providers' in stats


class TestExecutionPlan:
    """Test ExecutionPlan class."""

    def test_from_compiled_plan(self):
        """Test creating ExecutionPlan from compiled goal."""
        compiled_goal = {
            'original_command': 'build app',
            'intent': 'test',
            'requirements': [{'task_class': 'frontend'}],
            'architecture': {},
            'milestones': [{'id': 'M001'}],
            'tool_steps': [{'step_id': 'S1'}],
            'verification_checklist': ['Check 1']
        }

        plan = ExecutionPlan.from_compiled_plan(compiled_goal)

        assert plan.original_command == 'build app'
        assert len(plan.requirements) == 1
        assert len(plan.milestones) == 1


class TestIntegration:
    """Integration tests."""

    @pytest.fixture
    def router(self):
        return create_router()

    def test_complete_routing_workflow(self, router):
        """Test complete routing workflow."""
        # Register provider
        provider = ClaudeCodeProvider()
        router.registry.register_provider(provider)

        # Compile and route a plan
        compiled_goal = {
            'original_command': 'build frontend + backend + supabase app',
            'intent': 'fullstack with supabase',
            'requirements': [
                {'task_class': 'frontend'},
                {'task_class': 'backend'},
                {'task_class': 'supabase'}
            ],
            'architecture': {'type': 'serverless_fullstack'},
            'milestones': [
                {'id': 'M001', 'name': 'Foundation'},
                {'id': 'M002', 'name': 'Frontend'},
                {'id': 'M003', 'name': 'Backend'}
            ],
            'tool_steps': [
                {
                    'step_id': 'STP0001',
                    'milestone_id': 'M002',
                    'task': 'Create UI',
                    'task_class': 'frontend',
                    'risk_level': 'low'
                }
            ],
            'verification_checklist': ['Test']
        }

        decision = router.route_task(
            compiled_goal=compiled_goal,
            task_class='frontend',
            task_type='create_ui',
            risk_level='low'
        )

        assert decision.decision == RouterDecision.SELECTED
        assert decision.selected_provider is not None

        # Get plan routing
        plan_results = router.route_plan(compiled_goal)
        assert len(plan_results) > 0

        # Get statistics
        stats = router.get_routing_statistics()
        assert stats['total_decisions'] >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
