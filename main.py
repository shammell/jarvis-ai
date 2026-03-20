# ==========================================================
# JARVIS v9.0 - Main Orchestrator
# Integrates all v9.0 ULTRA components
# ==========================================================

import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Fix Windows console encoding for emoji support
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

# Memory imports
from memory.memory_controller import MemoryController

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/jarvis_v9.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
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

        # System state
        self.start_time = datetime.now()
        self.request_count = 0

        logger.info("✅ JARVIS v9.0 ULTRA initialized successfully")

        # Note: Autonomous startup will be triggered when async context is available
        # Use jarvis_autonomous.py for standalone autonomous mode

        # Activate Self-Evolving Architecture
        try:
            self.sea_controller.activate()
            logger.info("🚀 Self-Evolving Architecture activated")
        except Exception as e:
            logger.error(f"❌ SEA activation failed: {e}")

    async def process_message(
        self,
        message: str,
        context: Dict[str, Any] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Process incoming message with full v9.0 capabilities

        Args:
            message: User message
            context: Additional context
            user_id: User identifier

        Returns:
            Response with metadata
        """
        start_time = datetime.now()
        self.request_count += 1

        logger.info(f"📨 Processing message: {message[:50]}...")

        # Monitor this function through SEA
        if hasattr(self, 'sea_controller'):
            monitored_process = self.sea_controller.monitor_function(self._process_message_impl)
            return await monitored_process(message, context, user_id)
        else:
            return await self._process_message_impl(message, context, user_id)

    async def _process_message_impl(
        self,
        message: str,
        context: Dict[str, Any] = None,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        Implementation of process_message with full v9.0 capabilities

        Args:
            message: User message
            context: Additional context
            user_id: User identifier

        Returns:
            Response with metadata
        """
        start_time = datetime.now()
        self.request_count += 1

        logger.info(f"📨 Processing message: {message[:50]}...")

        try:
            # Step 1: Match relevant skills (profiled)
            with self.profiler.profile("skill_matching", "orchestrator"):
                matched_skills = self.skill_loader.match_skills(message)
            if matched_skills:
                logger.info(f"🎯 Matched {len(matched_skills)} skills for query")
                for skill in matched_skills[:3]:
                    logger.info(f"  - {skill['name']} (score: {skill['score']})")

            # Step 2: Store in memory (profiled)
            with self.profiler.profile("memory_store", "memory"):
                self.memory.store(message, memory_type="conversation", metadata={
                    "user_id": user_id,
                    "timestamp": start_time.isoformat()
                })

            # Step 3: Retrieve relevant context (profiled)
            with self.profiler.profile("memory_retrieve", "memory"):
                relevant_memories = self.memory.retrieve(message, top_k=5)
            context_text = "\n".join([m["text"] for m in relevant_memories])

            # Step 4: Determine if complex reasoning needed
            is_complex = self._is_complex_query(message)

            # Step 5: Generate response (profiled)
            if is_complex:
                logger.info("🧠 Using System 2 thinking for complex query")
                with self.profiler.profile("system2_reason", "system2"):
                    response = await self._system2_response(message, context_text)
            else:
                logger.info("⚡ Using fast response with speculative decoding")
                with self.profiler.profile("llm_generate", "llm"):
                    response = await self._fast_response(message, context_text)

            # Step 6: Log task for automation detection
            self.hyper_automation.log_task(message, context)

            # Step 7: Calculate quality score
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            quality_signals = {
                "latency_ms": elapsed_ms,
                "source": response.get("source", "groq"),
                "matched_skills": len(matched_skills) if matched_skills else 0
            }
            quality_score = self.quality_scorer.calculate_quality(
                response=response,
                request={"message": message, "user_id": user_id},
                signals=quality_signals
            )

            # Step 8: Track performance with actual quality
            self.rapid_iteration.track_performance({
                "latency": elapsed_ms,
                "success_rate": 1.0,
                "quality": quality_score
            })

            # Step 8: Store response in memory
            self.memory.store(response["text"], memory_type="conversation", metadata={
                "user_id": user_id,
                "response_to": message[:100],
                "timestamp": datetime.now().isoformat(),
                "quality_score": quality_score
            })

            return {
                "text": response["text"],
                "metadata": {
                    "latency_ms": elapsed_ms,
                    "source": response.get("source", "groq"),
                    "complex_reasoning": is_complex,
                    "matched_skills": len(matched_skills) if matched_skills else 0,
                    "top_skill": matched_skills[0]['name'] if matched_skills else None,
                    "request_id": self.request_count,
                    "quality_score": quality_score
                }
            }

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return {
                "text": "I encountered an error processing your request. Please try again.",
                "metadata": {
                    "error": str(e),
                    "request_id": self.request_count
                }
            }

    async def stream_response(
        self,
        message: str,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Stream response tokens as they become available

        Args:
            message: User message
            user_id: User identifier
            context: Additional context

        Yields:
            Dictionary with token chunks and completion metadata
        """
        # Monitor this function through SEA
        if hasattr(self, 'sea_controller'):
            monitored_process = self.sea_controller.monitor_function(self._stream_response_impl)
            async for chunk in monitored_process(message, user_id, context):
                yield chunk
        else:
            async for chunk in self._stream_response_impl(message, user_id, context):
                yield chunk

    async def _stream_response_impl(
        self,
        message: str,
        user_id: str = None,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Stream response tokens as they become available

        Args:
            message: User message
            user_id: User identifier
            context: Additional context

        Yields:
            Dictionary with token chunks and completion metadata
        """
        start_time = datetime.now()
        self.request_count += 1

        logger.info(f"📨 Streaming message: {message[:50]}...")

        try:
            # Step 1: Match relevant skills (profiled)
            with self.profiler.profile("skill_matching", "orchestrator"):
                matched_skills = self.skill_loader.match_skills(message)
            if matched_skills:
                logger.info(f"🎯 Matched {len(matched_skills)} skills for query")

            # Step 2: Store in memory (profiled)
            with self.profiler.profile("memory_store", "memory"):
                self.memory.store(message, memory_type="conversation", metadata={
                    "user_id": user_id,
                    "timestamp": start_time.isoformat()
                })

            # Step 3: Retrieve relevant context (profiled)
            with self.profiler.profile("memory_retrieve", "memory"):
                relevant_memories = self.memory.retrieve(message, top_k=5)
            context_text = "\n".join([m["text"] for m in relevant_memories])

            # Step 4: Determine if complex reasoning needed
            is_complex = self._is_complex_query(message)

            # Step 5: Generate response with streaming capability
            if is_complex:
                logger.info("🧠 Using System 2 thinking for complex query")
                # For complex reasoning, we'll return complete result at once
                with self.profiler.profile("system2_reason", "system2"):
                    response = await self._system2_response(message, context_text)

                # Yield tokens in chunks for streaming
                response_text = response["text"]
                chunk_size = 10  # Adjust based on desired streaming granularity
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    yield {
                        "type": "token",
                        "content": chunk,
                        "metadata": {
                            "partial_response": True
                        }
                    }
            else:
                logger.info("⚡ Using streaming with speculative decoder")
                with self.profiler.profile("llm_generate", "llm"):
                    # Use the speculative decoder's streaming capability
                    messages = [
                        {"role": "system", "content": "You are JARVIS v9.0, an advanced AI assistant. Provide comprehensive, detailed responses."},
                        {"role": "user", "content": f"Context: {context_text}\n\nUser: {message}"}
                    ]

                    # Generate response with streaming support
                    async for token in self._stream_fast_response(messages):
                        yield {
                            "type": "token",
                            "content": token,
                            "metadata": {
                                "partial_response": True
                            }
                        }

            # Step 6: Log task for automation detection
            self.hyper_automation.log_task(message, context)

            # Step 7: Calculate quality score
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            quality_score = self.quality_scorer.calculate_quality(
                response={"text": ""},  # Will be calculated from streamed content
                request={"message": message, "user_id": user_id},
                signals={"latency_ms": elapsed_ms}
            )

            # Step 8: Track performance
            self.rapid_iteration.track_performance({
                "latency": elapsed_ms,
                "success_rate": 1.0,
                "quality": quality_score
            })

            # Step 9: Yield completion event
            yield {
                "type": "complete",
                "metadata": {
                    "latency_ms": elapsed_ms,
                    "source": "streaming",
                    "complex_reasoning": is_complex,
                    "matched_skills": len(matched_skills) if matched_skills else 0,
                    "top_skill": matched_skills[0]['name'] if matched_skills else None,
                    "request_id": self.request_count,
                    "quality_score": quality_score
                }
            }

        except Exception as e:
            logger.error(f"❌ Error in streaming: {e}")
            yield {
                "type": "complete",
                "metadata": {
                    "error": str(e),
                    "request_id": self.request_count
                }
            }

    def _is_complex_query(self, message: str) -> bool:
        """Determine if query requires System 2 thinking"""
        complex_indicators = [
            "why", "how does", "explain", "analyze", "compare",
            "what if", "solve", "calculate", "reason", "prove"
        ]

        message_lower = message.lower()
        return any(indicator in message_lower for indicator in complex_indicators)

    async def _fast_response(self, message: str, context: str) -> Dict[str, Any]:
        """Generate fast response with speculative decoding"""
        messages = [
            {"role": "system", "content": "You are JARVIS v9.0, an advanced AI assistant. Provide comprehensive, detailed responses."},
            {"role": "user", "content": f"Context: {context}\n\nUser: {message}"}
        ]

        result = self.speculative_decoder.generate(
            messages,
            max_tokens=2048,
            temperature=0.7,
            use_speculative=True
        )

        return {
            "text": result["text"],
            "source": "speculative_decoder",
            "tokens": result["tokens"],
            "time_ms": result["time_ms"]
        }

    async def _stream_fast_response(self, messages: list):
        """
        Generate response with streaming from the LLM
        This method yields response chunks as they become available from the API
        """
        # Use the speculative decoder's streaming capability
        # Note: The current speculative decoder implementation doesn't support true streaming
        # So we'll use the direct streaming method from the target model
        try:
            # Attempt to stream directly from the target model
            for chunk in self.speculative_decoder.stream_direct(
                messages,
                max_tokens=2048,
                temperature=0.7
            ):
                if chunk and chunk.strip():
                    yield chunk
        except Exception as e:
            logger.error(f"Streaming failed, falling back to non-streaming: {e}")
            # Fallback to non-streaming approach
            full_response = self.speculative_decoder.generate(
                messages,
                max_tokens=2048,
                temperature=0.7,
                use_speculative=True
            )

            response_text = full_response["text"]
            # Yield in chunks to simulate streaming
            chunk_size = 10
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                if chunk.strip():
                    yield chunk

    async def _system2_response(self, message: str, context: str) -> Dict[str, Any]:
        """Generate response with System 2 thinking"""
        result = self.system2.reason(
            problem=message,
            context=context,
            max_iterations=5,
            max_depth=3
        )

        return {
            "text": result["solution"],
            "source": "system2",
            "confidence": result["confidence"],
            "time_ms": result["time_ms"],
            "reasoning_path": result["reasoning_path"]
        }

    async def analyze_with_first_principles(self, problem: str) -> Dict[str, Any]:
        """Analyze problem using first principles"""
        logger.info(f"🔬 First principles analysis: {problem[:50]}...")

        result = self.first_principles.decompose(problem)

        return result

    async def suggest_automations(self) -> list:
        """Get automation suggestions"""
        suggestions = self.hyper_automation.get_suggestions(status="pending")

        logger.info(f"💡 Found {len(suggestions)} automation suggestions")

        return suggestions

    async def make_autonomous_decision(
        self,
        action: str,
        context: Dict[str, Any],
        confidence: float = 0.5
    ) -> Dict[str, Any]:
        """Make autonomous decision with risk assessment"""
        decision = self.autonomous.evaluate_decision(action, context, confidence)

        logger.info(f"🤖 Decision: {decision['decision']} (risk: {decision['risk_score']:.1f})")

        return decision

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            "version": "9.0.0",
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "memory": self.memory.get_stats(),
            "llm": self.llm_manager.get_stats(),
            "speculative_decoder": self.speculative_decoder.get_stats(),
            "hyper_automation": self.hyper_automation.get_stats(),
            "rapid_iteration": self.rapid_iteration.get_stats(),
            "quality": self.quality_scorer.get_stats(),
            "profiler": self.profiler.get_stats(),
            "optimization": self.optimization.get_optimization_report(),
            "autonomous": self.autonomous.get_autonomy_report(),
            "timestamp": datetime.now().isoformat()
        }

    async def optimize_system(self):
        """Run system optimization"""
        logger.info("⚡ Running system optimization...")

        # Get current performance
        stats = self.get_system_stats()

        # Detect bottlenecks using profiler
        bottlenecks = self.profiler.get_bottlelinecks(hours=1)
        if bottlenecks:
            logger.info(f"🐌 Found {len(bottlenecks)} bottlenecks")
            for bn in bottlenecks[:3]:
                logger.info(f"   - {bn['operation']}: {bn['latency_ms']:.2f}ms")
                logger.info(f"     Suggestion: {bn['suggestion']}")

        # Get quality trends
        quality_trend = self.quality_scorer.get_quality_trend(hours=1)
        logger.info(f"📊 Quality trend: {quality_trend['trend']} (avg: {quality_trend['avg_quality']:.2f})")

        # Get component stats
        for component in self.profiler.component_stats.keys():
            comp_stats = self.profiler.get_component_stats(component)
            if comp_stats.get('avg_ms', 0) > 100:
                logger.info(f"⚠️  {component}: avg {comp_stats['avg_ms']:.2f}ms")

        logger.info("✅ Optimization analysis complete")

    def save_state(self):
        """Save all system state"""
        logger.info("💾 Saving system state...")

        os.makedirs("state", exist_ok=True)

        self.memory.save_all()
        self.hyper_automation.save("state/hyper_automation.json")
        self.rapid_iteration.save("state/rapid_iteration.json")
        self.optimization.save("state/optimization.json")
        self.autonomous.save("state/autonomous.json")

        logger.info("✅ System state saved")

    def load_state(self):
        """Load system state"""
        logger.info("📂 Loading system state...")

        try:
            self.hyper_automation.load("state/hyper_automation.json")
            self.autonomous.load("state/autonomous.json")
            logger.info("✅ System state loaded")
        except Exception as e:
            logger.warning(f"⚠️ Could not load state: {e}")


# FastAPI Integration
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="JARVIS v9.0 ULTRA", version="9.0.0")

# CORS configuration for web app
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:3003").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = JarvisV9Orchestrator()

# Mount chat router
from api.routers import chat as chat_router
chat_router.set_orchestrator(orchestrator)
app.include_router(chat_router.router)


class MessageRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class DecisionRequest(BaseModel):
    action: str
    context: Dict[str, Any]
    confidence: float = 0.5


@app.post("/api/message")
async def process_message(request: MessageRequest):
    """Process user message"""
    result = await orchestrator.process_message(
        request.message,
        request.context,
        request.user_id
    )
    return result


@app.post("/api/first-principles")
async def first_principles_analysis(request: MessageRequest):
    """Analyze with first principles"""
    result = await orchestrator.analyze_with_first_principles(request.message)
    return result


@app.get("/api/automations")
async def get_automations():
    """Get automation suggestions"""
    suggestions = await orchestrator.suggest_automations()
    return {"suggestions": suggestions}


@app.post("/api/decision")
async def make_decision(request: DecisionRequest):
    """Make autonomous decision"""
    result = await orchestrator.make_autonomous_decision(
        request.action,
        request.context,
        request.confidence
    )
    return result


class AgentTeamRequest(BaseModel):
    task: str
    team_name: str = "standard_workflow"
    context: Optional[Dict[str, Any]] = None


@app.post("/api/agent-team")
async def execute_agent_team(request: AgentTeamRequest):
    """Execute a task using a coordinated team of agents"""
    result = await orchestrator.autonomy_system.execute_with_agent_team(
        task_description=request.task,
        team_name=request.team_name,
        context=request.context
    )
    return result


@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return orchestrator.get_system_stats()


@app.post("/api/optimize")
async def optimize():
    """Run system optimization"""
    await orchestrator.optimize_system()
    return {"status": "optimization_complete"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "9.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/synthesize-workflow")
async def synthesize_workflow(goal: str, context: Optional[Dict[str, Any]] = None):
    """Synthesize a workflow from a goal"""
    workflow = orchestrator.workflow_synth.synthesize(goal, context)
    return orchestrator.workflow_synth.get_workflow_info(workflow)


@app.post("/api/execute-workflow")
async def execute_workflow(goal: str, context: Optional[Dict[str, Any]] = None):
    """Synthesize and execute a workflow"""
    workflow = orchestrator.workflow_synth.synthesize(goal, context)
    result = await orchestrator.workflow_synth.execute_workflow(
        workflow=workflow,
        initial_state=context,
        executor=orchestrator.autonomy_system.executor
    )
    return result


@app.get("/api/skill-graph")
async def get_skill_graph(skill: Optional[str] = None):
    """Get skill graph info"""
    if skill:
        info = orchestrator.skill_graph.get_skill_info(skill)
        return {"skill": info} if info else {"error": "Skill not found"}
    return orchestrator.skill_graph.get_stats()


@app.on_event("startup")
async def startup():
    """Startup tasks"""
    logger.info("🚀 JARVIS v9.0 ULTRA API starting...")
    orchestrator.load_state()


@app.on_event("shutdown")
async def shutdown():
    """Shutdown tasks"""
    logger.info("🛑 JARVIS v9.0 ULTRA API shutting down...")
    orchestrator.save_state()


# Main entry point
if __name__ == "__main__":
    import uvicorn

    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    os.makedirs("state", exist_ok=True)

    logger.info("="*50)
    logger.info("JARVIS v9.0 ULTRA")
    logger.info("PhD-Level AI Assistant with Elon Musk Features")
    logger.info("="*50)

    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
