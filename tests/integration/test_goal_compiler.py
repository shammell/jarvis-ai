"""
Test Suite: Project Goal Compiler

Tests for project_goal_compiler.py
- Goal compilation for frontend, backend, supabase requests
- Pattern matching accuracy
- Milestone generation
- Architecture determination
"""

import pytest
import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.project_goal_compiler import ProjectGoalCompiler, TaskClass, compile_goal


class TestPatternMatching:
    """Test pattern recognition for task categories."""

    @pytest.fixture
    def compiler(self):
        """Create a fresh compiler instance."""
        return ProjectGoalCompiler()

    def test_frontend_detection(self, compiler):
        """Test frontend task detection."""
        command = "build frontend + ui + interface"
        result = compiler.compile(command)

        frontend_reqs = [r for r in result.requirements if r['task_class'] == 'frontend']
        assert len(frontend_reqs) >= 1
        assert any('frontend' in r['source'] for r in frontend_reqs)

    def test_backend_detection(self, compiler):
        """Test backend task detection."""
        command = "build backend + api + server"
        result = compiler.compile(command)

        backend_reqs = [r for r in result.requirements if r['task_class'] == 'backend']
        assert len(backend_reqs) >= 1

    def test_supabase_detection(self, compiler):
        """Test supabase task detection."""
        command = "supabase database + postgres"
        result = compiler.compile(command)

        supabase_reqs = [r for r in result.requirements if r['task_class'] == 'supabase']
        assert len(supabase_reqs) >= 1

    def test_database_detection(self, compiler):
        """Test database task detection."""
        command = "design database schema postgres"
        result = compiler.compile(command)

        database_reqs = [r for r in result.requirements if r['task_class'] == 'database']
        assert len(database_reqs) >= 1

    def test_infrastructure_detection(self, compiler):
        """Test infrastructure task detection."""
        command = "deploy to aws with docker kubernetes"
        result = compiler.compile(command)

        infra_reqs = [r for r in result.requirements if r['task_class'] == 'infrastructure']
        assert len(infra_reqs) >= 1

    def test_testing_detection(self, compiler):
        """Test testing task detection."""
        command = "write tests + unit + integration e2e"
        result = compiler.compile(command)

        test_reqs = [r for r in result.requirements if r['task_class'] == 'testing']
        assert len(test_reqs) >= 1

    def test_security_detection(self, compiler):
        """Test security task detection."""
        command = "add security + auth + encryption"
        result = compiler.compile(command)

        security_reqs = [r for r in result.requirements if r['task_class'] == 'security']
        assert len(security_reqs) >= 1

    def test_no_matching_tasks(self, compiler):
        """Test command with no matching tasks."""
        command = "random gibberish nonsense text"
        result = compiler.compile(command)

        # Should have at least foundation milestone
        assert len(result.milestones) >= 1

    def test_priority_calculation(self, compiler):
        """Test priority calculation for tasks."""
        command = "critical urgent security auth deploy"
        result = compiler.compile(command)

        # Security should have high priority
        security_reqs = [r for r in result.requirements if r['task_class'] == 'security']
        if security_reqs:
            assert security_reqs[0]['priority'] >= 85

    def test_confidence_scoring(self, compiler):
        """Test confidence scoring for pattern matching."""
        command = "frontend react ui"
        result = compiler.compile(command)

        frontend_reqs = [r for r in result.requirements if r['task_class'] == 'frontend']
        if frontend_reqs:
            assert frontend_reqs[0]['confidence'] >= 0.85


class TestCompoundRequirements:
    """Test compound requirement handling."""

    @pytest.fixture
    def compiler(self):
        return ProjectGoalCompiler()

    def test_frontend_plus_backend(self, compiler):
        """Test frontend + backend compound requirement."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        frontend_count = sum(1 for r in result.requirements if r['task_class'] == 'frontend')
        backend_count = sum(1 for r in result.requirements if r['task_class'] == 'backend')

        assert frontend_count >= 1
        assert backend_count >= 1

    def test_frontend_backend_supabase(self, compiler):
        """Test complete stack requirement."""
        command = "build frontend + backend + supabase app"
        result = compiler.compile(command)

        frontend_count = sum(1 for r in result.requirements if r['task_class'] == 'frontend')
        backend_count = sum(1 for r in result.requirements if r['task_class'] == 'backend')
        supabase_count = sum(1 for r in result.requirements if r['task_class'] == 'supabase')

        assert frontend_count >= 1
        assert backend_count >= 1
        assert supabase_count >= 1

    def test_api_integration_implicit(self, compiler):
        """Test implicit API integration when frontend + backend."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        # Should have API-related tasks
        api_tasks = [m for m in result.milestones if 'integration' in m['name'].lower()]
        assert len(api_tasks) >= 1


class TestMilestoneGeneration:
    """Test milestone generation from requirements."""

    @pytest.fixture
    def compiler(self):
        return ProjectGoalCompiler()

    def test_foundation_milestone_first(self, compiler):
        """Test foundation milestone is first."""
        command = "build frontend"
        result = compiler.compile(command)

        assert len(result.milestones) >= 1
        first_milestone = result.milestones[0]
        assert 'Foundation' in first_milestone['name']
        assert first_milestone['phase'] == 'foundation'

    def test_milestone_dependencies(self, compiler):
        """Test milestone dependencies are set."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        # Later milestones should depend on foundation
        for milestone in result.milestones[1:]:
            assert 'M001' in milestone.get('dependencies', [])

    def test_integration_milestone_exists(self, compiler):
        """Test integration milestone exists."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        integration_milestone = [m for m in result.milestones if m['phase'] == 'integration']
        assert len(integration_milestone) >= 1

    def test_deployment_milestone_exists(self, compiler):
        """Test deployment milestone exists."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        deployment_milestone = [m for m in result.milestones if m['phase'] == 'deployment']
        assert len(deployment_milestone) >= 1

    def test_milestone_estimated_hours(self, compiler):
        """Test milestone hour estimates."""
        command = "build frontend"
        result = compiler.compile(command)

        frontend_milestone = [m for m in result.milestones
                             if 'Frontend' in m['name']]
        if frontend_milestone:
            assert frontend_milestone[0]['estimated_hours'] > 0


class TestArchitectureDetermination:
    """Test architecture determination based on requirements."""

    @pytest.fixture
    def compiler(self):
        return ProjectGoalCompiler()

    def test_fullstack_architecture(self, compiler):
        """Test fullstack architecture for frontend + backend."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        assert result.architecture['type'] == 'fullstack'
        assert 'frontend' in result.architecture
        assert 'backend' in result.architecture
        assert 'database' in result.architecture

    def test_supabase_architecture(self, compiler):
        """Test serverless fullstack for frontend + backend + supabase."""
        command = "build frontend + backend + supabase"
        result = compiler.compile(command)

        assert result.architecture['type'] == 'serverless_fullstack'
        assert result.architecture.get('database', {}).get('provider') == 'supabase'

    def test_database_only_architecture(self, compiler):
        """Test database-first architecture."""
        command = "design supabase database"
        result = compiler.compile(command)

        assert result.architecture['type'] == 'database_first'

    def test_frontend_only_architecture(self, compiler):
        """Test frontend-only architecture."""
        command = "build frontend ui"
        result = compiler.compile(command)

        assert result.architecture['type'] == 'frontend_only'
        assert 'frontend' in result.architecture

    def test_infrastructure_architecture(self, compiler):
        """Test infrastructure-first architecture."""
        command = "deploy to aws with docker"
        result = compiler.compile(command)

        assert result.architecture['type'] == 'infrastructure_first'


class TestToolSteps:
    """Test tool execution step generation."""

    @pytest.fixture
    def compiler(self):
        return ProjectGoalCompiler()

    def test_tool_steps_generated(self, compiler):
        """Test that tool steps are generated."""
        command = "build frontend"
        result = compiler.compile(command)

        assert len(result.tool_steps) > 0

    def test_tool_step_structure(self, compiler):
        """Test tool step has required fields."""
        command = "build frontend"
        result = compiler.compile(command)

        if result.tool_steps:
            step = result.tool_steps[0]
            assert 'step_id' in step
            assert 'milestone_id' in step
            assert 'task' in step
            assert 'tool_steps' in step or 'assigned_tools' in step

    def test_tool_step_parallelizable(self, compiler):
        """Test parallelizable flag is set."""
        command = "build frontend"
        result = compiler.compile(command)

        if result.tool_steps:
            step = result.tool_steps[0]
            assert 'parallelizable' in step
            assert 'estimated_time' in step


class TestVerificationChecklist:
    """Test verification checklist generation."""

    @pytest.fixture
    def compiler(self):
        return ProjectGoalCompiler()

    def test_checklist_generated(self, compiler):
        """Test verification checklist is generated."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        assert len(result.verification_checklist) > 0

    def test_checklist_general_tasks(self, compiler):
        """Test checklist has general verification tasks."""
        command = "build frontend"
        result = compiler.compile(command)

        checklist_str = ' '.join(result.verification_checklist)
        assert 'requirement' in checklist_str.lower() or 'build' in checklist_str.lower()

    def test_checklist_architecture_specific(self, compiler):
        """Test checklist has architecture-specific items."""
        command = "build frontend + backend"
        result = compiler.compile(command)

        checklist_str = ' '.join(result.verification_checklist)

        if 'frontend' in command:
            assert any('frontend' in c.lower() or 'respons' in c.lower()
                      for c in result.verification_checklist)


class TestCompileGoalFunction:
    """Test convenience function."""

    def test_compile_goal_returns_dict(self):
        """Test compile_goal returns dict format."""
        command = "build frontend + backend + supabase app"
        result = compile_goal(command)

        assert isinstance(result, dict)
        assert 'requirements' in result
        assert 'architecture' in result
        assert 'milestones' in result
        assert 'tool_steps' in result
        assert 'verification_checklist' in result


class TestIntegration:
    """Integration tests combining multiple features."""

    @pytest.fixture
    def compiler(self):
        return ProjectGoalCompiler()

    def test_fullstack_compilation(self, compiler):
        """Test complete fullstack compilation."""
        command = "build frontend + backend + supabase app"
        result = compiler.compile(command)

        # Verify all components present
        assert len(result.requirements) >= 3
        assert result.architecture['type'] == 'serverless_fullstack'
        assert len(result.milestones) >= 4  # Foundation + 3 components + Integration + Deployment
        assert len(result.tool_steps) > 0
        assert len(result.verification_checklist) > 0

        # Verify milestone count includes all phases
        phases = set(m['phase'] for m in result.milestones)
        assert 'foundation' in phases
        assert 'development' in phases
        assert 'integration' in phases
        assert 'deployment' in phases

    def test_single_component_compilation(self, compiler):
        """Test single component compilation."""
        command = "build frontend"
        result = compiler.compile(command)

        assert len(result.requirements) >= 1
        assert result.architecture['type'] == 'frontend_only'
        assert len(result.milestones) >= 3  # Foundation + Development + Integration + Deployment


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
