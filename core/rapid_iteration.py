# ==========================================================
# JARVIS v9.0 - Rapid Iteration Loop
# Fast feedback loops - measure, learn, improve every 5 minutes
# A/B test prompt variations, auto-tune hyperparameters
# ==========================================================

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import statistics
import random

logger = logging.getLogger(__name__)


class RapidIteration:
    """
    Rapid iteration engine for JARVIS v9.0
    - Track every decision outcome
    - A/B test prompt variations
    - Auto-tune hyperparameters
    - Deploy improvements without restart
    """

    def __init__(self):
        self.experiments = {}  # Active A/B tests
        self.results = []  # Experiment results
        self.hyperparameters = {
            "temperature": 0.7,
            "max_tokens": 1024,
            "top_p": 0.9,
            "frequency_penalty": 0.0
        }
        self.performance_history = []  # Performance metrics over time

        # Iteration settings
        self.iteration_interval_minutes = 5
        self.min_samples_per_variant = 10
        self.confidence_threshold = 0.95

        logger.info("🔄 Rapid Iteration Engine initialized")

    def create_experiment(
        self,
        name: str,
        variants: List[Dict[str, Any]],
        metric: str = "success_rate"
    ) -> str:
        """
        Create A/B test experiment

        Args:
            name: Experiment name
            variants: List of variants to test
            metric: Metric to optimize (success_rate, latency, quality)

        Returns:
            Experiment ID
        """
        experiment_id = f"exp_{hash(name + str(datetime.now()))}"

        experiment = {
            "id": experiment_id,
            "name": name,
            "variants": variants,
            "metric": metric,
            "created_at": datetime.now().isoformat(),
            "status": "active",
            "results": {v["id"]: [] for v in variants}
        }

        self.experiments[experiment_id] = experiment
        logger.info(f"🧪 Experiment created: {name} ({len(variants)} variants)")

        return experiment_id

    def get_variant(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get variant to use (epsilon-greedy selection)

        Args:
            experiment_id: Experiment ID

        Returns:
            Variant to use
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment or experiment["status"] != "active":
            return None

        # Epsilon-greedy: 10% exploration, 90% exploitation
        epsilon = 0.1

        if random.random() < epsilon:
            # Explore: random variant
            variant = random.choice(experiment["variants"])
            logger.debug(f"🎲 Exploring variant: {variant['id']}")
        else:
            # Exploit: best performing variant
            variant = self._get_best_variant(experiment)
            logger.debug(f"🎯 Exploiting best variant: {variant['id']}")

        return variant

    def record_result(
        self,
        experiment_id: str,
        variant_id: str,
        outcome: Dict[str, Any]
    ):
        """
        Record experiment result

        Args:
            experiment_id: Experiment ID
            variant_id: Variant ID
            outcome: Outcome metrics (success, latency, quality, etc.)
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            logger.error(f"❌ Experiment {experiment_id} not found")
            return

        result = {
            "variant_id": variant_id,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        }

        experiment["results"][variant_id].append(result)
        self.results.append(result)

        logger.debug(f"📊 Result recorded: {variant_id} - {outcome}")

        # Check if we should conclude experiment
        self._check_experiment_conclusion(experiment_id)

    def _get_best_variant(self, experiment: Dict) -> Dict[str, Any]:
        """Get best performing variant based on metric"""
        metric = experiment["metric"]
        best_variant = None
        best_score = -float('inf')

        for variant in experiment["variants"]:
            variant_id = variant["id"]
            results = experiment["results"][variant_id]

            if not results:
                # No data yet, return this variant
                return variant

            # Calculate average metric
            scores = [r["outcome"].get(metric, 0) for r in results]
            avg_score = statistics.mean(scores)

            if avg_score > best_score:
                best_score = avg_score
                best_variant = variant

        return best_variant or experiment["variants"][0]

    def _check_experiment_conclusion(self, experiment_id: str):
        """Check if experiment has enough data to conclude"""
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            return

        # Check if all variants have minimum samples
        min_samples = self.min_samples_per_variant
        all_have_samples = all(
            len(results) >= min_samples
            for results in experiment["results"].values()
        )

        if not all_have_samples:
            return

        # Perform statistical test
        winner = self._determine_winner(experiment)

        if winner:
            experiment["status"] = "concluded"
            experiment["winner"] = winner
            experiment["concluded_at"] = datetime.now().isoformat()

            logger.info(f"🏆 Experiment concluded: {experiment['name']} - Winner: {winner['id']}")

            # Auto-deploy winner
            self._deploy_winner(experiment, winner)

    def _determine_winner(self, experiment: Dict) -> Optional[Dict[str, Any]]:
        """Determine experiment winner using statistical test"""
        metric = experiment["metric"]
        variant_scores = {}

        # Calculate mean and std for each variant
        for variant in experiment["variants"]:
            variant_id = variant["id"]
            results = experiment["results"][variant_id]
            scores = [r["outcome"].get(metric, 0) for r in results]

            if len(scores) < 2:
                continue

            variant_scores[variant_id] = {
                "variant": variant,
                "mean": statistics.mean(scores),
                "stdev": statistics.stdev(scores),
                "n": len(scores)
            }

        if len(variant_scores) < 2:
            return None

        # Find best variant
        best_variant_id = max(variant_scores.keys(), key=lambda k: variant_scores[k]["mean"])
        best_stats = variant_scores[best_variant_id]

        # Check if significantly better than others
        # Simplified: just check if mean is >10% better
        for variant_id, stats in variant_scores.items():
            if variant_id == best_variant_id:
                continue

            improvement = (best_stats["mean"] - stats["mean"]) / stats["mean"]
            if improvement < 0.1:  # Not significantly better
                return None

        return best_stats["variant"]

    def _deploy_winner(self, experiment: Dict, winner: Dict[str, Any]):
        """Deploy winning variant"""
        logger.info(f"🚀 Deploying winner: {winner['id']}")

        # Update hyperparameters if applicable
        if "hyperparameters" in winner:
            self.hyperparameters.update(winner["hyperparameters"])
            logger.info(f"⚙️ Hyperparameters updated: {winner['hyperparameters']}")

        # Store deployment record
        deployment = {
            "experiment_id": experiment["id"],
            "winner_id": winner["id"],
            "deployed_at": datetime.now().isoformat(),
            "config": winner
        }

        # TODO: Actually deploy changes (restart services, update configs, etc.)

    def auto_tune_hyperparameters(self, task_type: str = "general"):
        """
        Auto-tune hyperparameters based on recent performance

        Args:
            task_type: Type of task to tune for
        """
        logger.info(f"🎛️ Auto-tuning hyperparameters for {task_type}...")

        # Create experiment with hyperparameter variants
        variants = [
            {
                "id": "baseline",
                "hyperparameters": self.hyperparameters.copy()
            },
            {
                "id": "low_temp",
                "hyperparameters": {**self.hyperparameters, "temperature": 0.3}
            },
            {
                "id": "high_temp",
                "hyperparameters": {**self.hyperparameters, "temperature": 0.9}
            },
            {
                "id": "more_tokens",
                "hyperparameters": {**self.hyperparameters, "max_tokens": 2048}
            }
        ]

        experiment_id = self.create_experiment(
            name=f"hyperparam_tune_{task_type}",
            variants=variants,
            metric="quality"
        )

        logger.info(f"✅ Hyperparameter tuning experiment started: {experiment_id}")

        return experiment_id

    def track_performance(self, metrics: Dict[str, float]):
        """
        Track performance metrics over time

        Args:
            metrics: Performance metrics (latency, success_rate, quality, etc.)
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }

        self.performance_history.append(entry)

        # Keep only last 1000 entries
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]

        logger.debug(f"📈 Performance tracked: {metrics}")

    def get_performance_trend(self, metric: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance trend for a metric

        Args:
            metric: Metric name
            hours: Hours to look back

        Returns:
            Trend analysis
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        recent_entries = [
            e for e in self.performance_history
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]

        if not recent_entries:
            return {"trend": "no_data"}

        values = [e["metrics"].get(metric, 0) for e in recent_entries]

        if len(values) < 2:
            return {"trend": "insufficient_data"}

        # Calculate trend
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)

        change = (avg_second - avg_first) / avg_first if avg_first > 0 else 0

        trend = "improving" if change > 0.05 else "declining" if change < -0.05 else "stable"

        return {
            "trend": trend,
            "change_percent": change * 100,
            "current_avg": avg_second,
            "previous_avg": avg_first,
            "samples": len(values)
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get iteration statistics"""
        return {
            "active_experiments": len([e for e in self.experiments.values() if e["status"] == "active"]),
            "concluded_experiments": len([e for e in self.experiments.values() if e["status"] == "concluded"]),
            "total_results": len(self.results),
            "current_hyperparameters": self.hyperparameters,
            "performance_entries": len(self.performance_history)
        }

    def save(self, filepath: str):
        """Save iteration state"""
        data = {
            "experiments": self.experiments,
            "results": self.results[-1000:],
            "hyperparameters": self.hyperparameters,
            "performance_history": self.performance_history[-1000:]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Iteration state saved to {filepath}")


# Test
if __name__ == "__main__":
    ri = RapidIteration()

    # Create experiment
    variants = [
        {"id": "prompt_v1", "prompt": "You are a helpful assistant."},
        {"id": "prompt_v2", "prompt": "You are an expert AI assistant."},
        {"id": "prompt_v3", "prompt": "You are a highly capable assistant."}
    ]

    exp_id = ri.create_experiment("prompt_test", variants, metric="quality")

    # Simulate results
    for _ in range(30):
        variant = ri.get_variant(exp_id)
        if variant:
            # Simulate outcome (prompt_v2 is best)
            quality = 0.8 if variant["id"] == "prompt_v2" else 0.6 + random.random() * 0.2
            ri.record_result(exp_id, variant["id"], {"quality": quality})

    print("\n" + "="*50)
    print("RAPID ITERATION STATS")
    print("="*50)
    print(json.dumps(ri.get_stats(), indent=2))

    print("\n" + "="*50)
    print("EXPERIMENT RESULTS")
    print("="*50)
    exp = ri.experiments[exp_id]
    print(f"Status: {exp['status']}")
    if exp.get("winner"):
        print(f"Winner: {exp['winner']['id']}")
