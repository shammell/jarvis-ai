# ==========================================================
# JARVIS v9.0 - Performance Profiler
# Detects bottlenecks and profiles system performance
# ==========================================================

import logging
import time
import statistics
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)


class Profiler:
    """
    Performance profiler for JARVIS v9.0
    - Bottleneck detection
    - Latency profiling
    - Resource usage tracking
    - Auto-optimization suggestions
    """

    def __init__(self):
        self.profiles = []
        self.benchmarks = {}
        self.bottlenecks = []
        self._lock = threading.Lock()

        # Thresholds
        self.thresholds = {
            "latency_warning_ms": 500,
            "latency_critical_ms": 1000,
            "memory_warning_percent": 70,
            "memory_critical_percent": 90,
            "cpu_warning_percent": 60,
            "cpu_critical_percent": 85
        }

        # Component tracking
        self.component_stats = {}

        logger.info("📈 Profiler initialized")

    @contextmanager
    def profile(self, operation: str, component: str = "default"):
        """
        Context manager for profiling operations

        Usage:
            with profiler.profile("skill_matching", "orchestrator"):
                result = match_skills(query)
        """
        start_time = time.perf_counter()
        start_mem = self._get_memory_usage()

        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            mem_usage = self._get_memory_usage()

            profile_entry = {
                "operation": operation,
                "component": component,
                "latency_ms": round(elapsed_ms, 2),
                "memory_mb": mem_usage,
                "timestamp": datetime.now().isoformat()
            }

            with self._lock:
                self.profiles.append(profile_entry)

                # Track component stats
                if component not in self.component_stats:
                    self.component_stats[component] = []
                self.component_stats[component].append(elapsed_ms)

                # Check for bottlenecks
                self._check_bottleneck(profile_entry)

            logger.debug(f"📊 Profiled: {operation} - {elapsed_ms:.2f}ms")

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0

    def _check_bottleneck(self, entry: Dict[str, Any]):
        """Check if operation is a bottleneck"""
        latency = entry["latency_ms"]

        if latency > self.thresholds["latency_critical_ms"]:
            bottleneck = {
                "type": "critical_latency",
                "operation": entry["operation"],
                "component": entry["component"],
                "latency_ms": latency,
                "timestamp": entry["timestamp"],
                "suggestion": self._get_optimization_suggestion(entry)
            }
            self.bottlenecks.append(bottleneck)
            logger.warning(f"🐌 Bottleneck detected: {entry['operation']} ({latency:.2f}ms)")

    def _get_optimization_suggestion(self, entry: Dict) -> str:
        """Get optimization suggestion for bottleneck"""
        operation = entry["operation"]

        suggestions = {
            "skill_matching": "Add caching for repeated queries or use vector indexing",
            "memory_retrieve": "Implement batch retrieval or increase top_k efficiency",
            "llm_generate": "Enable speculative decoding or reduce max_tokens",
            "system2_reason": "Reduce max_iterations or use cached reasoning paths",
            "decision_evaluate": "Lower risk assessment complexity for common actions"
        }

        return suggestions.get(operation, "Profile to identify specific hot paths")

    def record_benchmark(self, name: str, value: float, unit: str = "ms"):
        """Record a benchmark measurement"""
        if name not in self.benchmarks:
            self.benchmarks[name] = []

        self.benchmarks[name].append({
            "value": value,
            "unit": unit,
            "timestamp": datetime.now().isoformat()
        })

        logger.debug(f"📊 Benchmark: {name} = {value}{unit}")

    def get_component_stats(self, component: str) -> Dict[str, Any]:
        """Get statistics for a component"""
        if component not in self.component_stats:
            return {"component": component, "status": "no_data"}

        latencies = self.component_stats[component]

        return {
            "component": component,
            "count": len(latencies),
            "avg_ms": round(statistics.mean(latencies), 2) if latencies else 0,
            "median_ms": round(statistics.median(latencies), 2) if latencies else 0,
            "stdev_ms": round(statistics.stdev(latencies), 2) if len(latencies) > 1 else 0,
            "min_ms": round(min(latencies), 2) if latencies else 0,
            "max_ms": round(max(latencies), 2) if latencies else 0
        }

    def get_benchmarks(self, name: str = None) -> Dict[str, Any]:
        """Get benchmark data"""
        if name:
            if name not in self.benchmarks:
                return {"status": "no_data"}

            values = [b["value"] for b in self.benchmarks[name]]
            return {
                "name": name,
                "count": len(values),
                "avg": round(statistics.mean(values), 2) if values else 0,
                "min": round(min(values), 2) if values else 0,
                "max": round(max(values), 2) if values else 0,
                "unit": self.benchmarks[name][0]["unit"] if values else "ms"
            }

        return {name: self.get_benchmarks(name) for name in self.benchmarks}

    def get_bottlelinecks(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get detected bottlenecks"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            b for b in self.bottlenecks
            if datetime.fromisoformat(b["timestamp"]) > cutoff
        ]
        return recent

    def get_profile_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary of profiling data"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            p for p in self.profiles
            if datetime.fromisoformat(p["timestamp"]) > cutoff
        ]

        if not recent:
            return {"status": "no_data"}

        latencies = [p["latency_ms"] for p in recent]

        return {
            "total_profiles": len(recent),
            "avg_latency_ms": round(statistics.mean(latencies), 2),
            "median_latency_ms": round(statistics.median(latencies), 2),
            "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95)] if len(latencies) > 20 else max(latencies), 2),
            "max_latency_ms": round(max(latencies), 2),
            "bottlenecks_detected": len(self.get_bottlelinecks(hours))
        }

    def generate_report(self) -> str:
        """Generate profiling report"""
        summary = self.get_profile_summary()
        bottlenecks = self.get_bottlelinecks()

        report = "=" * 60 + "\n"
        report += "PERFILING REPORT\n"
        report += "=" * 60 + "\n\n"

        report += f"Total Profiles: {summary.get('total_profiles', 0)}\n"
        report += f"Avg Latency: {summary.get('avg_latency_ms', 0):.2f}ms\n"
        report += f"P95 Latency: {summary.get('p95_latency_ms', 0):.2f}ms\n"
        report += f"Bottlenecks: {len(bottlenecks)}\n\n"

        if bottlenecks:
            report += "TOP BOTTLENECKS:\n"
            for i, bn in enumerate(bottlenecks[:5], 1):
                report += f"  {i}. {bn['operation']} ({bn['latency_ms']:.2f}ms)\n"
                report += f"     Suggestion: {bn['suggestion']}\n"

        report += "\n" + "=" * 60

        return report

    def get_stats(self) -> Dict[str, Any]:
        """Get profiler statistics"""
        return {
            "total_profiles": len(self.profiles),
            "total_benchmarks": len(self.benchmarks),
            "total_bottlenecks": len(self.bottlenecks),
            "components_tracked": list(self.component_stats.keys()),
            "summary": self.get_profile_summary(hours=1)
        }

    def save(self, filepath: str):
        """Save profiler state"""
        import json
        data = {
            "profiles": self.profiles[-500:],
            "benchmarks": self.benchmarks,
            "bottlenecks": self.bottlencks[-100:]
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"💾 Profiler state saved to {filepath}")
