# ==========================================================
# JARVIS v9.0 - Autonomous Task Executor
# High-level goal execution with minimal user intervention
# Breaks down goals, executes steps, asks only when necessary
# ==========================================================

import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class AutonomousExecutor:
    """
    Autonomous task execution engine
    - Takes high-level goals
    - Breaks down into steps
    - Executes with minimal user input
    - Uses AutonomousDecision for risk assessment
    - Reports progress
    """

    def __init__(self, autonomous_decision, skill_loader=None):
        self.autonomous_decision = autonomous_decision
        self.skill_loader = skill_loader

        # Task tracking
        self.current_goal = None
        self.task_queue = []
        self.completed_tasks = []
        self.failed_tasks = []

        # Execution state
        self.is_executing = False
        self.pause_requested = False

        # Callbacks
        self.on_task_complete = None
        self.on_need_approval = None
        self.on_progress_update = None

        logger.info("🤖 Autonomous Executor initialized")

    async def execute_goal(
        self,
        goal: str,
        context: Dict[str, Any] = None,
        max_steps: int = 50
    ) -> Dict[str, Any]:
        """
        Execute a high-level goal autonomously

        Args:
            goal: High-level goal description
            context: Additional context
            max_steps: Maximum steps to prevent infinite loops

        Returns:
            Execution result with status and outcomes
        """
        logger.info(f"🎯 Starting autonomous execution: {goal}")

        self.current_goal = {
            "description": goal,
            "context": context or {},
            "started_at": datetime.now().isoformat(),
            "status": TaskStatus.IN_PROGRESS.value
        }

        self.is_executing = True

        try:
            # Step 1: Decompose goal into tasks
            tasks = await self._decompose_goal(goal, context)
            self.task_queue = tasks

            logger.info(f"📋 Goal decomposed into {len(tasks)} tasks")
            self._report_progress(f"Decomposed goal into {len(tasks)} tasks")

            # Step 2: Execute tasks sequentially
            step_count = 0
            while self.task_queue and step_count < max_steps:
                if self.pause_requested:
                    logger.info("⏸️ Execution paused by user")
                    break

                task = self.task_queue.pop(0)
                result = await self._execute_task(task)

                if result["status"] == TaskStatus.COMPLETED.value:
                    self.completed_tasks.append(result)

                    # Check if task generated new subtasks
                    if result.get("subtasks"):
                        self.task_queue = result["subtasks"] + self.task_queue
                        logger.info(f"➕ Added {len(result['subtasks'])} subtasks")

                elif result["status"] == TaskStatus.FAILED.value:
                    self.failed_tasks.append(result)

                    # Decide whether to continue or stop
                    if result.get("critical", False):
                        logger.error(f"❌ Critical task failed: {task['description']}")
                        break
                    else:
                        logger.warning(f"⚠️ Non-critical task failed, continuing...")

                elif result["status"] == TaskStatus.BLOCKED.value:
                    # Task needs user input
                    logger.info(f"🚧 Task blocked, waiting for user input")
                    user_input = await self._request_user_input(task, result)

                    if user_input:
                        # Retry with user input
                        task["user_input"] = user_input
                        self.task_queue.insert(0, task)
                    else:
                        # User declined, mark as failed
                        self.failed_tasks.append(result)

                step_count += 1
                self._report_progress(f"Completed {len(self.completed_tasks)}/{len(self.completed_tasks) + len(self.task_queue)} tasks")

            # Step 3: Generate final report
            self.current_goal["status"] = TaskStatus.COMPLETED.value
            self.current_goal["completed_at"] = datetime.now().isoformat()

            result = {
                "success": len(self.failed_tasks) == 0,
                "goal": goal,
                "completed_tasks": len(self.completed_tasks),
                "failed_tasks": len(self.failed_tasks),
                "remaining_tasks": len(self.task_queue),
                "steps_taken": step_count,
                "outcomes": self._generate_outcomes()
            }

            logger.info(f"✅ Goal execution complete: {result['completed_tasks']} tasks completed")

            return result

        except Exception as e:
            logger.error(f"❌ Goal execution failed: {e}")
            self.current_goal["status"] = TaskStatus.FAILED.value
            return {
                "success": False,
                "error": str(e),
                "completed_tasks": len(self.completed_tasks),
                "failed_tasks": len(self.failed_tasks)
            }

        finally:
            self.is_executing = False

    async def _decompose_goal(
        self,
        goal: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Decompose high-level goal into executable tasks

        This is where we break down the goal into concrete steps.
        In a real implementation, this would use LLM reasoning.
        """
        # Simple heuristic decomposition (replace with LLM in production)
        tasks = []

        # Check if we have relevant skills
        if self.skill_loader:
            matching_skills = self.skill_loader.find_matching_skills(goal)
            if matching_skills:
                logger.info(f"🎯 Found {len(matching_skills)} matching skills")
                for skill in matching_skills[:5]:  # Top 5 skills
                    tasks.append({
                        "type": "skill_execution",
                        "description": f"Execute skill: {skill['name']}",
                        "skill": skill,
                        "confidence": 0.8,
                        "critical": False
                    })

        # Generic task decomposition
        goal_lower = goal.lower()

        if "optimize" in goal_lower or "improve" in goal_lower:
            tasks.extend([
                {
                    "type": "analysis",
                    "description": "Analyze current system performance",
                    "confidence": 0.9,
                    "critical": True
                },
                {
                    "type": "identification",
                    "description": "Identify bottlenecks and issues",
                    "confidence": 0.8,
                    "critical": True
                },
                {
                    "type": "implementation",
                    "description": "Implement optimizations",
                    "confidence": 0.7,
                    "critical": False
                },
                {
                    "type": "validation",
                    "description": "Validate improvements",
                    "confidence": 0.9,
                    "critical": True
                }
            ])

        elif "build" in goal_lower or "create" in goal_lower:
            tasks.extend([
                {
                    "type": "planning",
                    "description": "Design system architecture",
                    "confidence": 0.8,
                    "critical": True
                },
                {
                    "type": "implementation",
                    "description": "Implement core functionality",
                    "confidence": 0.7,
                    "critical": True
                },
                {
                    "type": "testing",
                    "description": "Test implementation",
                    "confidence": 0.9,
                    "critical": True
                }
            ])

        elif "debug" in goal_lower or "fix" in goal_lower:
            tasks.extend([
                {
                    "type": "investigation",
                    "description": "Investigate issue",
                    "confidence": 0.8,
                    "critical": True
                },
                {
                    "type": "diagnosis",
                    "description": "Diagnose root cause",
                    "confidence": 0.7,
                    "critical": True
                },
                {
                    "type": "fix",
                    "description": "Implement fix",
                    "confidence": 0.8,
                    "critical": True
                },
                {
                    "type": "verification",
                    "description": "Verify fix works",
                    "confidence": 0.9,
                    "critical": True
                }
            ])

        else:
            # Generic decomposition
            tasks.append({
                "type": "generic",
                "description": goal,
                "confidence": 0.6,
                "critical": True
            })

        return tasks

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task

        Args:
            task: Task to execute

        Returns:
            Task result with status and outcomes
        """
        logger.info(f"🔧 Executing task: {task['description']}")

        # Evaluate decision autonomously
        decision = self.autonomous_decision.evaluate_decision(
            action=task["description"],
            context=task.get("context", {}),
            confidence=task.get("confidence", 0.5)
        )

        # If blocked, return blocked status
        if decision["decision"] == "block":
            logger.warning(f"🚫 Task blocked: {decision['reasoning']}")
            return {
                "task": task,
                "status": TaskStatus.BLOCKED.value,
                "reason": decision["reasoning"],
                "decision": decision
            }

        # If needs approval, request it
        if decision["decision"] == "ask_user":
            logger.info(f"❓ Task needs approval: {decision['reasoning']}")

            if self.on_need_approval:
                approved = await self.on_need_approval(task, decision)

                if not approved:
                    return {
                        "task": task,
                        "status": TaskStatus.BLOCKED.value,
                        "reason": "User declined approval",
                        "decision": decision
                    }
            else:
                # No approval callback, block task
                return {
                    "task": task,
                    "status": TaskStatus.BLOCKED.value,
                    "reason": "Approval required but no callback set",
                    "decision": decision
                }

        # Execute task
        try:
            # Simulate task execution (replace with actual execution)
            await asyncio.sleep(0.1)  # Simulate work

            # Record successful outcome
            self.autonomous_decision.record_outcome(
                action=task["description"],
                decision=decision,
                user_approved=True,
                outcome_success=True
            )

            result = {
                "task": task,
                "status": TaskStatus.COMPLETED.value,
                "decision": decision,
                "outcome": "Task completed successfully",
                "completed_at": datetime.now().isoformat()
            }

            logger.info(f"✅ Task completed: {task['description']}")

            if self.on_task_complete:
                await self.on_task_complete(result)

            return result

        except Exception as e:
            logger.error(f"❌ Task failed: {e}")

            # Record failed outcome
            self.autonomous_decision.record_outcome(
                action=task["description"],
                decision=decision,
                user_approved=True,
                outcome_success=False
            )

            return {
                "task": task,
                "status": TaskStatus.FAILED.value,
                "error": str(e),
                "decision": decision,
                "critical": task.get("critical", False)
            }

    async def _request_user_input(
        self,
        task: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Request user input for blocked task"""
        logger.info(f"❓ Requesting user input for: {task['description']}")

        # In production, this would trigger a UI prompt or callback
        # For now, return None (user declined)
        return None

    def _report_progress(self, message: str):
        """Report progress to user"""
        if self.on_progress_update:
            self.on_progress_update(message)

        logger.info(f"📊 Progress: {message}")

    def _generate_outcomes(self) -> List[str]:
        """Generate list of outcomes from completed tasks"""
        outcomes = []

        for task_result in self.completed_tasks:
            outcomes.append(task_result["task"]["description"])

        return outcomes

    def pause(self):
        """Pause execution"""
        self.pause_requested = True
        logger.info("⏸️ Pause requested")

    def resume(self):
        """Resume execution"""
        self.pause_requested = False
        logger.info("▶️ Execution resumed")

    def get_status(self) -> Dict[str, Any]:
        """Get current execution status"""
        return {
            "is_executing": self.is_executing,
            "current_goal": self.current_goal,
            "tasks_remaining": len(self.task_queue),
            "tasks_completed": len(self.completed_tasks),
            "tasks_failed": len(self.failed_tasks),
            "autonomy_level": self.autonomous_decision.autonomy_level
        }


# Test
if __name__ == "__main__":
    from autonomous_decision import AutonomousDecision

    async def test_executor():
        ad = AutonomousDecision()
        executor = AutonomousExecutor(ad)

        # Set up callbacks
        async def on_task_complete(result):
            print(f"✅ Task completed: {result['task']['description']}")

        async def on_need_approval(task, decision):
            print(f"❓ Approval needed: {task['description']}")
            print(f"   Risk: {decision['risk_score']:.1f}")
            print(f"   Reasoning: {decision['reasoning']}")
            return True  # Auto-approve for test

        def on_progress(message):
            print(f"📊 {message}")

        executor.on_task_complete = on_task_complete
        executor.on_need_approval = on_need_approval
        executor.on_progress_update = on_progress

        # Test goal execution
        result = await executor.execute_goal(
            goal="Optimize JARVIS performance",
            context={"system": "jarvis_v9"}
        )

        print("\n" + "="*50)
        print("EXECUTION RESULT")
        print("="*50)
        print(json.dumps(result, indent=2))

        print("\n" + "="*50)
        print("AUTONOMY REPORT")
        print("="*50)
        print(json.dumps(ad.get_autonomy_report(), indent=2))

    asyncio.run(test_executor())
