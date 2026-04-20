# ==========================================================
# JARVIS v9.0 - Core Orchestrator
# Main orchestration logic extracted from main.py
# ==========================================================

import os
import sys
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# Core imports
from core.speculative_decoder import SpeculativeDecoder
from core.system2_thinking import System2Thinking
from core.local_llm_fallback import HybridLLMManager
from core.first_principles import FirstPrinciples
from core.hyper_automation import HyperAutomation
from core.rapid_iteration import RapidIteration
from core.optimization_engine import OptimizationEngine
from core.autonomous_decision import AutonomousDecision
from core.skill_loader import SkillLoader
from core.quality_scorer import QualityScorer
from core.profiler import Profiler
from core.skill_graph import SkillGraph
from core.workflow_synth import WorkflowSynthesizer
from core.self_evolving_architecture import SEAController
from core.security_system import (
    security_manager,
    input_validator,
    security_middleware,
)
from core.error_handling import (
    with_circuit_breaker,
    with_bulkhead,
    with_resilience,
    with_resource_pool,
    error_handler
)

# Memory imports
from memory.memory_controller import MemoryController

logger = logging.getLogger(__name__)


class JarvisV9Orchestrator:
    """
    JARVIS v9.0 ULTRA Main Orchestrator
    - Integrates all PhD-level systems
    - Elon Musk-style features
    - 10x performance improvements
    """

    def __init__(self):
        logger.info("🚀 Initializing JARVIS v9.0 ULTRA...")

        # Load environment
        from dotenv import load_dotenv
        load_dotenv()

        # Initialize core systems
        self.llm_manager = HybridLLMManager()
        self.speculative_decoder = SpeculativeDecoder()
        self.system2 = System2Thinking()

        # Initialize memory
        self.memory = MemoryController()

        # Initialize Elon Musk features
        self.first_principles = FirstPrinciples()
        self.hyper_automation = HyperAutomation()
        self.rapid_iteration = RapidIteration()
        self.optimization = OptimizationEngine()
        self.autonomous = AutonomousDecision()

        # Initialize skill loader (uses SKILLS_PATH from .env or defaults to ./skills)
        self.skill_loader = SkillLoader()
        stats = self.skill_loader.get_stats()
        logger.info(f"📚 Loaded {stats['total_skills']} Antigravity skills from {self.skill_loader.skills_path}")

        # Initialize skill graph and workflow synthesizer
        self.skill_graph = SkillGraph()
        self.workflow_synth = WorkflowSynthesizer(self.skill_graph)
        logger.info(f"🕷️ Skill Graph built: {self.skill_graph.get_stats()['total_skills']} nodes, {self.skill_graph.get_stats()['total_edges']} edges")
        logger.info("🔬 Workflow Synthesizer initialized")

        # Initialize quality scorer and profiler
        self.quality_scorer = QualityScorer()
        self.profiler = Profiler()
        logger.info("📊 Quality Scorer and Profiler initialized")

        # Initialize Enhanced Autonomy System
        from enhanced_autonomy import EnhancedAutonomySystem
        self.autonomy_system = EnhancedAutonomySystem(skill_loader=self.skill_loader)
        logger.info("🤖 Enhanced Autonomy System integrated")

        # Initialize Self-Evolving Architecture (SEA) System
        self.sea_controller = SEAController(self)
        logger.info("🧬 Self-Evolving Architecture (SEA) System integrated")

        # Initialize Security System (PhD Level - Phase 1)
        self.security_manager = security_manager
        self.input_validator = input_validator
        self.security_middleware = security_middleware
        logger.info("🔒 Security System initialized with JWT authentication and RBAC")

        # Configuration state (Enhanced - Fix 15)
        self.config = {
            "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", 100)),
            "request_timeout": int(os.getenv("REQUEST_TIMEOUT", 30)),
            "retry_attempts": int(os.getenv("RETRY_ATTEMPTS", 3)),
            "health_check_enabled": os.getenv("HEALTH_CHECK_ENABLED", "true").lower() == "true",
            "metrics_collection_enabled": os.getenv("METRICS_COLLECTION_ENABLED", "true").lower() == "true",
            "autonomous_mode": os.getenv("AUTONOMOUS_MODE", "false").lower() == "true",
            "sea_enabled": os.getenv("SEA_ENABLED", "true").lower() == "true",
            "security_enabled": True,
            "jwt_secret_set": bool(self.security_manager.secret_key)
        }

        # System state (Enhanced - Fix 15)
        self.start_time = datetime.now()
        self.request_count = 0
        self.last_request_time = None
        self.total_processing_time = 0.0
        self.error_count = 0
        self.success_count = 0
        self.uptime_seconds = 0

        # Component health tracking
        self.component_health = {
            "llm_manager": True,
            "speculative_decoder": True,
            "system2_thinking": True,
            "memory": True,
            "first_principles": True,
            "hyper_automation": True,
            "rapid_iteration": True,
            "optimization_engine": True,
            "autonomous_decision": True,
            "skill_loader": True,
            "quality_scorer": True,
            "profiler": True,
            "sea_controller": True
        }

        # Performance metrics
        self.performance_metrics = {
            "active_requests": 0,
            "avg_response_time_ms": 0.0,
            "p95_response_time_ms": 0.0,
            "p99_response_time_ms": 0.0
        }

        # Degraded mode flag
        self.degraded_mode = False

        logger.info("✅ JARVIS v9.0 ULTRA initialized successfully")

    async def process_message(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a message through the full JARVIS pipeline"""
        start_time = datetime.now()
        self.request_count += 1
        self.last_request_time = start_time
        self.performance_metrics["active_requests"] += 1

        try:
            # Input validation
            if not self.input_validator.validate_input(message, 'general'):
                self.error_count += 1
                return {"error": "Invalid input", "success": False}

            # Use speculative decoding for faster response
            response = await self.speculative_decoder.decode(message, context or {})

            # Track success
            self.success_count += 1
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.total_processing_time += processing_time

            return {
                "success": True,
                "response": response,
                "processing_time_ms": processing_time
            }

        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing message: {e}")
            return {"error": str(e), "success": False}

        finally:
            self.performance_metrics["active_requests"] -= 1

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        total_success = self.success_count
        total_errors = self.error_count
        total_requests = total_errors + total_success

        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 100.0
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0

        # Calculate avg response time if available
        avg_response_time = (self.total_processing_time / total_success) if total_success > 0 else 0.0

        # Overall system health determination
        overall_health = all(self.component_health.values()) and success_rate >= 95.0

        return {
            "overall_health": overall_health,
            "status": "healthy" if overall_health else "degraded",
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "successful_requests": total_success,
            "failed_requests": total_errors,
            "success_rate_percent": success_rate,
            "error_rate_percent": error_rate,
            "average_response_time_ms": avg_response_time,
            "active_requests": self.performance_metrics.get("active_requests", 0),
            "components": self.component_health,
            "timestamp": datetime.now().isoformat(),
            "version": "9.0.0",
            "degraded_mode": self.degraded_mode
        }

    @with_resilience(component='optimization', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
    async def optimize_system(self):
        """Run system optimization"""
        logger.info("⚡ Running system optimization...")

        # Get current performance
        stats = self.get_system_stats()

        # Detect bottlenecks using profiler
        bottlenecks = self.profiler.get_bottlenecks(hours=1)
        if bottlenecks:
            logger.info(f"🐌 Found {len(bottlenecks)} bottlenecks")
            for bn in bottlenecks[:3]:
                logger.info(f"   - {bn['operation']}: {bn['latency_ms']:.2f}ms")
                logger.info(f"     Suggestion: {bn['suggestion']}")

        # Get quality trends
        quality_trend = self.quality_scorer.get_quality_trend(hours=1)
        logger.info(f"📊 Quality trend: {quality_trend['trend']} (avg: {quality_trend['avg_quality']:.2f})")

        return {
            "success": True,
            "stats": stats,
            "bottlenecks": bottlenecks,
            "quality_trend": quality_trend
        }
