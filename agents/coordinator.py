# ==========================================================
# Sub-Agent Coordinator
# Manages and coordinates all sub-agents
# ==========================================================

import logging
import asyncio
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.optimizer import OptimizerAgent
from agents.code_analyzer import CodeAnalyzerAgent
from agents.tester import TesterAgent
from agents.researcher import ResearcherAgent

logger = logging.getLogger(__name__)


class SubAgentCoordinator:
    """
    Coordinates multiple sub-agents
    - Agent selection
    - Task delegation
    - Result aggregation
    - Parallel execution
    """

    def __init__(self):
        # Initialize all sub-agents
        self.agents = {
            "Optimizer": OptimizerAgent(),
            "CodeAnalyzer": CodeAnalyzerAgent(),
            "Tester": TesterAgent(),
            "Researcher": ResearcherAgent()
        }

        logger.info(f"🤖 SubAgentCoordinator initialized with {len(self.agents)} agents")

    async def delegate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Delegate tasks to appropriate sub-agents

        Args:
            tasks: List of tasks with agent and task description

        Returns:
            Aggregated results from all agents
        """
        logger.info(f"🤖 Delegating {len(tasks)} tasks to sub-agents...")

        # Execute tasks in parallel
        results = await asyncio.gather(*[
            self._execute_task(task) for task in tasks
        ])

        # Aggregate results
        aggregated = {
            "tasks_completed": len(results),
            "tasks_successful": len([r for r in results if r.get("success")]),
            "results": results
        }

        logger.info(f"✅ Delegation complete: {aggregated['tasks_successful']}/{aggregated['tasks_completed']} successful")

        return aggregated

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task with appropriate agent"""
        agent_name = task.get("agent")
        task_description = task.get("task")
        context = task.get("context", {})

        if agent_name not in self.agents:
            return {
                "success": False,
                "error": f"Unknown agent: {agent_name}",
                "task": task_description
            }

        agent = self.agents[agent_name]

        try:
            # Route to appropriate agent method
            if agent_name == "Optimizer":
                result = await agent.optimize(task_description, context)
            elif agent_name == "CodeAnalyzer":
                code = context.get("code", "")
                language = context.get("language", "python")
                result = await agent.analyze(code, language)
            elif agent_name == "Tester":
                result = await agent.test(task_description, context)
            elif agent_name == "Researcher":
                result = await agent.research(task_description, context)
            else:
                result = {"error": "Agent method not implemented"}

            return {
                "success": True,
                "agent": agent_name,
                "task": task_description,
                "result": result
            }

        except Exception as e:
            logger.error(f"❌ Task failed: {agent_name} - {task_description}: {e}")
            return {
                "success": False,
                "agent": agent_name,
                "task": task_description,
                "error": str(e)
            }

    async def auto_delegate(self, user_request: str) -> Dict[str, Any]:
        """
        Automatically determine which agents to use based on request

        Args:
            user_request: User's request

        Returns:
            Results from appropriate agents
        """
        logger.info(f"🤖 Auto-delegating: {user_request}")

        tasks = []

        # Analyze request and determine agents
        request_lower = user_request.lower()

        if "optimize" in request_lower or "performance" in request_lower:
            tasks.append({
                "agent": "Optimizer",
                "task": user_request,
                "context": {}
            })

        if "analyze" in request_lower or "review" in request_lower:
            tasks.append({
                "agent": "CodeAnalyzer",
                "task": user_request,
                "context": {}
            })

        if "test" in request_lower:
            tasks.append({
                "agent": "Tester",
                "task": user_request,
                "context": {}
            })

        if "research" in request_lower or "explore" in request_lower:
            tasks.append({
                "agent": "Researcher",
                "task": user_request,
                "context": {}
            })

        if not tasks:
            # Default to researcher for general queries
            tasks.append({
                "agent": "Researcher",
                "task": user_request,
                "context": {}
            })

        return await self.delegate(tasks)


# Test
if __name__ == "__main__":
    async def test():
        coordinator = SubAgentCoordinator()

        # Test parallel delegation
        tasks = [
            {
                "agent": "Optimizer",
                "task": "optimize code performance",
                "context": {}
            },
            {
                "agent": "CodeAnalyzer",
                "task": "analyze code quality",
                "context": {"code": "def test(): pass", "language": "python"}
            },
            {
                "agent": "Tester",
                "task": "test function",
                "context": {}
            }
        ]

        print("\n" + "="*50)
        print("PARALLEL DELEGATION TEST")
        print("="*50)

        result = await coordinator.delegate(tasks)

        print(f"Tasks Completed: {result['tasks_completed']}")
        print(f"Tasks Successful: {result['tasks_successful']}")

        for r in result['results']:
            print(f"\n{r['agent']}: {'✅' if r['success'] else '❌'}")
            if r['success']:
                print(f"  Result: {list(r['result'].keys())}")

        # Test auto-delegation
        print("\n" + "="*50)
        print("AUTO-DELEGATION TEST")
        print("="*50)

        auto_result = await coordinator.auto_delegate("Optimize and test the code")

        print(f"Auto-delegated to {auto_result['tasks_completed']} agents")
        for r in auto_result['results']:
            print(f"  - {r['agent']}: {r['task']}")

    asyncio.run(test())
