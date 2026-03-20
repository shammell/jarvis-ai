# ==========================================================
# Jruce v9.0 - Workflow Synthesizer
# Auto-composes multi-skill workflows from user goals
# ==========================================================

import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import asyncio
import re

from core.skill_graph import SkillGraph, SkillNode

logger = logging.getLogger(__name__)


@dataclass
class WorkflowStep:
    """A single step in a synthesized workflow"""
    step_id: int
    skill_name: str
    description: str
    input_required: str
    output_produced: str
    dependencies: List[int]  # Step IDs this depends on
    parallel_group: int = 0
    estimated_time_ms: int = 500
    risk_score: float = 3.0


@dataclass
class SynthesizedWorkflow:
    """A complete synthesized workflow"""
    workflow_id: str
    goal: str
    steps: List[WorkflowStep]
    total_steps: int
    parallel_groups: int
    estimated_time_ms: int
    total_risk: float
    composition_valid: bool
    validation_msg: str
    created_at: str


class WorkflowSynthesizer:
    """
    Synthesizes workflows from user goals by:
    1. Parsing goal intent
    2. Querying skill graph for matching skills
    3. Composing valid skill chains
    4. Validating type compatibility
    5. Parallelizing independent steps
    """

    def __init__(self, skill_graph: SkillGraph = None):
        self.skill_graph = skill_graph or SkillGraph()

        # Goal patterns for intent parsing
        self.goal_patterns = {
            "audit": {
                "keywords": ["audit", "review", "assess", "evaluate", "check"],
                "skills": ["security-audit", "code-review", "performance-analysis"],
                "output": "report"
            },
            "fix": {
                "keywords": ["fix", "debug", "resolve", "repair", "correct"],
                "skills": ["debug", "fix-bug", "error-resolution"],
                "output": "fixed_code"
            },
            "optimize": {
                "keywords": ["optimize", "improve", "speed", "accelerate", "tune"],
                "skills": ["performance-optimization", "code-optimization", "caching-strategies"],
                "output": "optimized_system"
            },
            "generate": {
                "keywords": ["generate", "create", "build", "write", "implement"],
                "skills": ["code-generation", "scaffold", "template-create"],
                "output": "code"
            },
            "test": {
                "keywords": ["test", "verify", "validate", "qa", "quality"],
                "skills": ["unit-test", "integration-test", "e2e-test"],
                "output": "test_results"
            },
            "analyze": {
                "keywords": ["analyze", "understand", "explore", "investigate"],
                "skills": ["code-analysis", "data-analysis", "static-analysis"],
                "output": "insights"
            },
            "deploy": {
                "keywords": ["deploy", "release", "publish", "ship"],
                "skills": ["deploy", "ci-cd", "release-management"],
                "output": "deployment"
            }
        }

        # Workflow templates for common goals
        self.templates = {
            "security_audit": [
                "static-security-analysis",
                "api-security-testing",
                "007",
                "generate-security-report"
            ],
            "performance_optimize": [
                "performance-profiling",
                "bottleneck-detection",
                "application-performance-optimization",
                "benchmark-verification"
            ],
            "bug_fix": [
                "debug",
                "root-cause-analysis",
                "fix-bug",
                "regression-test"
            ],
            "code_generation": [
                "requirements-analysis",
                "architecture-design",
                "code-generation",
                "unit-test-generation"
            ]
        }

        logger.info("🔬 Workflow Synthesizer initialized")

    def synthesize(self, goal: str, context: Dict[str, Any] = None) -> SynthesizedWorkflow:
        """Synthesize a workflow from a goal"""
        logger.info(f"🎯 Synthesizing workflow for: {goal}")

        # Step 1: Parse goal intent
        intent = self._parse_intent(goal)

        # Step 2: Find matching skills
        matched_skills = self._find_matching_skills(goal, intent)

        # Step 3: Build skill chain
        skill_chain = self._build_chain(matched_skills, goal)

        # Step 4: Create workflow steps
        steps = self._create_steps(skill_chain, goal)

        # Step 5: Parallelize
        parallel_groups = self._parallelize(steps)

        # Step 6: Validate composition
        valid, msg = self.skill_graph.validate_composition(skill_chain)

        # Step 7: Build workflow
        workflow = self._build_workflow(goal, steps, parallel_groups, valid, msg)

        logger.info(f"✅ Workflow synthesized: {workflow.workflow_id}")
        return workflow

    def _parse_intent(self, goal: str) -> Dict[str, Any]:
        """Parse goal into intent categories"""
        goal_lower = goal.lower()

        intent = {
            "primary_action": None,
            "target": None,
            "constraints": [],
            "confidence": 0.0
        }

        # Match primary action
        for action_type, config in self.goal_patterns.items():
            for keyword in config["keywords"]:
                if keyword in goal_lower:
                    intent["primary_action"] = action_type
                    intent["confidence"] = 0.7
                    break

            if intent["primary_action"]:
                break

        # Extract target (what's being acted on)
        target_patterns = {
            "api": ["api", "endpoint", "route", "handler"],
            "code": ["code", "function", "module", "component"],
            "system": ["system", "application", "service", "app"],
            "security": ["security", "auth", "authentication", "authorization"],
            "performance": ["performance", "speed", "latency", "response"]
        }

        for target_type, keywords in target_patterns.items():
            for kw in keywords:
                if kw in goal_lower:
                    intent["target"] = target_type
                    intent["confidence"] += 0.1
                    break

        # Extract constraints
        if "fast" in goal_lower or "quick" in goal_lower:
            intent["constraints"].append("speed")
        if "safe" in goal_lower or "careful" in goal_lower:
            intent["constraints"].append("safety")
        if "minimal" in goal_lower:
            intent["constraints"].append("minimal_change")

        if not intent["primary_action"]:
            intent["primary_action"] = "analyze"  # Default
            intent["confidence"] = 0.3

        return intent

    def _find_matching_skills(self, goal: str, intent: Dict) -> List[str]:
        """Find skills matching the goal"""
        matches = []

        # Use skill graph matching
        graph_matches = self.skill_graph._match_goal(goal)
        matches.extend(graph_matches[:5])

        # Add template matches
        for template_name, skills in self.templates.items():
            if template_name in intent.get("primary_action", "") or template_name in goal.lower():
                matches.extend(skills)

        # Add action-specific skills
        action = intent.get("primary_action", "")
        if action in self.goal_patterns:
            action_skills = self.goal_patterns[action]["skills"]
            matches.extend(action_skills)

        # Dedupe and return
        return list(set(matches))

    def _build_chain(self, skills: List[str], goal: str) -> List[str]:
        """Build a valid skill chain"""
        if not skills:
            return []

        # Try to find chain from skill graph
        chain = self.skill_graph.find_skill_chain(goal, max_length=5)

        if chain:
            return chain

        # Fallback: order by dependencies
        ordered = []
        remaining = set(skills)

        while remaining:
            # Pick skill with no unscheduled predecessors
            for skill in remaining:
                if skill not in self.skill_graph.skills:
                    continue

                predecessors = set(self.skill_graph.graph.predecessors(skill))
                if not predecessors.intersection(remaining):
                    ordered.append(skill)
                    remaining.discard(skill)
                    break
            else:
                # No progress - just add one
                ordered.append(list(remaining)[0])
                remaining = remaining - {list(remaining)[0]}

        return ordered[:5]  # Limit to 5 steps

    def _create_steps(self, skill_chain: List[str], goal: str) -> List[WorkflowStep]:
        """Create workflow steps from skill chain"""
        steps = []

        for i, skill_name in enumerate(skill_chain):
            skill_info = self.skill_graph.get_skill_info(skill_name)

            if not skill_info:
                # Create minimal step
                steps.append(WorkflowStep(
                    step_id=i,
                    skill_name=skill_name,
                    description=f"Execute {skill_name}",
                    input_required="any",
                    output_produced="any",
                    dependencies=[i-1] if i > 0 else []
                ))
                continue

            # Build step from skill info
            deps = []
            if i > 0:
                deps.append(i - 1)  # Depends on previous step

            steps.append(WorkflowStep(
                step_id=i,
                skill_name=skill_name,
                description=skill_info.get("description", f"Execute {skill_name}"),
                input_required=skill_info.get("input_type", "any"),
                output_produced=skill_info.get("output_type", "any"),
                dependencies=deps,
                estimated_time_ms=self._estimate_time(skill_name),
                risk_score=self._estimate_risk(skill_name)
            ))

        return steps

    def _estimate_time(self, skill_name: str) -> int:
        """Estimate execution time for skill"""
        time_estimates = {
            "analyze": 300,
            "test": 500,
            "audit": 800,
            "optimize": 600,
            "fix": 400,
            "generate": 500,
            "deploy": 1000
        }

        for prefix, time in time_estimates.items():
            if prefix in skill_name.lower():
                return time

        return 500  # Default

    def _estimate_risk(self, skill_name: str) -> float:
        """Estimate risk score for skill"""
        if skill_name not in self.skill_graph.skills:
            return 3.0

        skill = self.skill_graph.skills[skill_name]

        # Base risk from skill metadata
        risk_map = {
            "unknown": 3.0,
            "low": 2.0,
            "medium": 5.0,
            "high": 7.0,
            "critical": 9.0
        }

        base_risk = risk_map.get(skill.risk_level, 3.0)

        # Adjust by output type (destructive outputs = higher risk)
        if skill.output_type in ["deployment", "deleted", "modified"]:
            base_risk += 2.0

        return min(base_risk, 10.0)

    def _parallelize(self, steps: List[WorkflowStep]) -> List[List[int]]:
        """Group steps that can run in parallel"""
        if len(steps) <= 1:
            return [[0]] if steps else []

        groups = []
        scheduled = set()

        while len(scheduled) < len(steps):
            # Find steps with all dependencies scheduled
            ready = []
            for step in steps:
                if step.step_id in scheduled:
                    continue
                if all(d in scheduled for d in step.dependencies):
                    ready.append(step.step_id)

            if ready:
                groups.append(ready)
                scheduled.update(ready)
            else:
                # Stuck - schedule one at a time
                for step in steps:
                    if step.step_id not in scheduled:
                        groups.append([step.step_id])
                        scheduled.add(step.step_id)
                        break

        return groups

    def _build_workflow(
        self,
        goal: str,
        steps: List[WorkflowStep],
        parallel_groups: List[List[int]],
        valid: bool,
        msg: str
    ) -> SynthesizedWorkflow:
        """Build final workflow object"""
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        total_time = sum(s.estimated_time_ms for s in steps)
        total_risk = max(s.risk_score for s in steps) if steps else 0

        return SynthesizedWorkflow(
            workflow_id=workflow_id,
            goal=goal,
            steps=steps,
            total_steps=len(steps),
            parallel_groups=len(parallel_groups),
            estimated_time_ms=total_time,
            total_risk=total_risk,
            composition_valid=valid,
            validation_msg=msg,
            created_at=datetime.now().isoformat()
        )

    async def execute_workflow(
        self,
        workflow: SynthesizedWorkflow,
        initial_state: Dict[str, Any] = None,
        executor = None
    ) -> Dict[str, Any]:
        """Execute a synthesized workflow"""
        logger.info(f"▶️ Executing workflow: {workflow.workflow_id}")

        results = {}
        state = initial_state or {}

        for step in workflow.steps:
            logger.info(f"  Step {step.step_id}: {step.skill_name}")

            # Execute skill using AutonomousExecutor if provided
            if executor:
                task = {
                    "type": "workflow_step",
                    "description": f"Execute skill: {step.skill_name}",
                    "skill": step.skill_name,
                    "context": state,
                    "confidence": 0.85,
                    "critical": True
                }

                step_result = await executor._execute_task(task)

                # Remove context from task to prevent circular references and massive outputs
                if "task" in step_result and "context" in step_result["task"]:
                    step_result["task"] = step_result["task"].copy()
                    step_result["task"].pop("context", None)

                # Check execution status
                if step_result.get("status") in ["failed", "blocked"]:
                    logger.warning(f"⚠️ Workflow halted at step {step.step_id}: {step_result.get('status')}")
                    return {
                        "workflow_id": workflow.workflow_id,
                        "goal": workflow.goal,
                        "success": False,
                        "steps_completed": step.step_id,
                        "results": results,
                        "final_state": state,
                        "error_step": step_result
                    }

                # Output successfully generated
                results[step.step_id] = step_result
                state[f"step_{step.step_id}_output"] = step_result
            else:
                # Placeholder fallback if no executor provided
                step_result = {
                    "step_id": step.step_id,
                    "skill": step.skill_name,
                    "status": "completed",
                    "output": f"Output from {step.skill_name}"
                }
                results[step.step_id] = step_result
                state[f"step_{step.step_id}_output"] = step_result

        return {
            "workflow_id": workflow.workflow_id,
            "goal": workflow.goal,
            "success": True,
            "steps_completed": workflow.total_steps,
            "results": results,
            "final_state": state
        }

    def get_workflow_info(self, workflow: SynthesizedWorkflow) -> Dict[str, Any]:
        """Get workflow information for display"""
        return {
            "workflow_id": workflow.workflow_id,
            "goal": workflow.goal,
            "total_steps": workflow.total_steps,
            "parallel_groups": workflow.parallel_groups,
            "estimated_time_ms": workflow.estimated_time_ms,
            "total_risk": workflow.total_risk,
            "composition_valid": workflow.composition_valid,
            "steps": [
                {
                    "step_id": s.step_id,
                    "skill": s.skill_name,
                    "description": s.description,
                    "dependencies": s.dependencies,
                    "parallel_group": s.parallel_group
                }
                for s in workflow.steps
            ]
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get synthesizer statistics"""
        return {
            "skill_graph_stats": self.skill_graph.get_stats(),
            "templates_loaded": len(self.templates),
            "goal_patterns": len(self.goal_patterns)
        }


# Test
if __name__ == "__main__":
    synth = WorkflowSynthesizer()

    print("\n" + "=" * 60)
    print("WORKFLOW SYNTHESIZER TEST")
    print("=" * 60)

    test_goals = [
        "Audit API security",
        "Optimize performance",
        "Fix the bug in login",
        "Generate test cases"
    ]

    for goal in test_goals:
        print(f"\nGoal: {goal}")
        workflow = synth.synthesize(goal)
        info = synth.get_workflow_info(workflow)
        print(f"  Workflow ID: {info['workflow_id']}")
        print(f"  Steps: {info['total_steps']}")
        print(f"  Parallel groups: {info['parallel_groups']}")
        print(f"  Est. time: {info['estimated_time_ms']}ms")
        print(f"  Risk: {info['total_risk']}")
        print(f"  Valid: {info['composition_valid']}")
        print(f"  Steps: {[s['skill'] for s in info['steps']]}")
