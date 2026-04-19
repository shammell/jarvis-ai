"""
Project Goal Compiler Module v2
Transforms voice commands and natural language into structured execution plans.

JARVIS v9.0+ - Multi-Provider Goal Compilation System

Integration with coding_execution_router.py for deterministic provider routing.
"""

from dataclasses import dataclass, field
from typing import Any
from enum import Enum
import re


class TaskClass(Enum):
    """Categorization for task routing decisions."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    INFRASTRUCTURE = "infrastructure"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    SECURITY = "security"
    DESIGN = "design"
    DOCUMENTATION = "documentation"
    SYSTEM = "system"
    SUPABASE = "supabase"


@dataclass
class CompiledGoal:
    """Structured representation of a compiled project goal."""
    requirements: list[dict[str, Any]] = field(default_factory=list)
    architecture: dict[str, Any] = field(default_factory=dict)
    milestones: list[dict[str, Any]] = field(default_factory=list)
    tool_steps: list[dict[str, Any]] = field(default_factory=list)
    verification_checklist: list[str] = field(default_factory=list)


class ProjectGoalCompiler:
    """
    Transforms natural language commands into structured execution plans.

    Input: "build frontend + backend + supabase app"
    Output: CompiledGoal with requirements, architecture, milestones, steps, and checks
    """

    # Pattern recognition rules for common phrases
    PATTERN_RULES = {
        r'\b(frontend|ui|interface|user interface|web front|frontend development)\b': {
            'task_class': TaskClass.FRONTEND,
            'keywords': ['frontend', 'ui', 'interface', 'react', 'vue', 'angular', 'html', 'css', 'javascript', 'typescript'],
            'default_tools': ['code_generator', 'ui_designer', 'component_builder']
        },
        r'\b(database|db|schema|sql|postgres|postgresql|mysql|mongodb)\b': {
            'task_class': TaskClass.DATABASE,
            'keywords': ['database', 'db', 'schema', 'sql', 'postgres', 'mysql', 'mongodb'],
            'default_tools': ['database_designer', 'schema_generator', 'migration_creator']
        },
        r'\b(backend|api|server|service|firebase)\b': {
            'task_class': TaskClass.BACKEND,
            'keywords': ['backend', 'api', 'server', 'service', 'firebase'],
            'default_tools': ['api_generator', 'database_designer', 'server_configurator']
        },
        r'\b(supabase|postgres|postgresql|database|db)\b': {
            'task_class': TaskClass.SUPABASE,
            'keywords': ['supabase', 'postgres', 'postgresql', 'database', 'db', 'schema'],
            'default_tools': ['schema_generator', 'migration_creator', 'db_designer']
        },
        r'\b(infrastructure|deploy|devops|cloud|aws|gcp|azure|docker|kubernetes|k8s)\b': {
            'task_class': TaskClass.INFRASTRUCTURE,
            'keywords': ['infrastructure', 'deploy', 'devops', 'cloud', 'aws', 'gcp', 'azure', 'docker', 'kubernetes'],
            'default_tools': ['infra_provisioner', 'deployment_planner', 'container_orchestrator']
        },
        r'\b(test|spec|qa|validation|unit|integration|e2e)\b': {
            'task_class': TaskClass.TESTING,
            'keywords': ['test', 'spec', 'qa', 'validation', 'unit', 'integration', 'e2e', 'jest', 'pytest'],
            'default_tools': ['test_generator', 'test_runner', 'coverage_analyzer']
        },
        r'\b(deploy|release|production|staging|ci\-cd)\b': {
            'task_class': TaskClass.DEPLOYMENT,
            'keywords': ['deploy', 'release', 'production', 'staging', 'pipeline', 'ci-cd'],
            'default_tools': ['deployment_executor', 'pipeline_configurator', 'release_manager']
        },
        r'\b(security|auth|authenticat|authorizat|encrypt|security)\b': {
            'task_class': TaskClass.SECURITY,
            'keywords': ['security', 'auth', 'authorization', 'encrypt', 'password', 'oauth', 'jwt'],
            'default_tools': ['security_analyzer', 'auth_configurator', 'vulnerability_scanner']
        },
        r'\b(design|ui\/ux|wireframe|mockup|prototype)\b': {
            'task_class': TaskClass.DESIGN,
            'keywords': ['design', 'ui/ux', 'wireframe', 'mockup', 'prototype', 'figma'],
            'default_tools': ['design_generator', 'prototype_builder', 'mockup_creator']
        },
        r'\b(doc|document|readme|guide|tutorial)\b': {
            'task_class': TaskClass.DOCUMENTATION,
            'keywords': ['doc', 'document', 'readme', 'guide', 'tutorial', 'api docs'],
            'default_tools': ['doc_generator', 'api_documenter', 'tutorial_creator']
        },
        r'\b(system|core|kernel|runtime)\b': {
            'task_class': TaskClass.SYSTEM,
            'keywords': ['system', 'core', 'kernel', 'runtime', 'basics'],
            'default_tools': ['system_configurator', 'runtime_builder']
        },
    }

    # Architecture templates
    ARCHITECTURE_TEMPLATES = {
        'fullstack': {
            'type': 'monolithic',
            'frontend': {
                'framework': 'react',
                'state_management': 'redux',
                'styling': 'tailwind-css'
            },
            'backend': {
                'framework': 'fastapi',
                'auth': 'jwt',
                'api_style': 'rest'
            },
            'database': {
                'type': 'postgresql',
                'orm': 'sqlalchemy'
            }
        },
        'microservices': {
            'type': 'microservices',
            'services': [],
            'api_gateway': True,
            'message_queue': True
        },
        'serverless': {
            'type': 'serverless',
            'functions': [],
            'provider': 'aws',
            'framework': 'serverless'
        }
    }

    def __init__(self):
        """Initialize the compiler with pattern rules."""
        self.pattern_rules = self.PATTERN_RULES
        self.architecture_templates = self.ARCHITECTURE_TEMPLATES

    def compile(self, command: str) -> CompiledGoal:
        """
        Compile a natural language command into a structured execution plan.

        Args:
            command: Natural language command (e.g., "build frontend + backend + supabase app")

        Returns:
            CompiledGoal with full execution plan
        """
        # Step 1: Parse and extract requirements
        requirements = self._extract_requirements(command)

        # Step 2: Determine architecture based on requirements
        architecture = self._determine_architecture(requirements)

        # Step 3: Generate milestones
        milestones = self._generate_milestones(requirements, architecture)

        # Step 4: Create tool execution steps
        tool_steps = self._generate_tool_steps(requirements, milestones)

        # Step 5: Create verification checklist
        verification_checklist = self._create_verification_checklist(requirements, milestones)

        return CompiledGoal(
            requirements=requirements,
            architecture=architecture,
            milestones=milestones,
            tool_steps=tool_steps,
            verification_checklist=verification_checklist
        )

    def _extract_requirements(self, command: str) -> list[dict[str, Any]]:
        """
        Extract structured requirements from natural language command.

        Args:
            command: Natural language command

        Returns:
            List of requirement dictionaries with task_class, description, and priority
        """
        requirements = []
        command_lower = command.lower()

        # Split by common separators (+, &, and, comma)
        segments = re.split(r'[\+&,\s]+', command_lower)
        segments = [s.strip() for s in segments if s.strip() and len(s) > 2]

        # Pattern matching for each segment
        found_tasks = set()

        for segment in segments:
            for pattern, config in self.pattern_rules.items():
                if re.search(pattern, segment, re.IGNORECASE):
                    task = {
                        'task_class': config['task_class'].value,
                        'keywords': config['keywords'],
                        'tools': config['default_tools'],
                        'priority': self._calculate_priority(segment, config['task_class']),
                        'confidence': self._calculate_confidence(segment, pattern),
                        'source': segment
                    }

                    # Avoid duplicates
                    task_key = f"{config['task_class'].value}:{segment}"
                    if task_key not in found_tasks:
                        found_tasks.add(task_key)
                        task['description'] = self._generate_task_description(segment, config['task_class'])
                        requirements.append(task)
                        break

        # Handle compound requests like "frontend + backend"
        if '+' in command or '&' in command:
            requirements = self._handle_compound_requirements(command, requirements)

        # Sort by priority
        requirements.sort(key=lambda x: x['priority'], reverse=True)

        return requirements

    def _calculate_priority(self, segment: str, task_class: TaskClass) -> int:
        """Calculate priority based on task type and context."""
        base_priority = {
            TaskClass.FRONTEND: 70,
            TaskClass.BACKEND: 75,
            TaskClass.DATABASE: 80,
            TaskClass.SUPABASE: 85,
            TaskClass.INFRASTRUCTURE: 85,
            TaskClass.TESTING: 60,
            TaskClass.DEPLOYMENT: 90,
            TaskClass.SECURITY: 95,
            TaskClass.DESIGN: 50,
            TaskClass.DOCUMENTATION: 40,
            TaskClass.SYSTEM: 88
        }

        # Boost priority for critical keywords
        critical_keywords = ['critical', 'urgent', 'must', 'require', 'essential']
        if any(kw in segment.lower() for kw in critical_keywords):
            return base_priority.get(task_class, 50) + 15

        return base_priority.get(task_class, 50)

    def _calculate_confidence(self, segment: str, pattern: str) -> float:
        """Calculate matching confidence score."""
        if re.search(pattern, segment, re.IGNORECASE):
            # Exact match gets higher confidence
            if segment in pattern or pattern in segment:
                return 0.95
            return 0.85
        return 0.5

    def _generate_task_description(self, segment: str, task_class: TaskClass) -> str:
        """Generate human-readable task description."""
        descriptions = {
            TaskClass.FRONTEND: f"Develop frontend user interface with {segment}",
            TaskClass.BACKEND: f"Build backend API and services for {segment}",
            TaskClass.DATABASE: f"Design and implement database schema for {segment}",
            TaskClass.SUPABASE: f"Configure Supabase backend for {segment}",
            TaskClass.INFRASTRUCTURE: f"Set up infrastructure and deployment for {segment}",
            TaskClass.TESTING: f"Create comprehensive tests for {segment}",
            TaskClass.DEPLOYMENT: f"Configure deployment pipeline for {segment}",
            TaskClass.SECURITY: f"Implement security measures for {segment}",
            TaskClass.DESIGN: f"Create UI/UX design for {segment}",
            TaskClass.DOCUMENTATION: f"Generate documentation for {segment}",
            TaskClass.SYSTEM: f"Implement system-level functionality for {segment}"
        }
        return descriptions.get(task_class, f"Implement {segment}")

    def _handle_compound_requirements(self, command: str,
                                       existing_requirements: list[dict]) -> list[dict]:
        """
        Handle compound requirements (e.g., "frontend + backend").
        Adds implicit dependencies and related requirements.
        """
        enhanced = existing_requirements.copy()

        # If both frontend and backend are present, ensure they're connected
        has_frontend = any(r['task_class'] == TaskClass.FRONTEND.value for r in enhanced)
        has_backend = any(r['task_class'] == TaskClass.BACKEND.value for r in enhanced)
        has_supabase = any(r['task_class'] in [TaskClass.SUPABASE.value, TaskClass.BACKEND.value]
                          for r in enhanced)

        # Add API integration requirement if both frontend and backend
        if has_frontend and has_backend:
            api_task = {
                'task_class': TaskClass.BACKEND.value,
                'keywords': ['api', 'integration', 'communication'],
                'tools': ['api_designer', 'integration_tester'],
                'priority': 70,
                'confidence': 0.9,
                'description': 'Design and implement API integration between frontend and backend',
                'source': 'implied by frontend+backend'
            }
            if not any(r.get('description') == api_task['description'] for r in enhanced):
                enhanced.append(api_task)

        return enhanced

    def _determine_architecture(self, requirements: list[dict]) -> dict:
        """
        Determine appropriate architecture based on requirements.

        Args:
            requirements: List of extracted requirements

        Returns:
            Architecture configuration dictionary
        """
        task_classes = set(r['task_class'] for r in requirements)

        # Fullstack detection with Supabase
        if (TaskClass.FRONTEND.value in task_classes and
            TaskClass.BACKEND.value in task_classes and
            TaskClass.SUPABASE.value in task_classes):
            return {
                'type': 'serverless_fullstack',
                'frontend': {
                    'framework': 'react',
                    'state_management': 'context',
                    'styling': 'tailwind-css',
                    'routing': 'react-router'
                },
                'backend': {
                    'framework': 'supabase',
                    'auth': 'jwtsupabase',
                    'api_style': 'rest'
                },
                'database': {
                    'type': 'postgresql',
                    'provider': 'supabase',
                    'migrations': True
                },
                'integration': {
                    'auth_strategy': 'supabase_auth',
                    'realtime': True
                }
            }

        # Fullstack without Supabase
        if TaskClass.FRONTEND.value in task_classes and TaskClass.BACKEND.value in task_classes:
            return {
                'type': 'fullstack',
                'frontend': {
                    'framework': 'react',
                    'state_management': 'context',
                    'styling': 'tailwind-css',
                    'routing': 'react-router'
                },
                'backend': {
                    'framework': 'fastapi',
                    'auth': 'jwt',
                    'api_style': 'rest',
                    'cors': True,
                    'validation': 'pydantic'
                },
                'database': {
                    'type': 'postgresql',
                    'orm': 'sqlalchemy',
                    'migration': 'alembic'
                },
                'integration': {
                    'api_strategy': 'rest',
                    'auth_strategy': 'jwt_with_refresh'
                }
            }

        # Database/Supabase-only
        elif TaskClass.DATABASE.value in task_classes or TaskClass.SUPABASE.value in task_classes:
            return {
                'type': 'database_first',
                'database': {
                    'type': 'postgresql',
                    'provider': TaskClass.SUPABASE.value if TaskClass.SUPABASE.value in task_classes else 'native',
                    'schema_design': 'normalized',
                    'migrations': True
                }
            }

        # Frontend-only
        elif TaskClass.FRONTEND.value in task_classes:
            return {
                'type': 'frontend_only',
                'frontend': {
                    'framework': 'react',
                    'state_management': 'context',
                    'styling': 'tailwind-css'
                }
            }

        # Infrastructure-focused
        elif TaskClass.INFRASTRUCTURE.value in task_classes:
            return {
                'type': 'infrastructure_first',
                'cloud_provider': 'aws',
                'containerization': 'docker',
                'orchestration': 'kubernetes',
                'ci_cd': 'github-actions'
            }

        # Default: modular monolith
        return {
            'type': 'modular_monolith',
            'scalability': 'modular',
            'layers': ['presentation', 'business_logic', 'data_access']
        }

    def _generate_milestones(self, requirements: list[dict],
                            architecture: dict) -> list[dict]:
        """
        Generate execution milestones from requirements.

        Args:
            requirements: Extracted requirements
            architecture: Determined architecture configuration

        Returns:
            List of milestone dictionaries
        """
        milestones = []
        milestone_num = 1

        # Foundation milestone (always first)
        milestones.append({
            'id': f'M{milestone_num:03d}',
            'name': 'Foundation & Setup',
            'phase': 'foundation',
            'dependencies': [],
            'tasks': ['Initialize project structure', 'Set up development environment',
                     'Configure version control', 'Setup basic build system'],
            'estimated_hours': 4,
            'deliverables': ['Initialized repository', 'Development environment ready']
        })
        milestone_num += 1

        # Milestones per requirement
        for req in requirements:
            milestone_name = self._get_milestone_name(req['task_class'], req.get('description', ''))

            milestone = {
                'id': f'M{milestone_num:03d}',
                'name': milestone_name,
                'phase': self._get_phase_by_task(req['task_class']),
                'dependencies': ['M001'],  # Depends on foundation
                'tasks': self._get_milestone_tasks(req['task_class'], req.get('tools', [])),
                'estimated_hours': self._estimate_milestone_hours(req['task_class']),
                'deliverables': self._get_milestone_deliverables(req['task_class'])
            }

            milestones.append(milestone)
            milestone_num += 1

        # Integration milestone
        integration_milestone = {
            'id': f'M{milestone_num:03d}',
            'name': 'Integration & Testing',
            'phase': 'integration',
            'dependencies': [m['id'] for m in milestones],
            'tasks': ['Integrate all components', 'Run integration tests',
                     'Performance testing', 'Security validation'],
            'estimated_hours': 8,
            'deliverables': ['Integrated system', 'Test reports']
        }
        milestones.append(integration_milestone)
        milestone_num += 1

        # Deployment milestone
        deployment_milestone = {
            'id': f'M{milestone_num:03d}',
            'name': 'Deployment & Production',
            'phase': 'deployment',
            'dependencies': ['M001', integration_milestone['id']],
            'tasks': ['Configure deployment environment', 'Deploy to staging',
                     'Final validation', 'Deploy to production', 'Monitor deployment'],
            'estimated_hours': 6,
            'deliverables': ['Production deployment', 'Monitor dashboard']
        }
        milestones.append(deployment_milestone)

        return milestones

    def _get_milestone_name(self, task_class: str, description: str) -> str:
        """Get user-friendly milestone name."""
        name_map = {
            TaskClass.FRONTEND.value: 'Frontend Development',
            TaskClass.BACKEND.value: 'Backend Development',
            TaskClass.DATABASE.value: 'Database Implementation',
            TaskClass.SUPABASE.value: 'Supabase Configuration',
            TaskClass.INFRASTRUCTURE.value: 'Infrastructure Setup',
            TaskClass.TESTING.value: 'Testing & QA',
            TaskClass.DEPLOYMENT.value: 'Deployment Setup',
            TaskClass.SECURITY.value: 'Security Implementation',
            TaskClass.DESIGN.value: 'Design & Prototyping',
            TaskClass.DOCUMENTATION.value: 'Documentation',
            TaskClass.SYSTEM.value: 'System Implementation'
        }
        return name_map.get(task_class, 'Implementation')

    def _get_phase_by_task(self, task_class: str) -> str:
        """Get phase category for milestone."""
        foundation_tasks = [TaskClass.FRONTEND.value, TaskClass.BACKEND.value,
                           TaskClass.DATABASE.value, TaskClass.SUPABASE.value]
        if task_class in foundation_tasks:
            return 'development'
        elif task_class in [TaskClass.TESTING.value, TaskClass.DEPLOYMENT.value]:
            return task_class
        else:
            return 'implementation'

    def _get_milestone_tasks(self, task_class: str, tools: list) -> list[str]:
        """Get specific tasks for a milestone."""
        task_templates = {
            TaskClass.FRONTEND.value: [
                'Create page components', 'Implement state management',
                'Add styling and themes', 'Implement routing',
                'Add responsive design'
            ],
            TaskClass.BACKEND.value: [
                'Design API endpoints', 'Implement business logic',
                'Add authentication', 'Create error handling',
                'Add logging and monitoring'
            ],
            TaskClass.DATABASE.value: [
                'Design database schema', 'Create migration files',
                'Set up relationships', 'Add indexes',
                'Configure connection pooling'
            ],
            TaskClass.SUPABASE.value: [
                'Initialize Supabase project', 'Configure database schema',
                'Set up authentication', 'Configure real-time subscriptions',
                'Setup storage buckets'
            ],
            TaskClass.INFRASTRUCTURE.value: [
                'Configure cloud resources', 'Setup containerization',
                'Create deployment scripts', 'Configure CI/CD pipelines'
            ],
            TaskClass.TESTING.value: [
                'Write unit tests', 'Create integration tests',
                'Setup test coverage', 'Configure test runners'
            ]
        }
        return task_templates.get(task_class, ['Implement functionality'])

    def _estimate_milestone_hours(self, task_class: str) -> int:
        """Estimate hours for milestone."""
        estimates = {
            TaskClass.FRONTEND.value: 16,
            TaskClass.BACKEND.value: 20,
            TaskClass.DATABASE.value: 12,
            TaskClass.SUPABASE.value: 10,
            TaskClass.INFRASTRUCTURE.value: 10,
            TaskClass.TESTING.value: 8,
            TaskClass.DEPLOYMENT.value: 6,
            TaskClass.SECURITY.value: 12,
            TaskClass.DESIGN.value: 8,
            TaskClass.DOCUMENTATION.value: 4,
            TaskClass.SYSTEM.value: 16
        }
        return estimates.get(task_class, 8)

    def _get_milestone_deliverables(self, task_class: str) -> list[str]:
        """Get deliverables for milestone."""
        deliverables_map = {
            TaskClass.FRONTEND.value: ['UI components', 'Responsive layout', 'State management'],
            TaskClass.BACKEND.value: ['API endpoints', 'Business logic', 'Error handling'],
            TaskClass.DATABASE.value: ['Schema', 'Migrations', 'Sample data'],
            TaskClass.SUPABASE.value: ['Supabase config', 'Auth setup', 'Database schema'],
            TaskClass.INFRASTRUCTURE.value: ['Infrastructure as code', 'Deployment config'],
            TaskClass.TESTING.value: ['Test suite', 'Coverage report'],
            TaskClass.DEPLOYMENT.value: ['Deployment scripts', 'Production environment'],
            TaskClass.SECURITY.value: ['Security implementation', 'Audit trail'],
            TaskClass.DESIGN.value: ['Design mockups', 'Prototype'],
            TaskClass.DOCUMENTATION.value: ['API docs', 'User guide'],
            TaskClass.SYSTEM.value: ['System components', 'Integration points']
        }
        return deliverables_map.get(task_class, ['Implemented feature'])

    def _generate_tool_steps(self, requirements: list[dict],
                            milestones: list[dict]) -> list[dict]:
        """
        Generate detailed tool execution steps.

        Args:
            requirements: Extracted requirements
            milestones: Generated milestones

        Returns:
            List of tool step dictionaries
        """
        steps = []
        step_id = 1

        for milestone in milestones:
            for task in milestone['tasks']:
                tool_step = {
                    'step_id': f'STP{step_id:04d}',
                    'milestone_id': milestone['id'],
                    'task': task,
                    'assigned_tools': self._get_tools_for_task(task, requirements),
                    'execution_order': step_id,
                    'parallelizable': self._is_task_parallelizable(task),
                    'estimated_time': self._estimate_task_time(task),
                    'success_criteria': self._get_success_criteria(task)
                }
                steps.append(tool_step)
                step_id += 1

        return steps

    def _get_tools_for_task(self, task: str, requirements: list[dict]) -> list[str]:
        """Get assigned tools for a task."""
        tool_map = {
            'Create page components': ['code_generator', 'component_builder'],
            'Implement state management': ['state_manager', 'context_builder'],
            'Design API endpoints': ['api_designer', 'swagger_generator'],
            'Implement business logic': ['logic_generator', 'business_rule_engine'],
            'Design database schema': ['schema_designer', 'db_architect'],
            'Configure Supabase project': ['supabase_cli', 'schema_generator'],
            'Configure deployment': ['deployment_configurator', 'infra_provisioner'],
            'Write unit tests': ['test_generator', 'unit_test_runner'],
            'Create integration tests': ['test_generator', 'integration_tester']
        }
        return tool_map.get(task, ['code_generator'])

    def _is_task_parallelizable(self, task: str) -> bool:
        """Determine if task can be parallelized."""
        parallel_tasks = [
            'Write unit tests',
            'Create integration tests',
            'Add styling and themes',
            'Implement routing',
            'Add logging and monitoring'
        ]
        return task in parallel_tasks

    def _estimate_task_time(self, task: str) -> int:
        """Estimate time for task in hours."""
        time_map = {
            'Create page components': 2,
            'Implement state management': 3,
            'Design API endpoints': 2,
            'Implement business logic': 4,
            'Design database schema': 3,
            'Configure Supabase project': 2,
            'Configure deployment': 2,
            'Write unit tests': 2,
            'Create integration tests': 3
        }
        return time_map.get(task, 2)

    def _get_success_criteria(self, task: str) -> str:
        """Get success criteria for task."""
        return f"Task '{task}' completed successfully with no errors"

    def _create_verification_checklist(self, requirements: list[dict],
                                       milestones: list[dict]) -> list[str]:
        """
        Create verification checklist for the completed project.

        Args:
            requirements: Extracted requirements
            milestones: Generated milestones

        Returns:
            List of verification checklist items
        """
        checklist = []

        # General requirements verification
        checklist.append("All requirements from original command are implemented")
        checklist.append("Project builds without errors")
        checklist.append("All tests pass (unit, integration, e2e)")

        # Architecture-specific checks
        if any(r['task_class'] == TaskClass.FRONTEND.value for r in requirements):
            checklist.append("Frontend is responsive across devices")
            checklist.append("UI components are reusable and modular")
            checklist.append("Frontend performance meets lighthouse criteria")

        if any(r['task_class'] == TaskClass.BACKEND.value for r in requirements):
            checklist.append("All API endpoints return correct responses")
            checklist.append("Authentication/authorization is implemented")
            checklist.append("Error handling is comprehensive")

        if any(r['task_class'] in [TaskClass.DATABASE.value, TaskClass.SUPABASE.value] for r in requirements):
            checklist.append("Database schema is normalized")
            checklist.append("Migrations are reversible")
            checklist.append("Indexes are optimized for queries")

        if any(r['task_class'] == TaskClass.SECURITY.value for r in requirements):
            checklist.append("Security vulnerabilities are scanned and fixed")
            checklist.append("Authentication tokens are securely stored")
            checklist.append("API endpoints are rate-limited")

        # Milestone verification
        for milestone in milestones:
            checklist.append(f"Deliverables for milestone {milestone['id']} ({milestone['name']}) completed")

        # Documentation
        checklist.append("Project documentation is complete")
        checklist.append("API documentation is accessible")
        checklist.append("Setup instructions are clear")

        return checklist


def compile_goal(command: str) -> dict:
    """
    Convenience function to compile a goal.

    Args:
        command: Natural language command

    Returns:
        CompiledGoal as dictionary
    """
    compiler = ProjectGoalCompiler()
    result = compiler.compile(command)

    return {
        'requirements': result.requirements,
        'architecture': result.architecture,
        'milestones': result.milestones,
        'tool_steps': result.tool_steps,
        'verification_checklist': result.verification_checklist
    }


# Example usage and testing
if __name__ == '__main__':
    compiler = ProjectGoalCompiler()

    # Test 1: Frontend + Backend + Supabase
    print("=" * 60)
    print("Test 1: Fullstack Application with Supabase")
    print("=" * 60)
    command1 = "build frontend + backend + supabase app"
    result1 = compiler.compile(command1)
    print(f"Command: {command1}")
    print(f"\nRequirements ({len(result1.requirements)}):")
    for req in result1.requirements:
        print(f"  - {req['task_class']}: {req['description']}")
    print(f"\nArchitecture type: {result1.architecture.get('type')}")
    print(f"\nMilestones ({len(result1.milestones)}):")
    for m in result1.milestones:
        print(f"  - [{m['id']}] {m['name']} ({m['phase']})")
    print(f"\nTool Steps ({len(result1.tool_steps)}):")
    print(f"  First 3 steps: {[s['task'] for s in result1.tool_steps[:3]]}")
    print(f"\nVerification Checklist ({len(result1.verification_checklist)}):")
    for check in result1.verification_checklist[:5]:
        print(f"  * {check}")

    # Test 2: Database-focused
    print("\n" + "=" * 60)
    print("Test 2: Supabase Database Implementation")
    print("=" * 60)
    command2 = "design supabase database with user authentication"
    result2 = compiler.compile(command2)
    print(f"Command: {command2}")
    print(f"\nRequirements:")
    for req in result2.requirements:
        print(f"  - {req['task_class']}: {req['description']}")

    # Test 3: Infrastructure
    print("\n" + "=" * 60)
    print("Test 3: Infrastructure Setup")
    print("=" * 60)
    command3 = "deploy to aws with docker and kubernetes"
    result3 = compiler.compile(command3)
    print(f"Command: {command3}")
    print(f"\nRequirements:")
    for req in result3.requirements:
        print(f"  - {req['task_class']}: {req['description']}")
    print(f"\nArchitecture: {result3.architecture}")
