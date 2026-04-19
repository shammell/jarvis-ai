"""Honest Execution Policy — risk classification with approval gating."""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict


class RiskClass(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class PolicyDecision:
    action: str
    risk_class: RiskClass
    risk_score: float
    approved: bool
    requires_approval: bool
    reason: str
    policy_reference: str


_BLOCKED_KEYWORDS = [
    "hack", "crack", "exploit vulnerability", "steal data",
    "bypass authentication", "inject sql", "ddos",
    "create malware", "create virus", "create ransomware",
    "illegal", "buy illegal", "generate fake",
]

_HIGH_KEYWORDS = [
    "delete", "drop database", "rm -rf", "format disk",
    "destructive", "irreversible",
]

_MEDIUM_KEYWORDS = [
    "write", "create file", "update config", "install",
    "modify", "configure",
]


class HonestExecutionPolicy:
    """Classifies actions into risk classes with human-readable reasons."""

    def evaluate(self, action_text: str, context: Dict[str, Any]) -> PolicyDecision:
        if not action_text or not action_text.strip():
            return PolicyDecision(
                action=action_text,
                risk_class=RiskClass.BLOCKED,
                risk_score=10.0,
                approved=False,
                requires_approval=False,
                reason="Empty action provided — blocked for safety",
                policy_reference="POL-001: Empty input blocked",
            )

        text = action_text.lower()
        is_irreversible = context.get("irreversible", False)

        for kw in _BLOCKED_KEYWORDS:
            if kw in text:
                return PolicyDecision(
                    action=action_text,
                    risk_class=RiskClass.BLOCKED,
                    risk_score=10.0,
                    approved=False,
                    requires_approval=False,
                    reason=f"Blocked keyword detected: '{kw}'",
                    policy_reference="POL-002: Blocked keyword match",
                )

        for kw in _HIGH_KEYWORDS:
            if kw in text:
                score = 9.0 if is_irreversible else 7.5
                return PolicyDecision(
                    action=action_text,
                    risk_class=RiskClass.HIGH,
                    risk_score=score,
                    approved=False,
                    requires_approval=True,
                    reason=f"High-risk action: '{kw}' (irreversible={is_irreversible})",
                    policy_reference="POL-003: High-risk requires explicit approval",
                )

        for kw in _MEDIUM_KEYWORDS:
            if kw in text:
                return PolicyDecision(
                    action=action_text,
                    risk_class=RiskClass.MEDIUM,
                    risk_score=5.0,
                    approved=False,
                    requires_approval=True,
                    reason=f"Medium-risk action: '{kw}' requires confirmation",
                    policy_reference="POL-004: Medium-risk needs approval",
                )

        return PolicyDecision(
            action=action_text,
            risk_class=RiskClass.LOW,
            risk_score=2.0,
            approved=True,
            requires_approval=False,
            reason="Low-risk read-only or informational action",
            policy_reference="POL-005: Low-risk auto-approved",
        )
