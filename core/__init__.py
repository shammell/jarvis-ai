"""
JARVIS v9.0 ULTRA - Package Initialization
"""

__version__ = "9.0.0"
__author__ = "JARVIS Team"
__description__ = "PhD-Level AI Assistant with Elon Musk-Style Features"

# Core exports
from core.speculative_decoder import SpeculativeDecoder
from core.system2_thinking import System2Thinking
from core.local_llm_fallback import HybridLLMManager
from core.first_principles import FirstPrinciples
from core.hyper_automation import HyperAutomation
from core.rapid_iteration import RapidIteration
from core.optimization_engine import OptimizationEngine
from core.autonomous_decision import AutonomousDecision
from core.self_evolving_architecture import SEAController

# Memory exports
from memory.memory_controller import MemoryController
from memory.graph_rag import GraphRAG
from memory.colbert_retriever import ColBERTRetriever

__all__ = [
    "SpeculativeDecoder",
    "System2Thinking",
    "HybridLLMManager",
    "FirstPrinciples",
    "HyperAutomation",
    "RapidIteration",
    "OptimizationEngine",
    "AutonomousDecision",
    "SEAController",
    "MemoryController",
    "GraphRAG",
    "ColBERTRetriever",
]
