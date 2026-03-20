# ==========================================================
# JARVIS v9.0 - Swarm Coordinator
# OpenAI Swarm-style architecture for agent orchestration
# Agents pass state dictionary asynchronously
# Enhanced with Claude Code-inspired agent communication
# ==========================================================

import logging
from typing import Dict, Any, List, Optional, Callable
import asyncio
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class SwarmAgent:
    """Base class for swarm agents"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.state = {}

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent with current state

        Args:
            state: Shared state dictionary

        Returns:
            Updated state dictionary
        """
        raise NotImplementedError("Agents must implement execute()")

    def can_handle(self, state: Dict[str, Any]) -> bool:
        """Check if agent can handle current state"""
        return True


class SwarmCoordinator:
    """
    Swarm coordinator for JARVIS v9.0
    - Agents communicate via shared state
    - Asynchronous message passing
    - Dynamic agent selection
    - Similar to OpenAI Swarm / LangGraph
    - Enhanced with Claude Code-inspired agent communication
    """

    def __init__(self):
        self.agents: Dict[str, SwarmAgent] = {}
        self.execution_history = []
        self.max_iterations = 10
        self.agent_teams = {}  # For organizing agents into teams
        self.communication_log = []  # For tracking inter-agent communication

        logger.info("🐝 Swarm Coordinator initialized")

    def create_agent_team(self, team_name: str, agent_names: List[str]):
        """Create a team of agents that can work together"""
        team_agents = {name: self.agents[name] for name in agent_names if name in self.agents}
        self.agent_teams[team_name] = team_agents
        logger.info(f"👥 Created agent team '{team_name}' with {len(team_agents)} agents")

    async def execute_team(
        self,
        team_name: str,
        task: str,
        initial_state: Dict[str, Any] = None,
        max_iterations: int = None
    ) -> Dict[str, Any]:
        """
        Execute a task using a team of agents

        Args:
            team_name: Name of the agent team
            task: Task description
            initial_state: Initial state dictionary
            max_iterations: Maximum iterations

        Returns:
            Final state dictionary
        """
        if team_name not in self.agent_teams:
            raise ValueError(f"Team '{team_name}' does not exist")

        team_agents = self.agent_teams[team_name]
        max_iterations = max_iterations or self.max_iterations

        # Initialize state
        state = initial_state or {}
        state["task"] = task
        state["iteration"] = 0
        state["completed"] = False
        state["history"] = []
        state["team_name"] = team_name

        logger.info(f"🚀 Starting team execution: {team_name} for task: {task[:50]}...")

        # Execution loop
        for iteration in range(max_iterations):
            state["iteration"] = iteration

            # Select next agent from the team
            agent = self._select_agent_from_team(team_agents, state)

            if not agent:
                logger.warning(f"⚠️ No agent in team '{team_name}' can handle current state")
                break

            logger.info(f"🤖 Team {team_name} - Iteration {iteration}: {agent.name}")

            # Execute agent
            try:
                state = await agent.execute(state)

                # Record execution
                self.execution_history.append({
                    "iteration": iteration,
                    "agent": agent.name,
                    "team": team_name,
                    "timestamp": datetime.now().isoformat(),
                    "state_keys": list(state.keys())
                })

                # Record communication
                self.communication_log.append({
                    "timestamp": datetime.now().isoformat(),
                    "sender": agent.name,
                    "team": team_name,
                    "task": task[:50],
                    "state_update": list(state.keys())
                })

                # Check if completed
                if state.get("completed", False):
                    logger.info(f"✅ Team task completed in {iteration + 1} iterations")
                    break

            except Exception as e:
                logger.error(f"❌ Agent {agent.name} in team {team_name} failed: {e}")
                state["error"] = str(e)
                break

        state["total_iterations"] = iteration + 1
        state["team_execution"] = True

        return state

    def _select_agent_from_team(self, team_agents: Dict[str, SwarmAgent], state: Dict[str, Any]) -> Optional[SwarmAgent]:
        """Select next agent based on state from a specific team"""
        # Check if state specifies next agent
        if "next_agent" in state:
            agent_name = state.pop("next_agent")
            if agent_name in team_agents:
                return team_agents[agent_name]

        # Find first agent in team that can handle state
        for agent in team_agents.values():
            if agent.can_handle(state):
                return agent

        return None

    def register_agent(self, agent: SwarmAgent):
        """Register an agent with the swarm"""
        self.agents[agent.name] = agent
        logger.info(f"📝 Registered agent: {agent.name}")

    async def execute(
        self,
        task: str,
        initial_state: Dict[str, Any] = None,
        max_iterations: int = None
    ) -> Dict[str, Any]:
        """
        Execute task using swarm of agents

        Args:
            task: Task description
            initial_state: Initial state dictionary
            max_iterations: Maximum iterations

        Returns:
            Final state dictionary
        """
        max_iterations = max_iterations or self.max_iterations

        # Initialize state
        state = initial_state or {}
        state["task"] = task
        state["iteration"] = 0
        state["completed"] = False
        state["history"] = []

        logger.info(f"🚀 Starting swarm execution: {task[:50]}...")

        # Execution loop
        for iteration in range(max_iterations):
            state["iteration"] = iteration

            # Select next agent
            agent = self._select_agent(state)

            if not agent:
                logger.warning("⚠️ No agent can handle current state")
                break

            logger.info(f"🤖 Iteration {iteration}: {agent.name}")

            # Execute agent
            try:
                state = await agent.execute(state)

                # Record execution
                self.execution_history.append({
                    "iteration": iteration,
                    "agent": agent.name,
                    "timestamp": datetime.now().isoformat(),
                    "state_keys": list(state.keys())
                })

                # Check if completed
                if state.get("completed", False):
                    logger.info(f"✅ Task completed in {iteration + 1} iterations")
                    break

            except Exception as e:
                logger.error(f"❌ Agent {agent.name} failed: {e}")
                state["error"] = str(e)
                break

        state["total_iterations"] = iteration + 1

        return state

    def _select_agent(self, state: Dict[str, Any]) -> Optional[SwarmAgent]:
        """Select next agent based on state"""
        # Check if state specifies next agent
        if "next_agent" in state:
            agent_name = state.pop("next_agent")
            return self.agents.get(agent_name)

        # Find first agent that can handle state
        for agent in self.agents.values():
            if agent.can_handle(state):
                return agent

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get swarm statistics"""
        return {
            "registered_agents": len(self.agents),
            "total_executions": len(self.execution_history),
            "agents": [
                {"name": agent.name, "description": agent.description}
                for agent in self.agents.values()
            ]
        }


# Example agents
class PlannerAgent(SwarmAgent):
    """Agent that plans tasks"""

    def __init__(self):
        super().__init__("planner", "Plans task execution")

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        task = state.get("task", "")

        # Simple planning logic
        state["plan"] = [
            "Analyze requirements",
            "Execute implementation",
            "Verify results"
        ]
        state["next_agent"] = "executor"

        logger.info(f"📋 Planned {len(state['plan'])} steps")

        return state

    def can_handle(self, state: Dict[str, Any]) -> bool:
        return "plan" not in state


class ExecutorAgent(SwarmAgent):
    """Agent that executes tasks"""

    def __init__(self):
        super().__init__("executor", "Executes planned tasks")

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        plan = state.get("plan", [])

        # Execute plan steps
        state["results"] = []
        for step in plan:
            result = f"Executed: {step}"
            state["results"].append(result)
            logger.info(f"⚙️ {result}")

        state["next_agent"] = "verifier"

        return state

    def can_handle(self, state: Dict[str, Any]) -> bool:
        return "plan" in state and "results" not in state


class VerifierAgent(SwarmAgent):
    """Agent that verifies results"""

    def __init__(self):
        super().__init__("verifier", "Verifies task completion")

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results = state.get("results", [])

        # Verify results
        state["verified"] = len(results) > 0
        state["completed"] = state["verified"]

        logger.info(f"✅ Verification: {'passed' if state['verified'] else 'failed'}")

        return state

    def can_handle(self, state: Dict[str, Any]) -> bool:
        return "results" in state and "verified" not in state


# Test
if __name__ == "__main__":
    async def test_swarm():
        # Create coordinator
        coordinator = SwarmCoordinator()

        # Register agents
        coordinator.register_agent(PlannerAgent())
        coordinator.register_agent(ExecutorAgent())
        coordinator.register_agent(VerifierAgent())

        # Execute task
        result = await coordinator.execute("Build a new feature")

        print("\n" + "="*50)
        print("SWARM EXECUTION RESULT")
        print("="*50)
        print(f"Completed: {result.get('completed')}")
        print(f"Iterations: {result.get('total_iterations')}")
        print(f"Verified: {result.get('verified')}")

        print("\n" + "="*50)
        print("SWARM STATS")
        print("="*50)
        print(json.dumps(coordinator.get_stats(), indent=2))

    asyncio.run(test_swarm())
