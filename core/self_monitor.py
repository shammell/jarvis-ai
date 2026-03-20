# ==========================================================
# JARVIS v9.0 - Self-Monitoring System
# Track performance, identify weaknesses, report metrics
# Learn from outcomes and adapt strategies
# ==========================================================

import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from pathlib import Path
import statistics

logger = logging.getLogger(__name__)


class MetricType:
    TASK_SUCCESS_RATE = "task_success_rate"
    RESPONSE_TIME = "response_time"
    AUTONOMY_LEVEL = "autonomy_level"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    DECISION_ACCURACY = "decision_accuracy"


class SelfMonitor:
    """
    Self-monitoring and performance tracking system
    - Track actions and outcomes
    - Measure success rates
    - Identify patterns in failures
    - Report performance metrics
    - Suggest improvements
    """

    def __init__(self, storage_path: str = None):
        # Default to Claude auto-memory location
        if storage_path is None:
            storage_path = str(Path.home() / ".claude" / "projects" / "C--Users-AK" / "memory" / "self_monitor.json")

        self.storage_path = storage_path

        # Metrics storage
        self.metrics = defaultdict(list)
        self.action_history = []
        self.error_log = []
        self.performance_snapshots = []

        # Performance thresholds
        self.thresholds = {
            MetricType.TASK_SUCCESS_RATE: 0.8,  # 80% success rate
            MetricType.RESPONSE_TIME: 2.0,       # 2 seconds
            MetricType.AUTONOMY_LEVEL: 0.7,      # 70% autonomy
            MetricType.ERROR_RATE: 0.1,          # 10% error rate
            MetricType.DECISION_ACCURACY: 0.85   # 85% accuracy
        }

        # Load existing data
        self._load_data()

        logger.info("📊 Self-Monitor initialized")

    def record_action(
        self,
        action: str,
        action_type: str,
        success: bool,
        duration: float = None,
        context: Dict[str, Any] = None,
        error: str = None
    ):
        """
        Record an action and its outcome

        Args:
            action: Action description
            action_type: Type of action (task, decision, etc.)
            success: Whether action succeeded
            duration: Time taken (seconds)
            context: Additional context
            error: Error message if failed
        """
        record = {
            "action": action,
            "action_type": action_type,
            "success": success,
            "duration": duration,
            "context": context or {},
            "error": error,
            "timestamp": datetime.now().isoformat()
        }

        self.action_history.append(record)

        # Update metrics
        self._update_metrics(record)

        # Log errors
        if not success and error:
            self.error_log.append({
                "action": action,
                "error": error,
                "timestamp": datetime.now().isoformat(),
                "context": context
            })

        self._save_data()

        logger.debug(f"📝 Action recorded: {action[:50]} - {'✅' if success else '❌'}")

    def record_metric(self, metric_type: str, value: float, context: Dict[str, Any] = None):
        """
        Record a metric value

        Args:
            metric_type: Type of metric
            value: Metric value
            context: Additional context
        """
        self.metrics[metric_type].append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        })

        self._save_data()

        logger.debug(f"📊 Metric recorded: {metric_type} = {value}")

    def get_success_rate(self, time_window_hours: int = 24) -> float:
        """Get success rate for recent actions"""
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent_actions = [
            a for a in self.action_history
            if datetime.fromisoformat(a["timestamp"]) > cutoff
        ]

        if not recent_actions:
            return 0.0

        successful = len([a for a in recent_actions if a["success"]])
        return successful / len(recent_actions)

    def get_average_response_time(self, time_window_hours: int = 24) -> float:
        """Get average response time"""
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent_actions = [
            a for a in self.action_history
            if datetime.fromisoformat(a["timestamp"]) > cutoff
            and a.get("duration") is not None
        ]

        if not recent_actions:
            return 0.0

        durations = [a["duration"] for a in recent_actions]
        return statistics.mean(durations)

    def get_error_rate(self, time_window_hours: int = 24) -> float:
        """Get error rate"""
        return 1.0 - self.get_success_rate(time_window_hours)

    def identify_failure_patterns(self) -> List[Dict[str, Any]]:
        """
        Identify patterns in failures

        Returns:
            List of failure patterns with frequency
        """
        failed_actions = [a for a in self.action_history if not a["success"]]

        if not failed_actions:
            return []

        # Group by action type
        type_failures = Counter([a["action_type"] for a in failed_actions])

        # Group by error message
        error_failures = Counter([a.get("error", "Unknown") for a in failed_actions])

        patterns = []

        # Action type patterns
        for action_type, count in type_failures.most_common(5):
            patterns.append({
                "type": "action_type",
                "pattern": action_type,
                "failure_count": count,
                "percentage": count / len(failed_actions)
            })

        # Error message patterns
        for error, count in error_failures.most_common(5):
            patterns.append({
                "type": "error_message",
                "pattern": error,
                "failure_count": count,
                "percentage": count / len(failed_actions)
            })

        return patterns

    def identify_weaknesses(self) -> List[str]:
        """
        Identify system weaknesses based on metrics

        Returns:
            List of weakness descriptions
        """
        weaknesses = []

        # Check success rate
        success_rate = self.get_success_rate()
        if success_rate < self.thresholds[MetricType.TASK_SUCCESS_RATE]:
            weaknesses.append(
                f"Low success rate: {success_rate:.1%} (threshold: {self.thresholds[MetricType.TASK_SUCCESS_RATE]:.1%})"
            )

        # Check response time
        avg_response_time = self.get_average_response_time()
        if avg_response_time > self.thresholds[MetricType.RESPONSE_TIME]:
            weaknesses.append(
                f"Slow response time: {avg_response_time:.2f}s (threshold: {self.thresholds[MetricType.RESPONSE_TIME]:.2f}s)"
            )

        # Check error rate
        error_rate = self.get_error_rate()
        if error_rate > self.thresholds[MetricType.ERROR_RATE]:
            weaknesses.append(
                f"High error rate: {error_rate:.1%} (threshold: {self.thresholds[MetricType.ERROR_RATE]:.1%})"
            )

        # Check failure patterns
        patterns = self.identify_failure_patterns()
        if patterns:
            top_pattern = patterns[0]
            if top_pattern["percentage"] > 0.3:  # >30% of failures
                weaknesses.append(
                    f"Recurring failure pattern: {top_pattern['pattern']} ({top_pattern['percentage']:.1%} of failures)"
                )

        return weaknesses

    def suggest_improvements(self) -> List[Dict[str, Any]]:
        """
        Suggest improvements based on identified weaknesses

        Returns:
            List of improvement suggestions
        """
        suggestions = []
        weaknesses = self.identify_weaknesses()

        for weakness in weaknesses:
            if "success rate" in weakness.lower():
                suggestions.append({
                    "weakness": weakness,
                    "suggestion": "Improve task decomposition and error handling",
                    "priority": "high",
                    "actions": [
                        "Review failed tasks and identify common causes",
                        "Add more robust error recovery mechanisms",
                        "Improve task validation before execution"
                    ]
                })

            elif "response time" in weakness.lower():
                suggestions.append({
                    "weakness": weakness,
                    "suggestion": "Optimize execution pipeline and reduce latency",
                    "priority": "medium",
                    "actions": [
                        "Profile slow operations",
                        "Add caching for repeated operations",
                        "Parallelize independent tasks"
                    ]
                })

            elif "error rate" in weakness.lower():
                suggestions.append({
                    "weakness": weakness,
                    "suggestion": "Strengthen error handling and validation",
                    "priority": "high",
                    "actions": [
                        "Add input validation",
                        "Implement retry logic for transient failures",
                        "Improve error messages and logging"
                    ]
                })

            elif "failure pattern" in weakness.lower():
                suggestions.append({
                    "weakness": weakness,
                    "suggestion": "Address recurring failure pattern",
                    "priority": "critical",
                    "actions": [
                        "Investigate root cause of pattern",
                        "Implement specific fix for this pattern",
                        "Add monitoring for this pattern"
                    ]
                })

        return suggestions

    def generate_report(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive performance report

        Args:
            time_window_hours: Time window for metrics

        Returns:
            Performance report
        """
        cutoff = datetime.now() - timedelta(hours=time_window_hours)
        recent_actions = [
            a for a in self.action_history
            if datetime.fromisoformat(a["timestamp"]) > cutoff
        ]

        # Calculate metrics
        success_rate = self.get_success_rate(time_window_hours)
        avg_response_time = self.get_average_response_time(time_window_hours)
        error_rate = self.get_error_rate(time_window_hours)

        # Action type breakdown
        action_types = Counter([a["action_type"] for a in recent_actions])

        # Success by action type
        success_by_type = {}
        for action_type in action_types.keys():
            type_actions = [a for a in recent_actions if a["action_type"] == action_type]
            successful = len([a for a in type_actions if a["success"]])
            success_by_type[action_type] = successful / len(type_actions) if type_actions else 0.0

        report = {
            "period": f"Last {time_window_hours} hours",
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_actions": len(recent_actions),
                "success_rate": success_rate,
                "error_rate": error_rate,
                "avg_response_time": avg_response_time
            },
            "action_breakdown": dict(action_types),
            "success_by_type": success_by_type,
            "failure_patterns": self.identify_failure_patterns(),
            "weaknesses": self.identify_weaknesses(),
            "suggestions": self.suggest_improvements(),
            "health_score": self._calculate_health_score()
        }

        return report

    def _calculate_health_score(self) -> float:
        """
        Calculate overall system health score (0-100)

        Returns:
            Health score
        """
        scores = []

        # Success rate score
        success_rate = self.get_success_rate()
        scores.append(success_rate * 100)

        # Response time score (inverse)
        avg_response_time = self.get_average_response_time()
        if avg_response_time > 0:
            response_score = max(0, 100 - (avg_response_time / self.thresholds[MetricType.RESPONSE_TIME]) * 50)
            scores.append(response_score)

        # Error rate score (inverse)
        error_rate = self.get_error_rate()
        error_score = max(0, 100 - (error_rate / self.thresholds[MetricType.ERROR_RATE]) * 100)
        scores.append(error_score)

        return statistics.mean(scores) if scores else 0.0

    def take_snapshot(self):
        """Take a performance snapshot"""
        snapshot = {
            "timestamp": datetime.now().isoformat(),
            "success_rate": self.get_success_rate(),
            "avg_response_time": self.get_average_response_time(),
            "error_rate": self.get_error_rate(),
            "health_score": self._calculate_health_score(),
            "total_actions": len(self.action_history)
        }

        self.performance_snapshots.append(snapshot)
        self._save_data()

        logger.info(f"📸 Performance snapshot taken: Health={snapshot['health_score']:.1f}")

    def _update_metrics(self, record: Dict[str, Any]):
        """Update metrics based on action record"""
        # Update success rate metric
        self.record_metric(
            MetricType.TASK_SUCCESS_RATE,
            1.0 if record["success"] else 0.0,
            {"action_type": record["action_type"]}
        )

        # Update response time metric
        if record.get("duration"):
            self.record_metric(
                MetricType.RESPONSE_TIME,
                record["duration"],
                {"action_type": record["action_type"]}
            )

    def _save_data(self):
        """Save monitoring data"""
        try:
            # Ensure directory exists
            Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)

            data = {
                "metrics": dict(self.metrics),
                "action_history": self.action_history[-1000:],  # Keep last 1000
                "error_log": self.error_log[-500:],  # Keep last 500
                "performance_snapshots": self.performance_snapshots[-100:]  # Keep last 100
            }

            with open(self.storage_path, 'w') as f:
                json.dump(data, f, indent=2)

            logger.debug(f"💾 Monitoring data saved to {self.storage_path}")

        except Exception as e:
            logger.error(f"❌ Failed to save monitoring data: {e}")

    def _load_data(self):
        """Load monitoring data"""
        try:
            if Path(self.storage_path).exists():
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)

                self.metrics = defaultdict(list, data.get("metrics", {}))
                self.action_history = data.get("action_history", [])
                self.error_log = data.get("error_log", [])
                self.performance_snapshots = data.get("performance_snapshots", [])

                logger.info(f"📂 Loaded monitoring data from {self.storage_path}")
            else:
                logger.info("📂 No existing monitoring data found, starting fresh")

        except Exception as e:
            logger.error(f"❌ Failed to load monitoring data: {e}")


# Test
if __name__ == "__main__":
    import time

    monitor = SelfMonitor("test_monitor.json")

    # Simulate actions
    actions = [
        ("Read file", "file_operation", True, 0.1),
        ("Write file", "file_operation", True, 0.2),
        ("API call", "network", False, 1.5, "Connection timeout"),
        ("Process data", "computation", True, 0.5),
        ("API call", "network", False, 2.0, "Connection timeout"),
        ("Read file", "file_operation", True, 0.1),
        ("API call", "network", True, 0.8),
        ("Process data", "computation", True, 0.6),
    ]

    for action, action_type, success, duration, *error in actions:
        error_msg = error[0] if error else None
        monitor.record_action(action, action_type, success, duration, error=error_msg)
        time.sleep(0.1)

    # Take snapshot
    monitor.take_snapshot()

    # Generate report
    print("\n" + "="*50)
    print("PERFORMANCE REPORT")
    print("="*50)
    report = monitor.generate_report()
    print(json.dumps(report, indent=2))

    print("\n" + "="*50)
    print("HEALTH SCORE")
    print("="*50)
    print(f"Overall Health: {report['health_score']:.1f}/100")

    print("\n" + "="*50)
    print("WEAKNESSES")
    print("="*50)
    for weakness in report["weaknesses"]:
        print(f"⚠️ {weakness}")

    print("\n" + "="*50)
    print("SUGGESTIONS")
    print("="*50)
    for suggestion in report["suggestions"]:
        print(f"\n🔧 {suggestion['suggestion']}")
        print(f"   Priority: {suggestion['priority'].upper()}")
        print(f"   Actions:")
        for action in suggestion["actions"]:
            print(f"   - {action}")
