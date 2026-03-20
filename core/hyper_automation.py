# ==========================================================
# JARVIS v9.0 - Hyper-Automation Engine
# Identify repetitive tasks and auto-create agents/workflows
# Proactively suggest automations
# ==========================================================

import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import json
import re

logger = logging.getLogger(__name__)


class HyperAutomation:
    """
    Hyper-automation engine for JARVIS v9.0
    - Monitor user patterns
    - Detect repetitive tasks
    - Auto-generate FTEs (Fine-Tuned Experts)
    - Suggest automations proactively
    """

    def __init__(self):
        self.task_history = []  # List of {task, timestamp, context}
        self.patterns = {}  # Detected patterns
        self.automations = {}  # Active automations
        self.suggestions = []  # Pending suggestions

        # Pattern detection thresholds
        self.min_occurrences = 3  # Minimum times to detect pattern
        self.time_window_days = 7  # Look back window

        logger.info("⚡ Hyper-Automation Engine initialized")

    def log_task(self, task: str, context: Dict = None):
        """
        Log a task for pattern detection

        Args:
            task: Task description
            context: Additional context (user, time, etc.)
        """
        entry = {
            "task": task,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }

        self.task_history.append(entry)
        logger.info(f"📝 Task logged: {task[:50]}...")

        # Trigger pattern detection
        self._detect_patterns()

    def _detect_patterns(self):
        """Detect repetitive patterns in task history"""
        if len(self.task_history) < self.min_occurrences:
            return

        # Get recent tasks (within time window)
        cutoff = datetime.now() - timedelta(days=self.time_window_days)
        recent_tasks = [
            t for t in self.task_history
            if datetime.fromisoformat(t["timestamp"]) > cutoff
        ]

        if len(recent_tasks) < self.min_occurrences:
            return

        # Pattern 1: Exact task repetition
        self._detect_exact_repetition(recent_tasks)

        # Pattern 2: Similar tasks (fuzzy matching)
        self._detect_similar_tasks(recent_tasks)

        # Pattern 3: Temporal patterns (daily, weekly)
        self._detect_temporal_patterns(recent_tasks)

        # Pattern 4: Sequential patterns (task chains)
        self._detect_sequential_patterns(recent_tasks)

    def _detect_exact_repetition(self, tasks: List[Dict]):
        """Detect exact task repetition"""
        task_counts = Counter([t["task"] for t in tasks])

        for task, count in task_counts.items():
            if count >= self.min_occurrences:
                pattern_id = f"exact_{hash(task)}"

                if pattern_id not in self.patterns:
                    self.patterns[pattern_id] = {
                        "type": "exact_repetition",
                        "task": task,
                        "count": count,
                        "detected_at": datetime.now().isoformat()
                    }

                    # Generate automation suggestion
                    self._suggest_automation(pattern_id, task, "exact_repetition")

                    logger.info(f"🔍 Pattern detected: '{task}' repeated {count} times")

    def _detect_similar_tasks(self, tasks: List[Dict]):
        """Detect similar tasks using fuzzy matching"""
        # Group tasks by similarity
        task_groups = defaultdict(list)

        for task_entry in tasks:
            task = task_entry["task"]
            # Extract key words (simple approach)
            key_words = set(re.findall(r'\b\w{4,}\b', task.lower()))

            # Find similar group
            found_group = False
            for group_key, group_tasks in task_groups.items():
                group_words = set(re.findall(r'\b\w{4,}\b', group_key.lower()))
                # If >50% word overlap, consider similar
                overlap = len(key_words & group_words) / max(len(key_words), len(group_words), 1)
                if overlap > 0.5:
                    group_tasks.append(task)
                    found_group = True
                    break

            if not found_group:
                task_groups[task] = [task]

        # Check for groups with enough occurrences
        for group_key, group_tasks in task_groups.items():
            if len(group_tasks) >= self.min_occurrences:
                pattern_id = f"similar_{hash(group_key)}"

                if pattern_id not in self.patterns:
                    self.patterns[pattern_id] = {
                        "type": "similar_tasks",
                        "template": group_key,
                        "examples": group_tasks[:5],
                        "count": len(group_tasks),
                        "detected_at": datetime.now().isoformat()
                    }

                    self._suggest_automation(pattern_id, group_key, "similar_tasks")

                    logger.info(f"🔍 Similar tasks pattern: {len(group_tasks)} variations of '{group_key[:50]}'")

    def _detect_temporal_patterns(self, tasks: List[Dict]):
        """Detect temporal patterns (daily, weekly, monthly)"""
        # Group tasks by day of week and hour
        temporal_groups = defaultdict(list)

        for task_entry in tasks:
            task = task_entry["task"]
            timestamp = datetime.fromisoformat(task_entry["timestamp"])
            day_of_week = timestamp.strftime("%A")
            hour = timestamp.hour

            key = f"{day_of_week}_{hour}"
            temporal_groups[key].append(task)

        # Check for recurring patterns
        for time_key, time_tasks in temporal_groups.items():
            if len(time_tasks) >= self.min_occurrences:
                # Check if tasks are similar
                task_counts = Counter(time_tasks)
                most_common_task, count = task_counts.most_common(1)[0]

                if count >= 2:  # At least 2 occurrences at same time
                    pattern_id = f"temporal_{hash(time_key + most_common_task)}"

                    if pattern_id not in self.patterns:
                        day, hour = time_key.split('_')
                        self.patterns[pattern_id] = {
                            "type": "temporal",
                            "task": most_common_task,
                            "day_of_week": day,
                            "hour": int(hour),
                            "count": count,
                            "detected_at": datetime.now().isoformat()
                        }

                        self._suggest_automation(pattern_id, most_common_task, "temporal")

                        logger.info(f"🔍 Temporal pattern: '{most_common_task[:50]}' every {day} at {hour}:00")

    def _detect_sequential_patterns(self, tasks: List[Dict]):
        """Detect sequential task patterns (task chains)"""
        # Look for sequences of tasks that often occur together
        if len(tasks) < 2:
            return

        # Build sequences (sliding window of 3 tasks)
        sequences = []
        for i in range(len(tasks) - 2):
            seq = tuple([tasks[i]["task"], tasks[i+1]["task"], tasks[i+2]["task"]])
            sequences.append(seq)

        # Count sequence occurrences
        seq_counts = Counter(sequences)

        for seq, count in seq_counts.items():
            if count >= 2:  # Sequence occurred at least twice
                pattern_id = f"sequential_{hash(seq)}"

                if pattern_id not in self.patterns:
                    self.patterns[pattern_id] = {
                        "type": "sequential",
                        "sequence": list(seq),
                        "count": count,
                        "detected_at": datetime.now().isoformat()
                    }

                    self._suggest_automation(pattern_id, " → ".join(seq), "sequential")

                    logger.info(f"🔍 Sequential pattern: {' → '.join([s[:30] for s in seq])}")

    def _suggest_automation(self, pattern_id: str, task: str, pattern_type: str):
        """Generate automation suggestion"""
        suggestion = {
            "id": pattern_id,
            "pattern_type": pattern_type,
            "task": task,
            "suggested_at": datetime.now().isoformat(),
            "status": "pending",
            "automation_type": self._determine_automation_type(task, pattern_type)
        }

        self.suggestions.append(suggestion)
        logger.info(f"💡 Automation suggested: {suggestion['automation_type']} for '{task[:50]}'")

    def _determine_automation_type(self, task: str, pattern_type: str) -> str:
        """Determine what type of automation to suggest"""
        task_lower = task.lower()

        if pattern_type == "temporal":
            return "scheduled_task"
        elif pattern_type == "sequential":
            return "workflow"
        elif "email" in task_lower or "send" in task_lower:
            return "email_automation"
        elif "report" in task_lower or "summary" in task_lower:
            return "report_generator"
        elif "check" in task_lower or "monitor" in task_lower:
            return "monitoring_agent"
        else:
            return "custom_agent"

    def get_suggestions(self, status: str = "pending") -> List[Dict]:
        """Get automation suggestions"""
        return [s for s in self.suggestions if s["status"] == status]

    def approve_automation(self, suggestion_id: str) -> Dict[str, Any]:
        """
        Approve and deploy automation

        Args:
            suggestion_id: Suggestion ID to approve

        Returns:
            Automation details
        """
        suggestion = next((s for s in self.suggestions if s["id"] == suggestion_id), None)

        if not suggestion:
            logger.error(f"❌ Suggestion {suggestion_id} not found")
            return {"success": False, "error": "Suggestion not found"}

        # Generate automation code
        automation = self._generate_automation(suggestion)

        # Deploy automation
        self.automations[suggestion_id] = automation
        suggestion["status"] = "approved"

        logger.info(f"✅ Automation deployed: {automation['name']}")

        return {
            "success": True,
            "automation": automation
        }

    def _generate_automation(self, suggestion: Dict) -> Dict[str, Any]:
        """Generate automation code/config"""
        automation_type = suggestion["automation_type"]
        task = suggestion["task"]

        automation = {
            "id": suggestion["id"],
            "name": f"Auto_{automation_type}_{suggestion['id'][:8]}",
            "type": automation_type,
            "task": task,
            "created_at": datetime.now().isoformat(),
            "config": {}
        }

        # Generate type-specific config
        if automation_type == "scheduled_task":
            pattern = self.patterns.get(suggestion["id"], {})
            automation["config"] = {
                "schedule": f"cron: 0 {pattern.get('hour', 9)} * * {pattern.get('day_of_week', 'MON')}",
                "action": task
            }

        elif automation_type == "workflow":
            pattern = self.patterns.get(suggestion["id"], {})
            automation["config"] = {
                "steps": pattern.get("sequence", []),
                "trigger": "manual"
            }

        elif automation_type == "email_automation":
            automation["config"] = {
                "trigger": "pattern_match",
                "action": "send_email",
                "template": task
            }

        return automation

    def get_stats(self) -> Dict[str, Any]:
        """Get automation statistics"""
        return {
            "total_tasks_logged": len(self.task_history),
            "patterns_detected": len(self.patterns),
            "suggestions_pending": len([s for s in self.suggestions if s["status"] == "pending"]),
            "automations_active": len(self.automations),
            "pattern_types": Counter([p["type"] for p in self.patterns.values()])
        }

    def save(self, filepath: str):
        """Save automation state"""
        data = {
            "task_history": self.task_history[-1000:],  # Keep last 1000
            "patterns": self.patterns,
            "automations": self.automations,
            "suggestions": self.suggestions
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Automation state saved to {filepath}")

    def load(self, filepath: str):
        """Load automation state"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.task_history = data.get("task_history", [])
            self.patterns = data.get("patterns", {})
            self.automations = data.get("automations", {})
            self.suggestions = data.get("suggestions", [])

            logger.info(f"📂 Automation state loaded from {filepath}")

        except Exception as e:
            logger.error(f"❌ Failed to load automation state: {e}")


# Test
if __name__ == "__main__":
    ha = HyperAutomation()

    # Simulate task logging
    tasks = [
        "Send daily report to team",
        "Check server status",
        "Send daily report to team",
        "Update project dashboard",
        "Send daily report to team",
        "Check server status",
        "Send weekly summary email",
        "Check server status"
    ]

    for task in tasks:
        ha.log_task(task)

    print("\n" + "="*50)
    print("HYPER-AUTOMATION STATS")
    print("="*50)
    print(json.dumps(ha.get_stats(), indent=2))

    print("\n" + "="*50)
    print("AUTOMATION SUGGESTIONS")
    print("="*50)

    suggestions = ha.get_suggestions()
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion['automation_type'].upper()}")
        print(f"   Task: {suggestion['task']}")
        print(f"   Pattern: {suggestion['pattern_type']}")
        print(f"   ID: {suggestion['id'][:16]}")

    # Approve first suggestion
    if suggestions:
        print("\n" + "="*50)
        print("APPROVING FIRST SUGGESTION")
        print("="*50)

        result = ha.approve_automation(suggestions[0]["id"])
        if result["success"]:
            print(f"✅ Automation deployed: {result['automation']['name']}")
            print(f"   Config: {json.dumps(result['automation']['config'], indent=2)}")
