# ==========================================================
# JARVIS v12.0 SINGULARITY - Emotional & Cognitive Synchronization
# AI adapts to the user's emotional state and cognitive load
# ==========================================================

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class CognitiveSyncEngine:
    """
    Analyzes user sentiment, typing cadence (simulated), and phrasing 
    to dynamically adjust JARVIS's tone, verbosity, and complexity.
    """
    
    def __init__(self):
        self.user_state = {
            "stress_level": 0.5,  # 0 to 1
            "cognitive_load": "medium",  # low, medium, high
            "primary_emotion": "neutral"
        }
        logger.info("❤️ Cognitive & Emotional Synchronization active. JARVIS is now empathetic.")

    def analyze_user_input(self, text: str, typing_speed: float = 1.0) -> None:
        """
        Updates the internal model of the user's current state.
        """
        # Simulated analysis
        text_lower = text.lower()
        if "urgent" in text_lower or "hurry" in text_lower or "fuck" in text_lower:
            self.user_state["stress_level"] = 0.9
            self.user_state["primary_emotion"] = "anxious/frustrated"
        elif "explain" in text_lower or "how" in text_lower:
            self.user_state["cognitive_load"] = "high"
            self.user_state["primary_emotion"] = "curious"
        else:
            self.user_state["stress_level"] = max(0.1, self.user_state["stress_level"] - 0.1)
            
        logger.info(f"🧠 User State Updated: Stress {self.user_state['stress_level']:.1f}, Emotion: {self.user_state['primary_emotion']}")

    def format_response(self, base_response: str) -> str:
        """
        Adjusts the output based on the user's cognitive state.
        """
        if self.user_state["stress_level"] > 0.7:
            # User is stressed: be extremely concise, skip pleasantries, provide immediate solutions.
            return f"⚡ [Priority Mode] {base_response.split('.')[0]}."
            
        if self.user_state["cognitive_load"] == "high":
            # User wants to learn: be verbose, use analogies, break down steps.
            return f"📚 [Tutorial Mode] Let's break this down:\n1. {base_response}\nDoes that make sense?"
            
        # Default neutral
        return base_response

if __name__ == "__main__":
    sync = CognitiveSyncEngine()
    
    sync.analyze_user_input("Bro this is urgent the server is down fix it now!!")
    print(sync.format_response("I have identified the issue. It was a memory leak in the redis cache. I restarted it."))
    
    sync.analyze_user_input("How exactly does quantum entanglement work?")
    print(sync.format_response("Quantum entanglement is when two particles link together so that a change in one immediately affects the other."))
