# ==========================================================
# JARVIS v9.0 - Persistent Goal Manager
# Maintains goals across sessions using auto-memory
# Tracks progress and resumes work automatically
# ==========================================================

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class GoalStatus(Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class GoalPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class GoalManager:
    """
    Persistent goal management system
    - Store goals across sessions
    - Track progress
    - Resume work automatically
    - Maintain context
    """

    def __init__(self, storage_path: str = None):
        # Default to Claude auto-memory location
        if storage_path is None:
            storage_path = str(Path.home() / ".claude" / "projects" / "C--Users-AK" / "memory" / "goals.json")

        self.storage_path = storage_path
        self.goals = {}

        # Load existing goals
        self._load_goals()

        logger.info(f"🎯 Goal Manager initialized with {len(self.goals)} goals")

    def create_goal(
        self,
        description: str,
        priority: GoalPriority = GoalPriority.MEDIUM,
        context: Dict[str, Any] = None,
        parent_goal_id: str = None
    ) -> str:
        """
        Create a new goal

        Args:
            description: Goal description
            priority: Goal priority
            context: Additional context
            parent_goal_id: Parent goal ID (for sub-goals)

        Returns:
            Goal ID
        """
        goal_id = f"goal_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.goals)}"

        goal = {
            "id": goal_id,
            "description": description,
            "priority": priority.value,
            "status": GoalStatus.ACTIVE.value,
            "context": context or {},
            "parent_goal_id": parent_goal_id,
            "sub_goals": [],
            "progress": 0.0,
            "tasks_completed": 0,
            "tasks_total": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "completed_at": None,
            "outcomes": [],
            "notes": []
        }

        self.goals[goal_id] = goal

        # If this is a sub-goal, add to parent
        if parent_goal_id and parent_goal_id in self.goals:
            self.goals[parent_goal_id]["sub_goals"].append(goal_id)

        self._save_goals()

        logger.info(f"🎯 Goal created: {goal_id} - {description}")

        return goal_id

    def update_progress(
        self,
        goal_id: str,
        tasks_completed: int = None,
        tasks_total: int = None,
        progress: float = None,
        outcome: str = None
    ):
        """
        Update goal progress

        Args:
            goal_id: Goal ID
            tasks_completed: Number of tasks completed
            tasks_total: Total number of tasks
            progress: Progress percentage (0-1)
            outcome: Outcome description
        """
        if goal_id not in self.goals:
            logger.error(f"❌ Goal not found: {goal_id}")
            return

        goal = self.goals[goal_id]

        if tasks_completed is not None:
            goal["tasks_completed"] = tasks_completed

        if tasks_total is not None:
            goal["tasks_total"] = tasks_total

        if progress is not None:
            goal["progress"] = progress
        elif goal["tasks_total"] > 0:
            goal["progress"] = goal["tasks_completed"] / goal["tasks_total"]

        if outcome:
            goal["outcomes"].append({
                "description": outcome,
                "timestamp": datetime.now().isoformat()
            })

        goal["updated_at"] = datetime.now().isoformat()

        # Check if goal is complete
        if goal["progress"] >= 1.0:
            self.complete_goal(goal_id)

        self._save_goals()

        logger.info(f"📊 Goal progress updated: {goal_id} - {goal['progress']:.1%}")

    def complete_goal(self, goal_id: str, success: bool = True):
        """
        Mark goal as completed

        Args:
            goal_id: Goal ID
            success: Whether goal was successful
        """
        if goal_id not in self.goals:
            logger.error(f"❌ Goal not found: {goal_id}")
            return

        goal = self.goals[goal_id]
        goal["status"] = GoalStatus.COMPLETED.value if success else GoalStatus.FAILED.value
        goal["completed_at"] = datetime.now().isoformat()
        goal["updated_at"] = datetime.now().isoformat()
        goal["progress"] = 1.0

        self._save_goals()

        logger.info(f"✅ Goal completed: {goal_id} - {goal['description']}")

    def pause_goal(self, goal_id: str):
        """Pause a goal"""
        if goal_id not in self.goals:
            logger.error(f"❌ Goal not found: {goal_id}")
            return

        self.goals[goal_id]["status"] = GoalStatus.PAUSED.value
        self.goals[goal_id]["updated_at"] = datetime.now().isoformat()

        self._save_goals()

        logger.info(f"⏸️ Goal paused: {goal_id}")

    def resume_goal(self, goal_id: str):
        """Resume a paused goal"""
        if goal_id not in self.goals:
            logger.error(f"❌ Goal not found: {goal_id}")
            return

        self.goals[goal_id]["status"] = GoalStatus.ACTIVE.value
        self.goals[goal_id]["updated_at"] = datetime.now().isoformat()

        self._save_goals()

        logger.info(f"▶️ Goal resumed: {goal_id}")

    def cancel_goal(self, goal_id: str):
        """Cancel a goal"""
        if goal_id not in self.goals:
            logger.error(f"❌ Goal not found: {goal_id}")
            return

        self.goals[goal_id]["status"] = GoalStatus.CANCELLED.value
        self.goals[goal_id]["updated_at"] = datetime.now().isoformat()

        self._save_goals()

        logger.info(f"❌ Goal cancelled: {goal_id}")

    def add_note(self, goal_id: str, note: str):
        """Add a note to a goal"""
        if goal_id not in self.goals:
            logger.error(f"❌ Goal not found: {goal_id}")
            return

        self.goals[goal_id]["notes"].append({
            "text": note,
            "timestamp": datetime.now().isoformat()
        })

        self._save_goals()

        logger.info(f"📝 Note added to goal: {goal_id}")

    def get_active_goals(self) -> List[Dict[str, Any]]:
        """Get all active goals"""
        return [
            goal for goal in self.goals.values()
            if goal["status"] == GoalStatus.ACTIVE.value
        ]

    def get_goals_by_priority(self, priority: GoalPriority) -> List[Dict[str, Any]]:
        """Get goals by priority"""
        return [
            goal for goal in self.goals.values()
            if goal["priority"] == priority.value
        ]

    def get_next_goal(self) -> Optional[Dict[str, Any]]:
        """
        Get next goal to work on
        Prioritizes by: priority > progress > created_at
        """
        active_goals = self.get_active_goals()

        if not active_goals:
            return None

        # Sort by priority (descending), then progress (ascending), then created_at
        sorted_goals = sorted(
            active_goals,
            key=lambda g: (-g["priority"], g["progress"], g["created_at"])
        )

        return sorted_goals[0] if sorted_goals else None

    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """Get goal by ID"""
        return self.goals.get(goal_id)

    def get_stats(self) -> Dict[str, Any]:
        """Get goal statistics"""
        total = len(self.goals)
        active = len([g for g in self.goals.values() if g["status"] == GoalStatus.ACTIVE.value])
        completed = len([g for g in self.goals.values() if g["status"] == GoalStatus.COMPLETED.value])
        failed = len([g for g in self.goals.values() if g["status"] == GoalStatus.FAILED.value])
        paused = len([g for g in self.goals.values() if g["status"] == GoalStatus.PAUSED.value])

        return {
            "total_goals": total,
            "active": active,
            "completed": completed,
            "failed": failed,
            "paused": paused,
            "completion_rate": completed / total if total > 0 else 0.0
        }

    def _save_goals(self):
        """Save goals to storage"""
        try:
            # Ensure directory exists
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

            with open(self.storage_path, 'w') as f:
                json.dump(self.goals, f, indent=2)

            logger.debug(f"💾 Goals saved to {self.storage_path}")

        except Exception as e:
            logger.error(f"❌ Failed to save goals: {e}")

    def _load_goals(self):
        """Load goals from storage"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    self.goals = json.load(f)

                logger.info(f"📂 Loaded {len(self.goals)} goals from {self.storage_path}")
            else:
                logger.info("📂 No existing goals found, starting fresh")

        except Exception as e:
            logger.error(f"❌ Failed to load goals: {e}")
            self.goals = {}


# Test
if __name__ == "__main__":
    gm = GoalManager("test_goals.json")

    # Create test goals
    goal1 = gm.create_goal(
        "Optimize JARVIS performance",
        priority=GoalPriority.HIGH,
        context={"system": "jarvis_v9"}
    )

    goal2 = gm.create_goal(
        "Build autonomous agent system",
        priority=GoalPriority.CRITICAL,
        context={"deadline": "2026-03-15"}
    )

    goal3 = gm.create_goal(
        "Implement self-monitoring",
        priority=GoalPriority.MEDIUM,
        parent_goal_id=goal2
    )

    # Update progress
    gm.update_progress(goal1, tasks_completed=3, tasks_total=10)
    gm.update_progress(goal2, tasks_completed=1, tasks_total=5)
    gm.update_progress(goal3, progress=0.5)

    # Add notes
    gm.add_note(goal1, "Started performance profiling")
    gm.add_note(goal2, "Designed system architecture")

    print("\n" + "="*50)
    print("GOAL MANAGER STATS")
    print("="*50)
    print(json.dumps(gm.get_stats(), indent=2))

    print("\n" + "="*50)
    print("ACTIVE GOALS")
    print("="*50)
    for goal in gm.get_active_goals():
        print(f"\n{goal['id']}")
        print(f"  Description: {goal['description']}")
        print(f"  Priority: {goal['priority']}")
        print(f"  Progress: {goal['progress']:.1%}")
        print(f"  Tasks: {goal['tasks_completed']}/{goal['tasks_total']}")

    print("\n" + "="*50)
    print("NEXT GOAL TO WORK ON")
    print("="*50)
    next_goal = gm.get_next_goal()
    if next_goal:
        print(f"ID: {next_goal['id']}")
        print(f"Description: {next_goal['description']}")
        print(f"Priority: {next_goal['priority']}")
        print(f"Progress: {next_goal['progress']:.1%}")
