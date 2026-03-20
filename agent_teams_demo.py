#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JARVIS v9.0 - Agent Teams Demo
Demonstrates Claude Code-inspired agent teaming capabilities
"""

import asyncio
import json
from datetime import datetime
import logging

from enhanced_autonomy import EnhancedAutonomySystem
from core.skill_loader import SkillLoader
from core.swarm_coordinator import SwarmCoordinator, SwarmAgent

logger = logging.getLogger(__name__)

class ResearchAgent(SwarmAgent):
    """Agent that performs research tasks"""

    def __init__(self):
        super().__init__("researcher", "Performs research and gathers information")

    async def execute(self, state: dict) -> dict:
        task = state.get("task", "")

        logger.info(f"🔬 Researching: {task}")

        # Simulate research process
        state["research_findings"] = [
            f"Finding 1 related to {task}",
            f"Finding 2 related to {task}",
            f"Finding 3 related to {task}"
        ]

        # Determine next step based on research
        if "optimize" in task.lower():
            state["next_agent"] = "optimizer"
        elif "build" in task.lower():
            state["next_agent"] = "builder"
        else:
            state["next_agent"] = "analyst"

        logger.info(f"✅ Completed research, passing to {state['next_agent']}")

        return state

    def can_handle(self, state: dict) -> bool:
        return "research_findings" not in state


class AnalystAgent(SwarmAgent):
    """Agent that analyzes information"""

    def __init__(self):
        super().__init__("analyst", "Analyzes information and provides insights")

    async def execute(self, state: dict) -> dict:
        findings = state.get("research_findings", [])

        logger.info(f"📊 Analyzing {len(findings)} research findings")

        # Simulate analysis process
        state["analysis"] = {
            "summary": f"Analysis of {len(findings)} findings",
            "key_insights": [f"Key insight from {finding}" for finding in findings[:2]],
            "recommendations": ["Recommendation 1", "Recommendation 2"]
        }

        state["next_agent"] = "planner"

        logger.info("✅ Completed analysis, passing to planner")

        return state

    def can_handle(self, state: dict) -> bool:
        return "research_findings" in state and "analysis" not in state


class BuilderAgent(SwarmAgent):
    """Agent that builds implementations"""

    def __init__(self):
        super().__init__("builder", "Builds implementations based on specifications")

    async def execute(self, state: dict) -> dict:
        task = state.get("task", "")
        analysis = state.get("analysis", {})

        logger.info(f"🔨 Building implementation for: {task}")

        # Simulate building process
        state["implementation"] = {
            "status": "built",
            "components": [f"Component for {task}", "Core module", "Utility functions"],
            "progress": 100
        }

        state["next_agent"] = "tester"

        logger.info("✅ Completed building, passing to tester")

        return state

    def can_handle(self, state: dict) -> bool:
        return "analysis" in state and "implementation" not in state


class TesterAgent(SwarmAgent):
    """Agent that tests implementations"""

    def __init__(self):
        super().__init__("tester", "Tests implementations and validates results")

    async def execute(self, state: dict) -> dict:
        implementation = state.get("implementation", {})

        logger.info(f"🧪 Testing implementation with {len(implementation.get('components', []))} components")

        # Simulate testing process
        state["test_results"] = {
            "passed": True,
            "tests_run": 10,
            "tests_passed": 10,
            "issues_found": [],
            "overall_grade": "A"
        }

        state["completed"] = True

        logger.info("✅ Testing complete, task finished")

        return state

    def can_handle(self, state: dict) -> bool:
        return "implementation" in state and "test_results" not in state


async def demo_agent_teams():
    """Demo function showcasing agent team capabilities"""
    print("\n" + "="*70)
    print("JARVIS v9.0 - Agent Teams Demo")
    print("Demonstrating Claude Code-inspired agent teaming")
    print("="*70)

    # Initialize the enhanced autonomy system
    skill_loader = SkillLoader("./skills")
    autonomy_system = EnhancedAutonomySystem(skill_loader=skill_loader)

    # Get reference to swarm coordinator
    swarm = autonomy_system.swarm_coordinator

    # Register specialized agents
    swarm.register_agent(ResearchAgent())
    swarm.register_agent(AnalystAgent())
    swarm.register_agent(BuilderAgent())
    swarm.register_agent(TesterAgent())

    # Create specialized teams
    swarm.create_agent_team("research_analysis_team", ["researcher", "analyst"])
    swarm.create_agent_team("development_team", ["builder", "tester"])
    swarm.create_agent_team("full_solution_team", ["researcher", "analyst", "builder", "tester"])

    print(f"\nRegistered {len(swarm.agents)} agents")
    print(f"Created {len(swarm.agent_teams)} agent teams")

    # Demo 1: Research and analysis task
    print("\n" + "-"*50)
    print("Demo 1: Research and Analysis Task")
    print("-"*50)

    result1 = await autonomy_system.execute_with_agent_team(
        task_description="Research the latest trends in AI agent architectures",
        team_name="research_analysis_team",
        context={"deadline": "today", "sources": ["arxiv", "github"]}
    )

    print(f"Task completed: {result1['success']}")
    print(f"Iterations: {result1['iterations']}")

    # Demo 2: Development task
    print("\n" + "-"*50)
    print("Demo 2: Development Task")
    print("-"*50)

    result2 = await autonomy_system.execute_with_agent_team(
        task_description="Build a recommendation engine for AI tools",
        team_name="development_team",
        context={"language": "python", "framework": "fastapi"}
    )

    print(f"Task completed: {result2['success']}")
    print(f"Iterations: {result2['iterations']}")

    # Demo 3: Full solution task
    print("\n" + "-"*50)
    print("Demo 3: Full Solution Task")
    print("-"*50)

    result3 = await autonomy_system.execute_with_agent_team(
        task_description="Create a complete AI agent system with memory and reasoning",
        team_name="full_solution_team",
        context={"requirements": ["memory", "reasoning", "communication"]}
    )

    print(f"Task completed: {result3['success']}")
    print(f"Iterations: {result3['iterations']}")

    # Print swarm statistics
    print("\n" + "-"*50)
    print("Swarm Statistics")
    print("-"*50)

    stats = swarm.get_stats()
    print(json.dumps(stats, indent=2))

    # Print communication log
    print("\n" + "-"*50)
    print("Communication Log (last 5 entries)")
    print("-"*50)

    # The communication log is in the swarm coordinator, but we need to access it
    # For now, let's just show that the system is working
    print("Communication tracking enabled for agent teams")

    print("\n" + "="*70)
    print("Demo completed successfully!")
    print("Agent teams functionality is now available in JARVIS")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(demo_agent_teams())