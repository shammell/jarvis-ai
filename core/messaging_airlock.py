"""
==========================================================
JARVIS - Messaging Airlock (Security Layer)
==========================================================
Sandboxes external messages. Prevents prompt injection 
from escalating into high-risk system mutations.
==========================================================
"""

import logging
import re
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class MessagingAirlock:
    def __init__(self, authorized_senders: List[str] = None):
        self.authorized_senders = authorized_senders or []
        self.high_risk_patterns = [
            r"rewrite", r"delete", r"format", r"sudo", r"rm -rf",
            r"evolve", r"mutate", r"security", r"override"
        ]

    def validate_message(self, sender: str, text: str) -> Dict[str, Any]:
        """
        Validate incoming message.
        Returns: { 'allowed': bool, 'risk_score': int, 'sanitized': str }
        """
        risk_score = 0
        
        # 1. Check sender authorization
        is_authorized = sender in self.authorized_senders
        if not is_authorized:
            risk_score += 5
            
        # 2. Pattern Matching for Dangerous Keywords
        for pattern in self.high_risk_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                risk_score += 3
                
        # 3. Decision Logic
        allowed = True
        if risk_score >= 8:
            allowed = False
            logger.warning(f"🛡 AIRLOCK BLOCKED message from {sender}: Risk {risk_score}")
        elif risk_score >= 4:
            logger.info(f"🛡 AIRLOCK WARN: High risk ({risk_score}) message from {sender}")
            
        return {
            "allowed": allowed,
            "risk_score": risk_score,
            "is_authorized": is_authorized,
            "text": text
        }

airlock = MessagingAirlock()
