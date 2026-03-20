# ==========================================================
# JARVIS v9.0 - Proactive Agent
# Anticipates needs, suggests improvements, takes initiative
# Uses HyperAutomation for pattern detection
# ==========================================================

import logging
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class ProactiveAgent:
    """
    Proactive intelligence system
    - Anticipates user needs
    - Suggests improvements
    - Takes initiative within constraints
    - Learns from interactions
    """

    def __init__(self, hyper_automation, self_monitor, goal_manager):
        self.hyper_automation = hyper_automation
        self.self_monitor = self_monitor
        self.goal_manager = goal_manager

        # Proactive suggestions
        self.pending_suggestions = []
        self.accepted_suggestions = []
        self.rejected_suggestions = []

        # Learning
        self.user_preferences = {}
        self.suggestion_patterns = defaultdict(int)

        logger.info("🔮 Proactive Agent initialized")

    async def analyze_and_suggest(self) -> List[Dict[str, Any]]:
        """
        Analyze current state and generate proactive suggestions

        Returns:
            List of suggestions
        """
        suggestions = []

        # 1. Check for automation opportunities
        automation_suggestions = self.hyper_automation.get_suggestions(status="pending")
        for auto_sugg in automation_suggestions:
            suggestions.append({
                "type": "automation",
                "priority": "medium",
                "title": f"Automate: {auto_sugg['task'][:50]}",
                "description": f"Detected {auto_sugg['pattern_type']} pattern. Suggest creating {auto_sugg['automation_type']}",
                "action": "approve_automation",
                "action_params": {"suggestion_id": auto_sugg["id"]},
                "source": "hyper_automation"
            })

        # 2. Check for performance issues
        weaknesses = self.self_monitor.identify_weaknesses()
        if weaknesses:
            for weakness in weaknesses:
                suggestions.append({
                    "type": "performance",
                    "priority": "high",
                    "title": "Performance Issue Detected",
                    "description": weakness,
                    "action": "investigate_weakness",
                    "action_params": {"weakness": weakness},
                    "source": "self_monitor"
                })

        # 3. Check for stalled goals
        active_goals = self.goal_manager.get_active_goals()
        for goal in active_goals:
            # Check if goal hasn't been updated in 24 hours
            updated_at = datetime.fromisoformat(goal["updated_at"])
            if datetime.now() - updated_at > timedelta(hours=24):
                suggestions.append({
                    "type": "goal_reminder",
                    "priority": "low",
                    "title": f"Goal Stalled: {goal['description'][:50]}",
                    "description": f"Goal hasn't been updated in {(datetime.now() - updated_at).days} days. Progress: {goal['progress']:.1%}",
                    "action": "resume_goal",
                    "action_params": {"goal_id": goal["id"]},
                    "source": "goal_manager"
                })

        # 4. Suggest improvements based on monitoring
        improvement_suggestions = self.self_monitor.suggest_improvements()
        for imp_sugg in improvement_suggestions:
            suggestions.append({
                "type": "improvement",
                "priority": imp_sugg["priority"],
                "title": imp_sugg["suggestion"],
                "description": imp_sugg["weakness"],
                "action": "implement_improvement",
                "action_params": {"actions": imp_sugg["actions"]},
                "source": "self_monitor"
            })

        # 5. Anticipate next steps for active goals
        next_goal = self.goal_manager.get_next_goal()
        if next_goal and next_goal["progress"] < 1.0:
            suggestions.append({
                "type": "goal_continuation",
                "priority": "medium",
                "title": f"Continue: {next_goal['description'][:50]}",
                "description": f"Resume work on goal (Progress: {next_goal['progress']:.1%})",
                "action": "continue_goal",
                "action_params": {"goal_id": next_goal["id"]},
                "source": "goal_manager"
            })

        # Filter based on user preferences
        suggestions = self._filter_by_preferences(suggestions)

        # Store pending suggestions
        self.pending_suggestions.extend(suggestions)

        logger.info(f"🔮 Generated {len(suggestions)} proactive suggestions")

        return suggestions

    def _filter_by_preferences(self, suggestions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter suggestions based on learned user preferences"""
        filtered = []

        for suggestion in suggestions:
            # Check if user has rejected this type before
            rejection_count = self.suggestion_patterns.get(f"reject_{suggestion['type']}", 0)
            acceptance_count = self.suggestion_patterns.get(f"accept_{suggestion['type']}", 0)

            # If user consistently rejects this type, skip it
            if rejection_count > 3 and acceptance_count == 0:
                logger.debug(f"Skipping suggestion type '{suggestion['type']}' (user preference)")
                continue

            filtered.append(suggestion)

        return filtered

    async def execute_suggestion(self, suggestion_id: int) -> Dict[str, Any]:
        """
        Execute a proactive suggestion

        Args:
            suggestion_id: Index of suggestion to execute

        Returns:
            Execution result
        """
        if suggestion_id >= len(self.pending_suggestions):
            return {"success": False, "error": "Invalid suggestion ID"}

        suggestion = self.pending_suggestions[suggestion_id]

        logger.info(f"🚀 Executing suggestion: {suggestion['title']}")

        try:
            # Execute based on action type
            if suggestion["action"] == "approve_automation":
                result = self.hyper_automation.approve_automation(
                    suggestion["action_params"]["suggestion_id"]
                )

            elif suggestion["action"] == "resume_goal":
                goal_id = suggestion["action_params"]["goal_id"]
                self.goal_manager.resume_goal(goal_id)
                result = {"success": True, "message": f"Goal {goal_id} resumed"}

            elif suggestion["action"] == "continue_goal":
                goal_id = suggestion["action_params"]["goal_id"]
                result = {"success": True, "message": f"Continuing goal {goal_id}"}

            elif suggestion["action"] == "implement_improvement":
                actions = suggestion["action_params"]["actions"]
                result = {"success": True, "message": f"Improvement plan created with {len(actions)} actions"}

            elif suggestion["action"] == "investigate_weakness":
                weakness = suggestion["action_params"]["weakness"]
                result = {"success": True, "message": f"Investigation started for: {weakness}"}

            else:
                result = {"success": False, "error": "Unknown action type"}

            # Record outcome
            if result.get("success"):
                self.accepted_suggestions.append(suggestion)
                self.suggestion_patterns[f"accept_{suggestion['type']}"] += 1
                logger.info(f"✅ Suggestion executed successfully")
            else:
                logger.error(f"❌ Suggestion execution failed: {result.get('error')}")

            return result

        except Exception as e:
            logger.error(f"❌ Suggestion execution error: {e}")
            return {"success": False, "error": str(e)}

    def reject_suggestion(self, suggestion_id: int, reason: str = None):
        """
        Reject a suggestion and learn from it

        Args:
            suggestion_id: Index of suggestion to reject
            reason: Optional reason for rejection
        """
        if suggestion_id >= len(self.pending_suggestions):
            return

        suggestion = self.pending_suggestions[suggestion_id]
        suggestion["rejection_reason"] = reason

        self.rejected_suggestions.append(suggestion)
        self.suggestion_patterns[f"reject_{suggestion['type']}"] += 1

        logger.info(f"❌ Suggestion rejected: {suggestion['title']}")

        # Learn from rejection
        if reason:
            self._learn_from_rejection(suggestion, reason)

    def _learn_from_rejection(self, suggestion: Dict[str, Any], reason: str):
        """Learn from rejected suggestions"""
        reason_lower = reason.lower()

        # Update user preferences
        if "not now" in reason_lower or "later" in reason_lower:
            # User wants this type of suggestion, just not now
            pass
        elif "never" in reason_lower or "don't" in reason_lower:
            # User doesn't want this type of suggestion
            self.user_preferences[f"disable_{suggestion['type']}"] = True
            logger.info(f"📝 Learned: User doesn't want '{suggestion['type']}' suggestions")

    def anticipate_next_action(self, current_context: Dict[str, Any]) -> Optional[str]:
        """
        Anticipate what the user might want to do next

        Args:
            current_context: Current context (recent actions, goals, etc.)

        Returns:
            Anticipated action description
        """
        # Check active goals
        next_goal = self.goal_manager.get_next_goal()
        if next_goal:
            return f"Continue working on: {next_goal['description']}"

        # Check for patterns in recent actions
        recent_patterns = self.hyper_automation.get_suggestions(status="pending")
        if recent_patterns:
            return f"Automate recurring task: {recent_patterns[0]['task']}"

        # Check for performance issues
        weaknesses = self.self_monitor.identify_weaknesses()
        if weaknesses:
            return f"Address performance issue: {weaknesses[0]}"

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get proactive agent statistics"""
        return {
            "pending_suggestions": len(self.pending_suggestions),
            "accepted_suggestions": len(self.accepted_suggestions),
            "rejected_suggestions": len(self.rejected_suggestions),
            "acceptance_rate": len(self.accepted_suggestions) / max(1, len(self.accepted_suggestions) + len(self.rejected_suggestions)),
            "suggestion_patterns": dict(self.suggestion_patterns),
            "user_preferences": self.user_preferences
        }


# Test
if __name__ == "__main__":
    from hyper_automation import HyperAutomation
    from self_monitor import SelfMonitor
    from goal_manager import GoalManager, GoalPriority

    async def test_proactive_agent():
        # Initialize dependencies
        ha = HyperAutomation()
        monitor = SelfMonitor("test_monitor.json")
        gm = GoalManager("test_goals.json")

        # Create test data
        ha.log_task("Send daily report")
        ha.log_task("Send daily report")
        ha.log_task("Send daily report")

        monitor.record_action("Test action", "test", False, 0.5, error="Test error")
        monitor.record_action("Test action", "test", False, 0.5, error="Test error")

        goal_id = gm.create_goal("Test goal", priority=GoalPriority.HIGH)
        gm.update_progress(goal_id, tasks_completed=1, tasks_total=10)

        # Initialize proactive agent
        agent = ProactiveAgent(ha, monitor, gm)

        # Generate suggestions
        suggestions = await agent.analyze_and_suggest()

        print("\n" + "="*50)
        print("PROACTIVE SUGGESTIONS")
        print("="*50)
        for i, suggestion in enumerate(suggestions):
            print(f"\n{i+1}. [{suggestion['priority'].upper()}] {suggestion['title']}")
            print(f"   {suggestion['description']}")
            print(f"   Source: {suggestion['source']}")

        # Test anticipation
        print("\n" + "="*50)
        print("ANTICIPATED NEXT ACTION")
        print("="*50)
        next_action = agent.anticipate_next_action({})
        if next_action:
            print(f"🔮 {next_action}")

        print("\n" + "="*50)
        print("PROACTIVE AGENT STATS")
        print("="*50)
        import json
        print(json.dumps(agent.get_stats(), indent=2))

    asyncio.run(test_proactive_agent())
