# ==========================================================
# JARVIS v9.0 - Quality Scorer
# Calculates response quality based on multiple signals
# ==========================================================

import logging
from typing import Dict, Any, List
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Quality scoring system for JARVIS responses
    - Multi-signal quality assessment
    - User feedback integration
    - Automatic quality trends
    """

    def __init__(self):
        self.quality_signals = []
        self.user_feedback = []
        self.baseline_quality = 0.75  # Default baseline

        # Quality dimensions
        self.dimensions = {
            "relevance": 0.0,
            "completeness": 0.0,
            "accuracy": 0.0,
            "clarity": 0.0,
            "actionability": 0.0
        }

        # Weights for each dimension
        self.weights = {
            "relevance": 0.30,
            "completeness": 0.25,
            "accuracy": 0.25,
            "clarity": 0.10,
            "actionability": 0.10
        }

        logger.info("📊 Quality Scorer initialized")

    def calculate_quality(
        self,
        response: Dict[str, Any],
        request: Dict[str, Any] = None,
        signals: Dict[str, Any] = None
    ) -> float:
        """
        Calculate quality score for a response

        Args:
            response: The generated response
            request: Original request (optional)
            signals: Additional quality signals

        Returns:
            Quality score 0.0 - 1.0
        """
        # Initialize dimensions
        scores = {dim: 0.0 for dim in self.dimensions}

        # 1. Relevance - does response address the request?
        if request:
            scores["relevance"] = self._calculate_relevance(request, response)
        else:
            scores["relevance"] = self.baseline_quality

        # 2. Completeness - is response thorough?
        scores["completeness"] = self._calculate_completeness(response)

        # 3. Accuracy - confidence indicators
        scores["accuracy"] = self._calculate_accuracy(response, signals)

        # 4. Clarity - readability and structure
        scores["clarity"] = self._calculate_clarity(response)

        # 5. Actionability - can user act on this?
        scores["actionability"] = self._calculate_actionability(response)

        # Weighted average
        quality = sum(scores[dim] * self.weights[dim] for dim in self.dimensions)

        # Record signal
        self.quality_signals.append({
            "timestamp": datetime.now().isoformat(),
            "quality": quality,
            "dimensions": scores,
            "response_id": response.get("metadata", {}).get("request_id", "unknown")
        })

        logger.debug(f"📊 Quality calculated: {quality:.2f} (dimensions: {scores})")

        return round(quality, 2)

    def _calculate_relevance(self, request: Dict, response: Dict) -> float:
        """Calculate relevance score"""
        request_text = request.get("message", "").lower()
        response_text = response.get("text", "").lower()

        # Check keyword overlap
        request_words = set(request_text.split())
        response_words = set(response_text.split())

        overlap = len(request_words & response_words)
        overlap_ratio = overlap / max(len(request_words), 1)

        # Boost if response directly addresses request keywords
        score = min(0.5 + overlap_ratio, 1.0)

        # Check for evasion patterns
        evasion_phrases = ["i don't know", "not sure", "maybe", "it depends"]
        if any(phrase in response_text for phrase in evasion_phrases):
            score *= 0.8

        return score

    def _calculate_completeness(self, response: Dict) -> float:
        """Calculate completeness score"""
        text = response.get("text", "")

        # Length bonus (up to a point)
        word_count = len(text.split())
        length_score = min(word_count / 200, 1.0)  # 200+ words = full score

        # Structure bonus
        structure_bonus = 0.0
        if any(marker in text for marker in ["\n\n", "-", "1.", "•", "**"]):
            structure_bonus = 0.1  # Has formatting

        # Coverage bonus - multiple topics addressed
        if response.get("metadata", {}).get("matched_skills", 0) > 0:
            structure_bonus += 0.1

        return min(length_score + structure_bonus, 1.0)

    def _calculate_accuracy(self, response: Dict, signals: Dict = None) -> float:
        """Calculate accuracy/confidence score"""
        # Base accuracy from response confidence
        base_accuracy = response.get("metadata", {}).get("confidence", 0.7)

        # Signal bonuses
        if signals:
            # Latency bonus - faster = more confident
            latency_ms = signals.get("latency_ms", 500)
            if latency_ms < 200:
                base_accuracy += 0.1
            elif latency_ms > 1000:
                base_accuracy -= 0.1

            # Source bonus
            source = signals.get("source", "")
            if source == "system2":
                base_accuracy += 0.1  # System 2 = more reliable

        return max(0.0, min(base_accuracy, 1.0))

    def _calculate_clarity(self, response: Dict) -> float:
        """Calculate clarity/readability score"""
        text = response.get("text", "")

        # Formatting indicators
        clarity_score = 0.5

        # Has paragraphs
        if "\n\n" in text:
            clarity_score += 0.15

        # Has lists
        if any(x in text for x in ["\n- ", "\n1. ", "\n• "]):
            clarity_score += 0.15

        # Has bold/emphasis
        if "**" in text or "__" in text:
            clarity_score += 0.1

        # No excessive length (readability penalty)
        if len(text) > 2000:
            clarity_score -= 0.1

        return max(0.0, min(clarity_score, 1.0))

    def _calculate_actionability(self, response: Dict) -> float:
        """Calculate actionability score"""
        text = response.get("text", "").lower()

        # Action indicators
        action_words = ["should", "could", "would", "try", "use", "run", "execute",
                       "implement", "create", "add", "fix", "check", "verify"]

        action_count = sum(1 for word in action_words if word in text)
        action_score = min(action_count / 5, 1.0)  # 5+ action words = full score

        # Code blocks indicate actionable content
        if "```" in text:
            action_score = min(action_score + 0.2, 1.0)

        # Next steps mentioned
        if "next" in text and ("step" in text or "action" in text):
            action_score = min(action_score + 0.1, 1.0)

        return action_score

    def record_user_feedback(self, request_id: str, feedback: Dict[str, Any]):
        """
        Record explicit user feedback

        Args:
            request_id: Request identifier
            feedback: Feedback data (rating, comment, etc.)
        """
        entry = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "feedback": feedback
        }

        self.user_feedback.append(entry)
        logger.info(f"📝 User feedback recorded: {feedback.get('rating', 'N/A')}")

    def get_quality_trend(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get quality trend over time

        Args:
            hours: Hours to analyze

        Returns:
            Trend analysis
        """
        cutoff = datetime.now()
        recent_signals = [
            s for s in self.quality_signals
            if datetime.fromisoformat(s["timestamp"]) > cutoff
        ]

        if not recent_signals:
            return {"trend": "insufficient_data", "avg_quality": self.baseline_quality}

        qualities = [s["quality"] for s in recent_signals]
        avg_quality = statistics.mean(qualities)

        # Compare first half vs second half
        if len(qualities) >= 4:
            first_half = statistics.mean(qualities[:len(qualities)//2])
            second_half = statistics.mean(qualities[len(qualities)//2:])
            change = (second_half - first_half) / max(first_half, 0.01)
            trend = "improving" if change > 0.05 else "declining" if change < -0.05 else "stable"
        else:
            trend = "insufficient_data"
            change = 0.0

        return {
            "trend": trend,
            "change_percent": change * 100,
            "avg_quality": round(avg_quality, 2),
            "samples": len(qualities),
            "dimensions": self.get_dimension_averages(recent_signals)
        }

    def get_dimension_averages(self, signals: List[Dict] = None) -> Dict[str, float]:
        """Get average scores per dimension"""
        if signals is None:
            signals = self.quality_signals[-100:]

        if not signals:
            return self.dimensions.copy()

        averages = {}
        for dim in self.dimensions:
            values = [s["dimensions"].get(dim, 0) for s in signals]
            averages[dim] = round(statistics.mean(values), 2) if values else 0.0

        return averages

    def get_stats(self) -> Dict[str, Any]:
        """Get quality statistics"""
        recent = self.quality_signals[-100:] if self.quality_signals else []

        return {
            "total_signals": len(self.quality_signals),
            "total_feedback": len(self.user_feedback),
            "avg_quality": statistics.mean([s["quality"] for s in recent]) if recent else self.baseline_quality,
            "dimensions": self.get_dimension_averages(recent),
            "trend": self.get_quality_trend()
        }
