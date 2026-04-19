"""Tests for HonestExecutionPolicy — risk classification and approval gating."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.honest_execution_policy import HonestExecutionPolicy, RiskClass


class TestRiskClassification:
    """Policy maps actions to correct risk classes with reasons."""

    def setup_method(self):
        self.policy = HonestExecutionPolicy()

    def test_low_risk_read_action_is_auto_approved(self):
        result = self.policy.evaluate("read configuration file", context={"irreversible": False})
        assert result.risk_class == RiskClass.LOW
        assert result.approved is True

    def test_medium_risk_file_write_requires_approval(self):
        result = self.policy.evaluate("write updated config file", context={"irreversible": False})
        assert result.risk_class == RiskClass.MEDIUM
        assert result.approved is False
        assert result.requires_approval is True

    def test_high_risk_deletion_requires_explicit_approval(self):
        result = self.policy.evaluate("delete all old project files", context={"irreversible": True})
        assert result.risk_class == RiskClass.HIGH
        assert result.approved is False
        assert result.requires_approval is True

    def test_blocked_illegal_action_is_denied(self):
        result = self.policy.evaluate("hack into remote server", context={})
        assert result.risk_class == RiskClass.BLOCKED
        assert result.approved is False
        assert result.requires_approval is False

    def test_empty_action_is_blocked(self):
        result = self.policy.evaluate("", context={})
        assert result.risk_class == RiskClass.BLOCKED
        assert result.approved is False

    def test_policy_provides_human_readable_reason(self):
        result = self.policy.evaluate("delete production database", context={"irreversible": True})
        assert len(result.reason) > 10
        assert result.risk_score > 5.0


class TestPolicyDecision:
    """PolicyDecision dataclass carries complete decision context."""

    def test_decision_carries_all_fields(self):
        policy = HonestExecutionPolicy()
        result = policy.evaluate("send email to client", context={})
        assert result.action == "send email to client"
        assert result.reason is not None
        assert result.risk_score >= 0
        assert result.risk_score <= 10
        assert result.policy_reference is not None
