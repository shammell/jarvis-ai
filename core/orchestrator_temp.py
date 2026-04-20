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

        # Request deduplication cache (Enhanced)
        self.deduplication_cache = {}
        self.deduplication_timeout = 300  # 5 minutes
        self.deduplication_stats = {
            "total_requests": 0,
            "duplicates_found": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

        # Performance metrics
        self.performance_metrics = {
            "avg_response_time": 0.0,
            "min_response_time": float('inf'),
            "max_response_time": 0.0,
            "success_rate": 1.0,
            "error_rate": 0.0,
            "throughput": 0.0,
            "memory_usage": 0.0,
            "cpu_usage": 0.0,
            "active_requests": 0,
            "queue_depth": 0
        }

        # System resilience and recovery
        self.recovery_attempts = {}
        self.degraded_mode = False
        self.last_health_check = self.start_time
        self.health_check_interval = 60  # Check every 60 seconds

        # Async Airlock Buffer - Background Task Queue
        self.background_tasks = set()

        # Configuration state
        self.config = {
            "max_concurrent_requests": 10,
            "request_timeout": 300,  # 5 minutes
            "retry_attempts": 3,
            "health_check_enabled": True,
            "metrics_collection_enabled": True,
            "autonomous_mode": False,
            "sea_enabled": True
        }

        # Component initialization status
        self.initialization_status = {
            "llm_manager": False,
            "speculative_decoder": False,
            "system2_thinking": False,
            "memory": False,
            "first_principles": False,
            "hyper_automation": False,
            "rapid_iteration": False,
            "optimization_engine": False,
            "autonomous_decision": False,
            "skill_loader": False,
            "quality_scorer": False,
            "profiler": False,
            "sea_controller": False
        }

        logger.info("✅ JARVIS v9.0 ULTRA initialized successfully")
        logger.info("🔧 Enhanced State Management: All systems initialized")

        # Note: Autonomous startup will be triggered when async context is available
        # Use jarvis_autonomous.py for standalone autonomous mode

        # SEA activation is deferred to async lifespan handler
        logger.info("🧬 Self-Evolving Architecture (SEA) - deferred to async context")

    @with_resilience(component='message_processor', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
    async def process_message(
        self,
        message: str,
        context: Dict[str, Any] = None,
        user_id: str = None,
        auth_token: str = None
    ) -> Dict[str, Any]:
        """
        Process incoming message with full v9.0 capabilities

        Args:
            message: User message
            context: Additional context
            user_id: User identifier
            auth_token: JWT authentication token

        Returns:
            Response with metadata
        """
        logger.info(f"📨 Processing message: {message[:50]}...")

        # Security authentication and authorization (PhD Level - Phase 1)
        try:
            # Authenticate user
            if auth_token:
                payload = self.security_manager.validate_token(auth_token)
                if not payload:
                    logger.warning(f"❌ Authentication failed for user: {user_id}")
                    return {
                        "text": "Authentication required. Please provide a valid JWT token.",
                        "metadata": {
                            "error": "authentication_failed",
                            "request_id": self.request_count,
                            "requires_auth": True
                        }
                    }
                user_id = payload.get('user_id')

            # Validate permissions for message processing
            if user_id and not self.security_manager.check_permission(auth_token or "", Permission.EXECUTE_SKILLS):
                logger.warning(f"❌ Permission denied for user: {user_id}")
                return {
                    "text": "Access denied. You don't have permission to execute skills.",
                    "metadata": {
                        "error": "permission_denied",
                        "request_id": self.request_count,
                        "user_id": user_id
                    }
                }

            # Log security event
            self.security_manager.log_security_event(
                "message_processed",
                user_id or "anonymous",
                {"message_length": len(message), "has_auth": bool(auth_token)}
            )

        except Exception as e:
            logger.error(f"❌ Security check failed: {e}")
            return {
                "text": "Security validation failed. Please try again.",
                "metadata": {
                    "error": "security_validation_failed",
                    "request_id": self.request_count,
                    "details": str(e)
                }
            }

        # Input validation (Enhanced - Fix 14)
        try:
            # Validate message parameter type
            if not isinstance(message, str):
                logger.error(f"❌ Invalid message type: {type(message)}")
                return {
                    "text": "Message must be a string.",
                    "metadata": {
                        "error": "invalid_message_type",
                        "request_id": self.request_count,
                        "expected_type": "string",
                        "actual_type": str(type(message))
                    }
                }

            # Validate message content and length
            if not message or not message.strip():
                logger.error("❌ Empty message received")
                return {
                    "text": "Please provide a valid message.",
                    "metadata": {
                        "error": "empty_message",
                        "request_id": self.request_count
                    }
                }

            # Validate message length (prevent abuse and system overload)
            if len(message) > 10000:  # 10KB limit
                logger.warning(f"⚠️ Message too long: {len(message)} characters")
                return {
                    "text": "Message is too long. Please keep it under 10,000 characters.",
                    "metadata": {
                        "error": "message_too_long",
                        "request_id": self.request_count,
                        "message_length": len(message),
                        "max_length": 10000
                    }
                }

            # Validate message content (basic safety checks for invalid characters)
            if any(char in message for char in ["\x00", "\uffff"]):  # Null bytes, invalid unicode
                logger.warning("⚠️ Message contains invalid characters")
                return {
                    "text": "Message contains invalid characters.",
                    "metadata": {
                        "error": "invalid_characters",
                        "request_id": self.request_count
                    }
                }

            # Validate context parameter if provided
            if context is not None and not isinstance(context, dict):
                logger.error(f"❌ Invalid context type: {type(context)}")
                return {
                    "text": "Context must be a dictionary or None.",
                    "metadata": {
                        "error": "invalid_context_type",
                        "request_id": self.request_count,
                        "expected_type": "dict or None",
                        "actual_type": str(type(context))
                    }
                }

            # Validate user_id parameter if provided
            if user_id is not None:
                if not isinstance(user_id, str):
                    logger.error(f"❌ Invalid user_id type: {type(user_id)}")
                    return {
                        "text": "User ID must be a string or None.",
                        "metadata": {
                            "error": "invalid_user_id_type",
                            "request_id": self.request_count,
                            "expected_type": "string or None",
                            "actual_type": str(type(user_id))
                        }
                    }

                # Validate user_id length (prevent abuse)
                if len(user_id) > 100:  # Reasonable length limit for user identifiers
                    logger.warning(f"⚠️ User ID too long: {len(user_id)} characters")
                    return {
                        "text": "User ID is too long. Please keep it under 100 characters.",
                        "metadata": {
                            "error": "user_id_too_long",
                            "request_id": self.request_count,
                            "user_id_length": len(user_id),
                            "max_length": 100
                        }
                    }

                # Basic sanitization for user_id
                if not user_id.strip():
                    logger.warning("⚠️ User ID is empty or whitespace")
                    user_id = None  # Reset to None if empty after stripping

        except Exception as validation_error:
            logger.error(f"❌ Input validation error: {validation_error}")
            return {
                "text": "Invalid input parameters.",
                "metadata": {
                    "error": "validation_error",
                    "request_id": self.request_count,
                    "error_details": str(validation_error)
                }
            }

        try:
            # Monitor this function through SEA
            if hasattr(self, 'sea_controller'):
                logger.debug("🔍 Using SEA controller for monitoring")
                try:
                    monitored_process = self.sea_controller.monitor_function(self._process_message_impl)
                    return await monitored_process(message, context, user_id)
                except Exception as e:
                    logger.warning(f"⚠️ SEA monitoring failed, falling back to direct execution: {e}")
                    return await self._process_message_impl(message, context, user_id)
            else:
                logger.debug("🔧 No SEA controller available, using direct execution")
                return await self._process_message_impl(message, context, user_id)

        except asyncio.CancelledError:
            logger.warning("⚠️ Message processing was cancelled")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in process_message wrapper: {e}", exc_info=True)
            return {
                "text": "I encountered an unexpected error. Please try again or contact support.",
                "metadata": {
                    "error": "process_message_wrapper_error",
                    "request_id": self.request_count,
                    "error_details": str(e)
                }
            }

    @with_resilience(component='message_processor_impl', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
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

        # Request deduplication check
        dedupe_response = self._check_request_deduplication(message, user_id)
        if dedupe_response:
            logger.info(f"🔄 Returning cached response for duplicate request from user {user_id}")
            return dedupe_response

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
                logger.info("🧠 Complex query detected - dispatching to Async Airlock Buffer")

                # 1. Immediate acknowledgment
                ack_response = {
                    "text": "🔍 This is a complex query. I am using System 2 thinking to analyze. I will reply via WhatsApp/Messaging as soon as I have the solution.",
                    "metadata": {
                        "status": "thinking",
                        "request_id": self.request_count,
                        "complex_reasoning": True
                    }
                }

                # 2. Dispatch background task
                task = asyncio.create_task(self._handle_background_reasoning(message, context_text, user_id))
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)

                return ack_response

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

            # Step 9: Store response in memory
            self.memory.store(response["text"], memory_type="conversation", metadata={
                "user_id": user_id,
                "response_to": message[:100],
                "timestamp": datetime.now().isoformat(),
                "quality_score": quality_score
            })

            # Step 10: Cache response for deduplication
            self._cache_response(message, user_id, {
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

    def _check_request_deduplication(self, message: str, user_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Check if this is a duplicate request and return cached response if available

        Args:
            message: User message
            user_id: User identifier

        Returns:
            Cached response if duplicate found, None otherwise
        """
        # Create cache key from message and user_id
        cache_key = self._generate_cache_key(message, user_id)

        current_time = time.time()

        if cache_key in self.deduplication_cache:
            cached_data = self.deduplication_cache[cache_key]
            cache_time = cached_data['timestamp']

            # Check if cache is still valid
            if current_time - cache_time < self.deduplication_timeout:
                logger.info(f"🎯 Found duplicate request, returning cached response")
                return cached_data['response']
            else:
                # Remove expired cache entry
                del self.deduplication_cache[cache_key]

        return None

    def _generate_cache_key(self, message: str, user_id: str = None) -> str:
        """
        Generate a cache key for request deduplication

        Args:
            message: User message
            user_id: User identifier

        Returns:
            Cache key string
        """
        # Normalize message for comparison
        normalized_message = message.strip().lower()

        # Combine message and user_id for cache key
        key_data = f"{normalized_message}:{user_id or 'anonymous'}"

        # Create hash for consistent key
        return hashlib.md5(key_data.encode()).hexdigest()

    def _cache_response(self, message: str, user_id: str, response: Dict[str, Any]):
        """
        Cache response for duplicate request detection

        Args:
            message: User message
            user_id: User identifier
            response: Response to cache
        """
        cache_key = self._generate_cache_key(message, user_id)
        self.deduplication_cache[cache_key] = {
            'timestamp': time.time(),
            'response': response
        }

    @with_resilience(component='streaming', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
    async def stream_response(
        self,
        message: str,
        user_id: str = None,
        context: Dict[str, Any] = None,
        auth_token: str = None
    ) -> Dict[str, Any]:
        """
        Stream response tokens as they become available

        Args:
            message: User message
            user_id: User identifier
            context: Additional context
            auth_token: JWT authentication token

        Yields:
            Dictionary with token chunks and completion metadata
        """
        # Security authentication and authorization (PhD Level - Phase 1)
        try:
            # Authenticate user
            if auth_token:
                payload = self.security_manager.validate_token(auth_token)
                if not payload:
                    logger.warning(f"❌ Authentication failed for user: {user_id}")
                    yield {
                        "type": "error",
                        "text": "Authentication required. Please provide a valid JWT token.",
                        "metadata": {
                            "error": "authentication_failed",
                            "request_id": self.request_count,
                            "requires_auth": True
                        }
                    }
                    return
                user_id = payload.get('user_id')

            # Validate permissions for streaming
            if user_id and not self.security_manager.check_permission(auth_token or "", Permission.EXECUTE_SKILLS):
                logger.warning(f"❌ Permission denied for user: {user_id}")
                yield {
                    "type": "error",
                    "text": "Access denied. You don't have permission to execute skills.",
                    "metadata": {
                        "error": "permission_denied",
                        "request_id": self.request_count,
                        "user_id": user_id
                    }
                }
                return

            # Log security event
            self.security_manager.log_security_event(
                "stream_response_started",
                user_id or "anonymous",
                {"message_length": len(message), "has_auth": bool(auth_token)}
            )

        except Exception as e:
            logger.error(f"❌ Security check failed: {e}")
            yield {
                "type": "error",
                "text": "Security validation failed. Please try again.",
                "metadata": {
                    "error": "security_validation_failed",
                    "request_id": self.request_count,
                    "details": str(e)
                }
            }
            return

        # Input validation
        if not message or not message.strip():
            logger.error("❌ Empty message received for streaming")
            yield {
                "type": "error",
                "text": "Please provide a valid message.",
                "metadata": {
                    "error": "empty_message",
                    "request_id": self.request_count
                }
            }
            return

        try:
            # Monitor this function through SEA
            if hasattr(self, 'sea_controller'):
                logger.debug("🔍 Using SEA controller for streaming monitoring")
                try:
                    monitored_process = self.sea_controller.monitor_function(self._stream_response_impl)
                    async for chunk in monitored_process(message, user_id, context):
                        yield chunk
                except Exception as e:
                    logger.warning(f"⚠️ SEA monitoring failed for streaming, falling back to direct execution: {e}")
                    async for chunk in self._stream_response_impl(message, user_id, context):
                        yield chunk
            else:
                logger.debug("🔧 No SEA controller available, using direct streaming execution")
                async for chunk in self._stream_response_impl(message, user_id, context):
                    yield chunk

        except asyncio.CancelledError:
            logger.warning("⚠️ Streaming was cancelled")
            yield {
                "type": "cancelled",
                "metadata": {
                    "request_id": self.request_count,
                    "message": "Streaming cancelled"
                }
            }
        except Exception as e:
            logger.error(f"❌ Unexpected error in stream_response wrapper: {e}", exc_info=True)
            yield {
                "type": "error",
                "text": "An error occurred during streaming. Please try again.",
                "metadata": {
                    "error": "stream_response_wrapper_error",
                    "request_id": self.request_count,
                    "error_details": str(e)
                }
            }

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

    @with_resilience(component='llm_call', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
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

    async def _handle_background_reasoning(self, message: str, context_text: str, user_id: str):
        """
        Background worker for Async Airlock Buffer.
        Runs System 2 thinking and pushes result to external bridges.
        """
        try:
            logger.info(f"⏳ Background reasoning started for: {message[:50]}...")

            with self.profiler.profile("system2_reason", "system2"):
                response = await self._system2_response(message, context_text)

            logger.info(f"✅ Background reasoning complete. Solution length: {len(response['text'])}")

            # Push result back to user via WhatsApp Bridge
            import httpx
            async with httpx.AsyncClient() as client:
                # Use current phone from context or fallback to Shameel profile
                phone = "03147139674"
                await client.post("http://localhost:3002/api/whatsapp/send", json={
                    "phone": phone,
                    "message": f"🧠 JARVIS SOLUTION:\n\n{response['text']}",
                    "sender": "JARVIS"
                })

            logger.info(f"📤 Solution pushed to WhatsApp bridge for user {user_id}")

        except Exception as e:
            logger.error(f"❌ Background reasoning task failed: {e}")

    @with_resilience(component='system2_thinking', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
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

    @with_resilience(component='first_principles', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
    async def analyze_with_first_principles(self, problem: str) -> Dict[str, Any]:
        """Analyze problem using first principles"""
        logger.info(f"🔬 First principles analysis: {problem[:50]}...")

        result = self.first_principles.decompose(problem)

        return result

    @with_resilience(component='automation', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
    async def suggest_automations(self) -> list:
        """Get automation suggestions"""
        suggestions = self.hyper_automation.get_suggestions(status="pending")

        logger.info(f"💡 Found {len(suggestions)} automation suggestions")

        return suggestions

    @with_resilience(component='autonomous_decision', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
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

    @with_resilience(component='system_stats', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
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

    @with_resilience(component='health_status', with_circuit_breaker=True, with_retry=True, with_bulkhead=True, with_watchdog=True)
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status for monitoring"""
        uptime = (datetime.now() - self.start_time).total_seconds()

        # Component health checks
        component_health = {}
        for component_name, component in [
            ('llm_manager', self.llm_manager),
            ('speculative_decoder', self.speculative_decoder),
            ('system2_thinking', self.system2),
            ('memory', self.memory),
            ('first_principles', self.first_principles),
            ('hyper_automation', self.hyper_automation),
            ('rapid_iteration', self.rapid_iteration),
            ('optimization_engine', self.optimization),
            ('autonomous_decision', self.autonomous),
            ('skill_loader', self.skill_loader),
            ('quality_scorer', self.quality_scorer),
            ('profiler', self.profiler),
            ('sea_controller', self.sea_controller)
        ]:
            # Check if component has health check method, otherwise assume healthy
            if hasattr(component, 'get_health_status'):
                component_health[component_name] = component.get_health_status()
            elif hasattr(component, 'is_healthy'):
                component_health[component_name] = component.is_healthy()
            else:
                # If no health method, we assume it's healthy if it exists
                component_health[component_name] = True

        # Calculate additional metrics
        total_errors = self.error_count
        total_success = self.success_count
        total_requests = total_errors + total_success

        success_rate = (total_success / total_requests * 100) if total_requests > 0 else 100.0
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0

        # Calculate avg response time if available
        avg_response_time = (self.total_processing_time / total_success) if total_success > 0 else 0.0

        # Overall system health determination
        overall_health = all(component_health.values()) and success_rate >= 95.0

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
            "components": component_health,
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
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Lifecycle manager for async startup/shutdown
_lifespan_state = {"orchestrator": None, "voice_runtime": None}


@asynccontextmanager
