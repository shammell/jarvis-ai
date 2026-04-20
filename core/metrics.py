# ==========================================================
# JARVIS v9.0 - Metrics Collection
# Prometheus-compatible metrics
# ==========================================================

import time
from typing import Dict, List
from collections import defaultdict
from datetime import datetime


class Counter:
    """Simple counter metric"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.value = 0

    def inc(self, amount: int = 1):
        """Increment counter"""
        self.value += amount

    def get(self) -> int:
        """Get current value"""
        return self.value


class Histogram:
    """Simple histogram metric"""
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.values: List[float] = []

    def observe(self, value: float):
        """Record observation"""
        self.values.append(value)

    def get_stats(self) -> Dict[str, float]:
        """Get statistics"""
        if not self.values:
            return {"count": 0, "sum": 0, "avg": 0, "min": 0, "max": 0}

        return {
            "count": len(self.values),
            "sum": sum(self.values),
            "avg": sum(self.values) / len(self.values),
            "min": min(self.values),
            "max": max(self.values)
        }


class MetricsCollector:
    """Centralized metrics collection"""

    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.histograms: Dict[str, Histogram] = {}

    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create counter"""
        if name not in self.counters:
            self.counters[name] = Counter(name, description)
        return self.counters[name]

    def histogram(self, name: str, description: str = "") -> Histogram:
        """Get or create histogram"""
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, description)
        return self.histograms[name]

    def get_all_metrics(self) -> Dict[str, any]:
        """Get all metrics"""
        metrics = {}

        # Counters
        for name, counter in self.counters.items():
            metrics[name] = counter.get()

        # Histograms
        for name, histogram in self.histograms.items():
            metrics[f"{name}_stats"] = histogram.get_stats()

        return metrics


# Global metrics instance
metrics = MetricsCollector()

# Pre-defined metrics
goal_executions = metrics.counter('jarvis_goal_executions_total', 'Total goals executed')
goal_duration = metrics.histogram('jarvis_goal_duration_seconds', 'Goal execution time')
api_requests = metrics.counter('jarvis_api_requests_total', 'Total API requests')
api_errors = metrics.counter('jarvis_api_errors_total', 'Total API errors')
