# ==========================================================
# JARVIS v9.0 - Enhanced Autonomy System
# Main integration point for all autonomy features
# ==========================================================

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Core autonomy components
from core.autonomous_decision import AutonomousDecision
from core.autonomous_executor import AutonomousExecutor
from core.goal_manager import GoalManager, GoalPriority
from core.self_monitor import SelfMonitor
from core.proactive_agent import ProactiveAgent
from core.hyper_automation import HyperAutomation
from core.skill_loader import SkillLoader
from core.self_evolving_architecture import SEAController

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedAutonomySystem:
    """
    Enhanced Autonomy System for JARVIS v9.0

    Integrates:
    - Autonomous decision making
    - Goal management across sessions
    - Self-monitoring and performance tracking
    - Proactive suggestions and anticipation
    - Task execution with minimal user input
    - Self-Evolving Architecture (SEA) for continuous optimization
    """

    def __init__(self, skill_loader: SkillLoader = None):
        logger.info("🚀 Initializing Enhanced Autonomy System...")

        # Initialize core components
        self.autonomous_decision = AutonomousDecision()
        self.goal_manager = GoalManager()
        self.self_monitor = SelfMonitor()
        self.hyper_automation = HyperAutomation()

        # Initialize executor
        self.executor = AutonomousExecutor(
            self.autonomous_decision,
            skill_loader
        )

        # Initialize Self-Evolving Architecture (SEA) System
        self.sea_controller = SEAController(self)
        logger.info("🧬 Self-Evolving Architecture (SEA) System integrated")

        # Initialize swarm coordinator for agent team management
        from core.swarm_coordinator import SwarmCoordinator
        self.swarm_coordinator = SwarmCoordinator()

        # Initialize proactive agent
        self.proactive_agent = ProactiveAgent(
            self.hyper_automation,
            self.self_monitor,
            self.goal_manager
        )

        # Set up executor callbacks
        self.executor.on_task_complete = self._on_task_complete
        self.executor.on_need_approval = self._on_need_approval
        self.executor.on_progress_update = self._on_progress_update

        # System state
        self.current_session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.is_running = False

        logger.info("✅ Enhanced Autonomy System initialized")

    async def execute_goal(
        self,
        goal_description: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a high-level goal autonomously

        Args:
            goal_description: Goal description
            priority: Goal priority
            context: Additional context

        Returns:
            Execution result
        """
        logger.info(f"🎯 Starting goal execution: {goal_description}")

        # Create goal
        goal_id = self.goal_manager.create_goal(
            goal_description,
            priority=priority,
            context=context
        )

        # Record start
        start_time = datetime.now()

        try:
            # Execute goal
            result = await self.executor.execute_goal(
                goal_description,
                context=context
            )

            # Update goal progress
            self.goal_manager.update_progress(
                goal_id,
                tasks_completed=result["completed_tasks"],
                tasks_total=result["completed_tasks"] + result["failed_tasks"]
            )

            # Record outcomes
            for outcome in result.get("outcomes", []):
                self.goal_manager.update_progress(
                    goal_id,
                    outcome=outcome
                )

            # Complete goal
            if result["success"]:
                self.goal_manager.complete_goal(goal_id, success=True)
            else:
                self.goal_manager.complete_goal(goal_id, success=False)

            # Record monitoring data
            duration = (datetime.now() - start_time).total_seconds()
            self.self_monitor.record_action(
                action=goal_description,
                action_type="goal_execution",
                success=result["success"],
                duration=duration,
                context={"goal_id": goal_id}
            )

            # Log task for automation detection
            self.hyper_automation.log_task(goal_description, context)

            logger.info(f"✅ Goal execution complete: {goal_id}")

            return {
                "success": result["success"],
                "goal_id": goal_id,
                "result": result
            }

        except Exception as e:
            logger.error(f"❌ Goal execution failed: {e}")

            # Mark goal as failed
            self.goal_manager.complete_goal(goal_id, success=False)

            # Record failure
            self.self_monitor.record_action(
                action=goal_description,
                action_type="goal_execution",
                success=False,
                duration=(datetime.now() - start_time).total_seconds(),
                error=str(e)
            )

            return {
                "success": False,
                "goal_id": goal_id,
                "error": str(e)
            }

    async def resume_session(self) -> Dict[str, Any]:
        """
        Resume work from previous session

        Returns:
            Resume status and next actions
        """
        logger.info("🔄 Resuming from previous session...")

        # Get active goals
        active_goals = self.goal_manager.get_active_goals()

        if not active_goals:
            logger.info("No active goals to resume")
            return {
                "resumed": False,
                "message": "No active goals found"
            }

        # Get next goal to work on
        next_goal = self.goal_manager.get_next_goal()

        if next_goal:
            logger.info(f"📋 Next goal: {next_goal['description']}")

            return {
                "resumed": True,
                "next_goal": next_goal,
                "active_goals_count": len(active_goals),
                "message": f"Ready to continue: {next_goal['description']}"
            }

        return {
            "resumed": False,
            "message": "No goals ready to resume"
        }

    async def get_proactive_suggestions(self) -> Dict[str, Any]:
        """
        Get proactive suggestions

        Returns:
            Suggestions and system status
        """
        logger.info("🔮 Generating proactive suggestions...")

        suggestions = await self.proactive_agent.analyze_and_suggest()

        # Get anticipated next action
        next_action = self.proactive_agent.anticipate_next_action({})

        return {
            "suggestions": suggestions,
            "anticipated_next_action": next_action,
            "suggestion_count": len(suggestions)
        }

    async def execute_suggestion(self, suggestion_id: int) -> Dict[str, Any]:
        """Execute a proactive suggestion"""
        return await self.proactive_agent.execute_suggestion(suggestion_id)

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status

        Returns:
            System status including all components
        """
        # Get performance report
        performance_report = self.self_monitor.generate_report(time_window_hours=24)

        # Get autonomy report
        autonomy_report = self.autonomous_decision.get_autonomy_report()

        # Get goal stats
        goal_stats = self.goal_manager.get_stats()

        # Get automation stats
        automation_stats = self.hyper_automation.get_stats()

        # Get proactive agent stats
        proactive_stats = self.proactive_agent.get_stats()

        return {
            "session_id": self.current_session_id,
            "is_running": self.is_running,
            "performance": {
                "health_score": performance_report["health_score"],
                "success_rate": performance_report["summary"]["success_rate"],
                "avg_response_time": performance_report["summary"]["avg_response_time"]
            },
            "autonomy": {
                "level": autonomy_report["autonomy_level"],
                "auto_approved_rate": autonomy_report.get("auto_approved_rate", 0),
                "auto_success_rate": autonomy_report.get("auto_success_rate", 0)
            },
            "goals": goal_stats,
            "automation": automation_stats,
            "proactive": proactive_stats
        }

    async def _on_task_complete(self, result: Dict[str, Any]):
        """Callback when task completes"""
        logger.info(f"✅ Task completed: {result['task']['description']}")

        # Record in monitoring
        self.self_monitor.record_action(
            action=result['task']['description'],
            action_type=result['task'].get('type', 'task'),
            success=True,
            context=result.get('context', {})
        )

    async def _on_need_approval(self, task: Dict[str, Any], decision: Dict[str, Any]) -> bool:
        """Callback when task needs approval"""
        logger.info(f"❓ Task needs approval: {task['description']}")
        logger.info(f"   Risk: {decision['risk_score']:.1f}")
        logger.info(f"   Reasoning: {decision['reasoning']}")

        # In production, this would prompt the user
        # For now, auto-approve medium-risk tasks
        return decision['risk_score'] < 6.0

    def _on_progress_update(self, message: str):
        """Callback for progress updates"""
        logger.info(f"📊 Progress: {message}")

    async def execute_with_agent_team(
        self,
        task_description: str,
        team_name: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a task using a coordinated team of agents

        Args:
            task_description: Description of the task to execute
            team_name: Name of the agent team to use
            context: Additional context for the task

        Returns:
            Execution result
        """
        logger.info(f"🎯 Executing task with agent team '{team_name}': {task_description}")

        # Initialize agent team if not already done
        if not self.swarm_coordinator.agent_teams:
            self._initialize_agent_teams()

        # Execute using team
        result = await self.swarm_coordinator.execute_team(
            team_name=team_name,
            task=task_description,
            initial_state=context or {},
            max_iterations=15  # Allow more iterations for complex tasks
        )

        # Record execution in monitoring
        self.self_monitor.record_action(
            action=task_description,
            action_type="agent_team_execution",
            success=result.get("completed", False),
            context={"team_name": team_name, "result_keys": list(result.keys())}
        )

        logger.info(f"✅ Agent team execution complete: {team_name}")

        return {
            "success": result.get("completed", False),
            "team_name": team_name,
            "result": result,
            "iterations": result.get("total_iterations", 0)
        }

    def _initialize_agent_teams(self):
        """Initialize default agent teams based on Claude Code patterns"""
        from core.swarm_coordinator import PlannerAgent, ExecutorAgent, VerifierAgent

        # Register default agents if not already registered
        if "planner" not in self.swarm_coordinator.agents:
            self.swarm_coordinator.register_agent(PlannerAgent())
        if "executor" not in self.swarm_coordinator.agents:
            self.swarm_coordinator.register_agent(ExecutorAgent())
        if "verifier" not in self.swarm_coordinator.agents:
            self.swarm_coordinator.register_agent(VerifierAgent())

        # Create default teams
        self.swarm_coordinator.create_agent_team(
            "standard_workflow",
            ["planner", "executor", "verifier"]
        )

        # Create advanced team with additional agents
        self.swarm_coordinator.create_agent_team(
            "advanced_workflow",
            ["planner", "executor", "verifier"]
        )

        logger.info("👥 Default agent teams initialized")


# CLI Interface
async def main():
    """Main CLI interface for testing"""
    import json

    # Initialize system
    system = EnhancedAutonomySystem()

    print("\n" + "="*60)
    print("JARVIS v9.0 - Enhanced Autonomy System")
    print("="*60)

    # Resume from previous session
    resume_result = await system.resume_session()
    print(f"\nSession Resume: {resume_result['message']}")

    # Get system status
    status = system.get_system_status()
    print("\n" + "="*60)
    print("SYSTEM STATUS")
    print("="*60)
    print(json.dumps(status, indent=2))

    # Get proactive suggestions
    suggestions_result = await system.get_proactive_suggestions()
    print("\n" + "="*60)
    print(f"PROACTIVE SUGGESTIONS ({suggestions_result['suggestion_count']})")
    print("="*60)
    for i, suggestion in enumerate(suggestions_result['suggestions']):
        print(f"\n{i+1}. [{suggestion['priority'].upper()}] {suggestion['title']}")
        print(f"   {suggestion['description']}")

    if suggestions_result['anticipated_next_action']:
        print(f"\nAnticipated Next: {suggestions_result['anticipated_next_action']}")

    # Test goal execution
    print("\n" + "="*60)
    print("TEST: Execute Goal")
    print("="*60)

    result = await system.execute_goal(
        "Optimize JARVIS performance",
        priority=GoalPriority.HIGH,
        context={"system": "jarvis_v9"}
    )

    print(f"\nGoal Execution Result:")
    print(json.dumps(result, indent=2))

    # Final status
    final_status = system.get_system_status()
    print("\n" + "="*60)
    print("FINAL STATUS")
    print("="*60)
    print(f"Health Score: {final_status['performance']['health_score']:.1f}/100")
    print(f"Autonomy Level: {final_status['autonomy']['level']:.1%}")
    print(f"Active Goals: {final_status['goals']['active']}")
    print(f"Completed Goals: {final_status['goals']['completed']}")


if __name__ == "__main__":
    asyncio.run(main())
