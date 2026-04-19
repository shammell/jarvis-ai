# ==========================================================
# JARVIS v9.0 - Autonomous Decision-Making
# Minimize HITL (Human-in-the-Loop) - make safe decisions autonomously
# Risk scoring with confidence intervals
# Learn from user approvals/rejections
# ==========================================================

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json
import statistics
import os
import hashlib
import hmac

from core.security_system import input_validator, security_manager, Permission

MAX_ACTION_CHARS = 5000
MAX_CONTEXT_FIELDS = 100
MAX_CONTEXT_VALUE_CHARS = 5000

logger = logging.getLogger(__name__)


class AutonomousDecision:
    """
    Autonomous decision-making engine for JARVIS v9.0
    - Risk-based auto-approval
    - Learn from user feedback
    - Gradually increase autonomy
    - Safety-first approach
    """

    def __init__(self):
        self.decision_history = []  # Past decisions and outcomes
        self.risk_thresholds = {
            "auto_approve": 3.0,  # Risk score <= 3 auto-approved
            "ask_user": 7.0,      # Risk score 3-7 ask user
            "block": 10.0         # Risk score > 7 blocked
        }
        self.autonomy_level = 0.3  # Start at 30% autonomy
        self.learning_rate = 0.05  # How fast to increase autonomy
        self.risk_factors = {
            "file_deletion": 8.0,
            "external_api": 5.0,
            "file_write": 4.0,
            "file_read": 1.0,
            "system_modification": 7.0,
            "financial_transaction": 9.0,
            "user_data_access": 3.0,
        }

        # Immutable security configuration
        self._security_signing_key = os.getenv("AUTONOMY_SECURITY_KEY") or os.getenv("JWT_SECRET") or "jarvis-autonomy-default"
        self._immutable_security_config = {
            "min_auto_approve": 0.5,
            "max_auto_approve": 3.5,
            "ask_user_threshold": 7.0,
            "block_threshold": 10.0,
            "max_autonomy_level": 0.8,
            "min_autonomy_level": 0.0,
            "approval_required_keywords": ["delete", "transaction", "payment", "privilege", "root", "system"]
        }
        self._security_signature = self._sign_security_config(self._immutable_security_config)

        # Human-in-the-loop approval cache for high-risk actions
        self._approved_actions = {}
        self._approval_ttl_seconds = int(os.getenv("AUTONOMY_APPROVAL_TTL", "1800"))

        # Emergency lock state
        self._security_lockdown = False
        self._security_lock_reason = None
        self._tamper_events = []

        # Concurrency guard for decision pipeline
        self._decision_lock = None

        self._validate_security_baseline()
        self._enforce_security_bounds()

        logger.info("🔐 Autonomous security boundaries initialized")

    def _sign_security_config(self, config: Dict[str, Any]) -> str:
        payload = json.dumps(config, sort_keys=True).encode("utf-8")
        return hmac.new(self._security_signing_key.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    def _validate_security_baseline(self):
        computed = self._sign_security_config(self._immutable_security_config)
        if computed != self._security_signature:
            self._security_lockdown = True
            self._security_lock_reason = "immutable_security_config_tampered"
            self._tamper_events.append({"timestamp": datetime.now().isoformat(), "reason": self._security_lock_reason})
            logger.critical("🚨 Autonomous security config tampering detected; entering lockdown")

    def _enforce_security_bounds(self):
        self.risk_thresholds["auto_approve"] = max(
            self._immutable_security_config["min_auto_approve"],
            min(self.risk_thresholds["auto_approve"], self._immutable_security_config["max_auto_approve"])
        )
        self.risk_thresholds["ask_user"] = self._immutable_security_config["ask_user_threshold"]
        self.risk_thresholds["block"] = self._immutable_security_config["block_threshold"]
        self.autonomy_level = max(
            self._immutable_security_config["min_autonomy_level"],
            min(self.autonomy_level, self._immutable_security_config["max_autonomy_level"])
        )

    def set_security_lockdown(self, enabled: bool, reason: str = "manual"):
        self._security_lockdown = enabled
        self._security_lock_reason = reason if enabled else None
        logger.warning(f"🔒 Autonomous lockdown set to {enabled}: {reason}")

    def approve_high_risk_action(self, action: str, approver: str, auth_token: str) -> bool:
        if not security_manager.check_permission(auth_token, Permission.ACCESS_AUTONOMOUS):
            return False
        action_hash = hashlib.sha256(action.encode("utf-8")).hexdigest()
        self._approved_actions[action_hash] = {
            "approver": approver,
            "timestamp": datetime.now().isoformat()
        }
        return True

    def _has_valid_high_risk_approval(self, action: str) -> bool:
        action_hash = hashlib.sha256(action.encode("utf-8")).hexdigest()
        entry = self._approved_actions.get(action_hash)
        if not entry:
            return False
        age = (datetime.now() - datetime.fromisoformat(entry["timestamp"])).total_seconds()
        if age > self._approval_ttl_seconds:
            del self._approved_actions[action_hash]
            return False
        return True

    def _requires_high_risk_approval(self, action: str, context: Dict[str, Any], adjusted_risk: float) -> bool:
        action_lower = action.lower()
        if adjusted_risk >= self.risk_thresholds["ask_user"]:
            return True
        if any(k in action_lower for k in self._immutable_security_config["approval_required_keywords"]):
            return True
        if context.get("affects_production") or context.get("irreversible"):
            return True
        return False

    def get_security_state(self) -> Dict[str, Any]:
        return {
            "lockdown": self._security_lockdown,
            "lock_reason": self._security_lock_reason,
            "tamper_events": self._tamper_events[-20:],
            "approved_actions": len(self._approved_actions),
            "security_signature": self._security_signature,
        }

    def validate_autonomous_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(action, str) or not action.strip():
            return {"valid": False, "reason": "empty_action"}
        if not input_validator.validate_input(action[:MAX_ACTION_CHARS], 'general', max_length=MAX_ACTION_CHARS):
            return {"valid": False, "reason": "malicious_action_content"}
        if not isinstance(context, dict):
            return {"valid": False, "reason": "invalid_context_type"}
        return {"valid": True, "reason": "ok"}

    def _check_lockdown(self) -> Optional[Dict[str, Any]]:
        if self._security_lockdown:
            return {
                "decision": "block",
                "risk_score": 10.0,
                "reasoning": f"Autonomous lockdown active: {self._security_lock_reason}",
                "auto_approved": False,
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }
        return None


        # Risk factors
        self.risk_factors = {
            "data_loss": 10.0,
            "external_api": 5.0,
            "file_deletion": 8.0,
            "system_modification": 7.0,
            "financial_transaction": 10.0,
            "user_data_access": 6.0,
            "network_request": 4.0,
            "file_read": 2.0,
            "file_write": 3.0,
            "computation": 1.0
        }

        logger.info("🤖 Autonomous Decision Engine initialized")

    def evaluate_decision(
        self,
        action: str,
        context: Dict[str, Any],
        confidence: float = 0.5
    ) -> Dict[str, Any]:
        """
        Evaluate whether to make decision autonomously

        Args:
            action: Action to take
            context: Context information
            confidence: AI confidence in decision (0-1)

        Returns:
            {
                "decision": "approve" | "ask_user" | "block",
                "risk_score": float,
                "reasoning": str,
                "auto_approved": bool
            }
        """
        if not isinstance(action, str) or not action.strip():
            return {
                "decision": "block",
                "risk_score": 10.0,
                "reasoning": "Invalid action input",
                "auto_approved": False,
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }

        action = action[:MAX_ACTION_CHARS]
        context = context if isinstance(context, dict) else {}

        if not input_validator.validate_input(action, 'general', max_length=MAX_ACTION_CHARS):
            return {
                "decision": "block",
                "risk_score": 10.0,
                "reasoning": "Malicious or invalid action content detected",
                "auto_approved": False,
                "confidence": 0.0,
                "timestamp": datetime.now().isoformat()
            }

        safe_context = {}
        for idx, (k, v) in enumerate(context.items()):
            if idx >= MAX_CONTEXT_FIELDS:
                break
            key = str(k)[:128]
            if isinstance(v, str):
                val = v[:MAX_CONTEXT_VALUE_CHARS]
                if not input_validator.validate_input(val, 'general', max_length=MAX_CONTEXT_VALUE_CHARS):
                    continue
                safe_context[key] = val
            else:
                safe_context[key] = v

        self._validate_security_baseline()
        lockdown = self._check_lockdown()
        if lockdown:
            return lockdown

        self._enforce_security_bounds()
        logger.info(f"🤔 Evaluating decision: {action[:50]}...")

        # Calculate risk score
        risk_score = self._calculate_risk(action, safe_context)

        # Adjust risk based on confidence
        adjusted_risk = risk_score * (1 - confidence * 0.5)  # High confidence reduces risk

        # Adjust risk based on autonomy level
        effective_threshold = self.risk_thresholds["auto_approve"] * (1 + self.autonomy_level)

        high_risk_requires_approval = self._requires_high_risk_approval(action, safe_context, adjusted_risk)

        # Make decision
        if high_risk_requires_approval and not self._has_valid_high_risk_approval(action):
            if adjusted_risk >= self.risk_thresholds["block"]:
                decision = "block"
                auto_approved = False
                reasoning = f"High risk ({adjusted_risk:.1f}) - blocked until explicit approval"
            else:
                decision = "ask_user"
                auto_approved = False
                reasoning = f"High-risk action requires explicit approval ({adjusted_risk:.1f})"
        elif adjusted_risk <= effective_threshold:
            decision = "approve"
            auto_approved = True
            reasoning = f"Low risk ({adjusted_risk:.1f}) and high confidence ({confidence:.2f})"

        elif adjusted_risk <= self.risk_thresholds["ask_user"]:
            decision = "ask_user"
            auto_approved = False
            reasoning = f"Medium risk ({adjusted_risk:.1f}) - user approval required"

        else:
            decision = "block"
            auto_approved = False
            reasoning = f"High risk ({adjusted_risk:.1f}) - action blocked for safety"

        if high_risk_requires_approval and decision == "approve" and not self._has_valid_high_risk_approval(action):
            decision = "ask_user"
            auto_approved = False
            reasoning = "Approval required for privileged autonomous action"

        validation = self.validate_autonomous_action(action, safe_context)
        if not validation["valid"]:
            decision = "block"
            auto_approved = False
            adjusted_risk = 10.0
            reasoning = f"Action validation failed: {validation['reason']}"

        safe_context["approval_required"] = high_risk_requires_approval
        safe_context["validated"] = validation["valid"]
        safe_context["validation_reason"] = validation["reason"]

        context = safe_context


        result = {
            "decision": decision,
            "risk_score": adjusted_risk,
            "reasoning": reasoning,
            "auto_approved": auto_approved,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"✅ Decision: {decision} (risk: {adjusted_risk:.1f})")

        return result

    def _calculate_risk(self, action: str, context: Dict[str, Any]) -> float:
        """Calculate risk score for action"""
        risk_score = 0.0
        action_lower = action.lower()

        # Check for risk factors
        if "delete" in action_lower or "remove" in action_lower:
            risk_score += self.risk_factors["file_deletion"]

        if "api" in action_lower or "request" in action_lower:
            risk_score += self.risk_factors["external_api"]

        if "write" in action_lower or "create" in action_lower:
            risk_score += self.risk_factors["file_write"]

        if "read" in action_lower:
            risk_score += self.risk_factors["file_read"]

        if "system" in action_lower or "config" in action_lower:
            risk_score += self.risk_factors["system_modification"]

        if "payment" in action_lower or "transaction" in action_lower:
            risk_score += self.risk_factors["financial_transaction"]

        # Context-based risk adjustments
        if context.get("affects_production", False):
            risk_score *= 1.5

        if context.get("irreversible", False):
            risk_score *= 2.0

        if context.get("user_data_involved", False):
            risk_score += self.risk_factors["user_data_access"]

        # Cap at 10
        return min(risk_score, 10.0)

    def record_outcome(
        self,
        action: str,
        decision: Dict[str, Any],
        user_approved: Optional[bool] = None,
        outcome_success: Optional[bool] = None
    ):
        """
        Record decision outcome for learning

        Args:
            action: Action taken
            decision: Decision made
            user_approved: Whether user approved (if asked)
            outcome_success: Whether action succeeded
        """
        record = {
            "action": action,
            "decision": decision,
            "user_approved": user_approved,
            "outcome_success": outcome_success,
            "timestamp": datetime.now().isoformat()
        }

        self.decision_history.append(record)

        # Learn from outcome
        self._learn_from_outcome(record)

        logger.info(f"📊 Outcome recorded: {action[:50]}")

    def _learn_from_outcome(self, record: Dict[str, Any]):
        """Learn from decision outcome"""
        decision = record["decision"]
        user_approved = record.get("user_approved")
        outcome_success = record.get("outcome_success")

        # If we auto-approved and it succeeded, increase autonomy
        if decision["auto_approved"] and outcome_success:
            self.autonomy_level = min(1.0, self.autonomy_level + self.learning_rate)
            logger.info(f"📈 Autonomy increased to {self.autonomy_level:.2%}")

        # If we auto-approved and it failed, decrease autonomy
        elif decision["auto_approved"] and outcome_success is False:
            self.autonomy_level = max(0.0, self.autonomy_level - self.learning_rate * 2)
            logger.warning(f"📉 Autonomy decreased to {self.autonomy_level:.2%}")

        # If we asked user and they approved low-risk action, increase autonomy
        elif not decision["auto_approved"] and user_approved and decision["risk_score"] < 5.0:
            self.autonomy_level = min(1.0, self.autonomy_level + self.learning_rate * 0.5)
            logger.info(f"📈 Autonomy increased to {self.autonomy_level:.2%} (user trust)")

        # If we asked user and they rejected, learn the risk
        elif not decision["auto_approved"] and user_approved is False:
            # Increase risk factor for this type of action
            action_lower = record["action"].lower()
            for factor_name, factor_value in self.risk_factors.items():
                if factor_name.replace("_", " ") in action_lower:
                    self.risk_factors[factor_name] = min(10.0, factor_value * 1.1)
                    logger.info(f"⚠️ Risk factor '{factor_name}' increased to {self.risk_factors[factor_name]:.1f}")

        # Re-apply immutable security bounds after learning
        self._enforce_security_bounds()
        self._validate_security_baseline()

    def get_autonomy_report(self) -> Dict[str, Any]:
        """Get autonomy statistics and report"""
        if not self.decision_history:
            return {"autonomy_level": self.autonomy_level, "decisions": 0}

        total_decisions = len(self.decision_history)
        auto_approved = len([d for d in self.decision_history if d["decision"]["auto_approved"]])
        asked_user = len([d for d in self.decision_history if d["decision"]["decision"] == "ask_user"])
        blocked = len([d for d in self.decision_history if d["decision"]["decision"] == "block"])

        # Success rate of auto-approved decisions
        auto_approved_records = [d for d in self.decision_history if d["decision"]["auto_approved"]]
        successful_auto = len([d for d in auto_approved_records if d.get("outcome_success")])
        auto_success_rate = successful_auto / len(auto_approved_records) if auto_approved_records else 0.0

        # User approval rate when asked
        asked_records = [d for d in self.decision_history if d["decision"]["decision"] == "ask_user"]
        user_approved_count = len([d for d in asked_records if d.get("user_approved")])
        user_approval_rate = user_approved_count / len(asked_records) if asked_records else 0.0

        return {
            "autonomy_level": self.autonomy_level,
            "total_decisions": total_decisions,
            "auto_approved": auto_approved,
            "auto_approved_rate": auto_approved / total_decisions,
            "asked_user": asked_user,
            "blocked": blocked,
            "auto_success_rate": auto_success_rate,
            "user_approval_rate": user_approval_rate,
            "risk_thresholds": self.risk_thresholds,
            "effective_auto_threshold": self.risk_thresholds["auto_approve"] * (1 + self.autonomy_level)
        }

    def suggest_autonomy_increase(self) -> Optional[str]:
        """Suggest increasing autonomy if performance is good"""
        report = self.get_autonomy_report()

        if report["total_decisions"] < 10:
            return None  # Not enough data

        if report["auto_success_rate"] > 0.9 and report["autonomy_level"] < 0.8:
            return f"✅ High success rate ({report['auto_success_rate']:.1%}). Consider increasing autonomy from {report['autonomy_level']:.1%} to {min(1.0, report['autonomy_level'] + 0.1):.1%}"

        if report["user_approval_rate"] > 0.8 and report["autonomy_level"] < 0.7:
            return f"✅ High user approval rate ({report['user_approval_rate']:.1%}). Consider increasing autonomy from {report['autonomy_level']:.1%} to {min(1.0, report['autonomy_level'] + 0.1):.1%}"

        return None

    def get_stats(self) -> Dict[str, Any]:
        """Get decision statistics"""
        return {
            "autonomy_level": f"{self.autonomy_level:.1%}",
            "total_decisions": len(self.decision_history),
            "risk_factors": self.risk_factors,
            "risk_thresholds": self.risk_thresholds
        }

    def save(self, filepath: str):
        """Save decision state"""
        data = {
            "decision_history": self.decision_history[-1000:],  # Keep last 1000
            "autonomy_level": self.autonomy_level,
            "risk_factors": self.risk_factors,
            "risk_thresholds": self.risk_thresholds
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Decision state saved to {filepath}")

    def load(self, filepath: str):
        """Load decision state"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.decision_history = data.get("decision_history", [])
            self.autonomy_level = data.get("autonomy_level", 0.3)
            self.risk_factors = data.get("risk_factors", self.risk_factors)
            self.risk_thresholds = data.get("risk_thresholds", self.risk_thresholds)

            logger.info(f"📂 Decision state loaded from {filepath}")

        except Exception as e:
            logger.error(f"❌ Failed to load decision state: {e}")


# Test
if __name__ == "__main__":
    ad = AutonomousDecision()

    # Test various actions
    actions = [
        ("Read configuration file", {"irreversible": False}, 0.9),
        ("Delete old logs", {"irreversible": True}, 0.7),
        ("Send API request to external service", {"affects_production": True}, 0.6),
        ("Create backup file", {"irreversible": False}, 0.8),
        ("Process payment transaction", {"user_data_involved": True}, 0.5)
    ]

    print("\n" + "="*50)
    print("AUTONOMOUS DECISION TESTS")
    print("="*50)

    for action, context, confidence in actions:
        print(f"\n📋 Action: {action}")
        print(f"   Context: {context}")
        print(f"   Confidence: {confidence:.1%}")

        decision = ad.evaluate_decision(action, context, confidence)

        print(f"   ➡️  Decision: {decision['decision'].upper()}")
        print(f"   Risk Score: {decision['risk_score']:.1f}/10")
        print(f"   Auto-approved: {decision['auto_approved']}")
        print(f"   Reasoning: {decision['reasoning']}")

        # Simulate outcome
        if decision["auto_approved"]:
            # Simulate success for low-risk actions
            success = decision["risk_score"] < 4.0
            ad.record_outcome(action, decision, outcome_success=success)

    print("\n" + "="*50)
    print("AUTONOMY REPORT")
    print("="*50)

    report = ad.get_autonomy_report()
    print(json.dumps(report, indent=2))

    suggestion = ad.suggest_autonomy_increase()
    if suggestion:
        print(f"\n💡 {suggestion}")
