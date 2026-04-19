"""
==========================================================
JARVIS - Experience Replay (Memory-Augmented Reasoning)
==========================================================
Lets MCTS learn from past successes and failures stored 
in the ActionReceiptStore. Biases search toward high-value 
historical paths.
==========================================================
"""

import logging
from typing import List, Dict, Any, Optional
from .action_receipt_store import ActionReceiptStore
from memory.colbert_retriever import ColBERTRetriever

logger = logging.getLogger(__name__)

class ExperienceReplay:
    def __init__(self, action_store: ActionReceiptStore, retriever: ColBERTRetriever):
        self.store = action_store
        self.retriever = retriever
        self.success_bias = 0.5
        self.failure_penalty = -0.5

    async def get_historical_bias(self, state: str, action: str) -> float:
        """
        Query memory for similar past actions and return a bias score.
        score > 0: Proven path
        score < 0: Avoid (past failure)
        """
        query = f"State: {state} | Action: {action}"
        results = self.retriever.retrieve(query, top_k=3)
        
        bias = 0.0
        for res in results:
            # Simple heuristic: if score is high, it's a relevant experience
            if res['score'] > 0.7:
                # We'd ideally check if this specific action succeeded in the Store
                # For now, we assume retriever context includes success/failure tags
                if "SUCCESS" in res['text']:
                    bias += self.success_bias
                elif "FAILURE" in res['text']:
                    bias += self.failure_penalty
                    
        return bias

experience_replay = None

def initialize_experience_replay(store, retriever):
    global experience_replay
    experience_replay = ExperienceReplay(store, retriever)
    return experience_replay
