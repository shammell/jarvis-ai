"""
==========================================================
JARVIS v9.0 - gRPC Python Server
Handles incoming requests from Node.js bridge
Expected: <10ms latency, binary protocol
PhD-Level Enhancement: Integrated with main orchestrator
==========================================================
"""

import sys
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

import grpc
from concurrent import futures
import time
import logging
import asyncio
from typing import Dict, Any

# Add parent directory and grpc_service directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import generated protobuf code
try:
    import jarvis_pb2
    import jarvis_pb2_grpc
except ImportError:
    print("⚠️  Protobuf files not generated. Run: python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. jarvis.proto")
    jarvis_pb2 = None
    jarvis_pb2_grpc = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ==========================================================
# PhD-Level Enhancement: Lazy-loaded orchestrator singleton
# Prevents circular imports and allows hot-reloading
# ==========================================================
class OrchestratorProxy:
    """Lazy-loading proxy for main orchestrator"""

    def __init__(self):
        self._orchestrator = None
        self._orchestrator_type = None
        self._load_attempts = 0
        self._max_attempts = 3

    def _load_orchestrator(self):
        """Try to load orchestrator with fallback chain"""
        if self._load_attempts >= self._max_attempts:
            logger.error("❌ Max orchestrator load attempts reached")
            return None

        self._load_attempts += 1

        # Try v11.0 GENESIS first (most advanced)
        try:
            from main_genesis import orchestrator
            self._orchestrator = orchestrator
            self._orchestrator_type = "v11.0 GENESIS"
            logger.info("✅ Loaded JARVIS v11.0 GENESIS orchestrator")
            return self._orchestrator
        except Exception as e:
            logger.warning(f"⚠️ Could not load v11.0 GENESIS: {e}")

        # Fallback to v9.0 ULTRA
        try:
            from main import orchestrator
            self._orchestrator = orchestrator
            self._orchestrator_type = "v9.0 ULTRA"
            logger.info("✅ Loaded JARVIS v9.0 ULTRA orchestrator")
            return self._orchestrator
        except Exception as e:
            logger.warning(f"⚠️ Could not load v9.0 ULTRA: {e}")

        # Final fallback: None (echo mode)
        logger.error("❌ No orchestrator available - running in echo mode")
        return None

    def get(self):
        """Get orchestrator instance (lazy load)"""
        if self._orchestrator is None:
            self._load_orchestrator()
        return self._orchestrator

    def get_type(self):
        """Get orchestrator type"""
        return self._orchestrator_type or "echo"


# Global orchestrator proxy
orchestrator_proxy = OrchestratorProxy()


class JarvisServicer:
    """gRPC service implementation"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        logger.info("🚀 JARVIS gRPC Servicer initialized")

    def ProcessMessage(self, request, context):
        """Process incoming WhatsApp message"""
        start = time.time()
        self.request_count += 1

        try:
            logger.info(f"📨 Processing message from {request.from_}: {request.text[:50]}...")

            # ==========================================================
            # PhD-Level Enhancement: Integrated orchestrator call
            # ==========================================================
            orchestrator = orchestrator_proxy.get()

            if orchestrator:
                # Call main orchestrator asynchronously
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    response_text = loop.run_until_complete(
                        orchestrator.handle_whatsapp_message(
                            request.from_,
                            request.text
                        )
                    )

                    loop.close()

                    logger.info(f"✅ Orchestrator response: {response_text[:100]}...")

                except Exception as e:
                    logger.error(f"❌ Orchestrator error: {e}")
                    response_text = f"⚠️ Processing error: {str(e)}"
            else:
                # Echo mode fallback
                response_text = f"🔄 JARVIS (echo mode) received: {request.text}"
                logger.warning("⚠️ Running in echo mode - orchestrator not available")

            processing_time = int((time.time() - start) * 1000)

            return jarvis_pb2.MessageResponse(
                success=True,
                response_text=response_text,
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"❌ Error processing message: {e}")
            return jarvis_pb2.MessageResponse(
                success=False,
                error=str(e)
            )

    def ExecuteAgent(self, request, context):
        """Execute agent task"""
        try:
            logger.info(f"🤖 Executing agent: {request.agent_type} - {request.task[:50]}...")

            # ==========================================================
            # PhD-Level Enhancement: Route to swarm coordinator
            # ==========================================================
            orchestrator = orchestrator_proxy.get()

            if orchestrator and hasattr(orchestrator, 'swarm'):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    result = loop.run_until_complete(
                        orchestrator.swarm.execute_agent_task(
                            request.agent_type,
                            request.task,
                            request.context
                        )
                    )

                    loop.close()

                    return jarvis_pb2.AgentResponse(
                        success=True,
                        result=str(result)
                    )
                except Exception as e:
                    logger.error(f"❌ Agent execution error: {e}")
                    return jarvis_pb2.AgentResponse(
                        success=False,
                        error=str(e)
                    )
            else:
                # Fallback
                result = f"Agent {request.agent_type} executed (fallback mode)"
                return jarvis_pb2.AgentResponse(
                    success=True,
                    result=result
                )

        except Exception as e:
            logger.error(f"❌ Error executing agent: {e}")
            return jarvis_pb2.AgentResponse(
                success=False,
                error=str(e)
            )

    def StoreMemory(self, request, context):
        """Store memory item"""
        try:
            logger.info(f"💾 Storing memory: {request.type} - {request.text[:50]}...")

            # ==========================================================
            # PhD-Level Enhancement: Integrated memory controller
            # ==========================================================
            orchestrator = orchestrator_proxy.get()

            if orchestrator and hasattr(orchestrator, 'memory'):
                try:
                    orchestrator.memory.store(
                        request.text,
                        memory_type=request.type,
                        metadata=dict(request.metadata)
                    )
                    logger.info("✅ Memory stored successfully")
                except Exception as e:
                    logger.error(f"❌ Memory storage error: {e}")
                    return jarvis_pb2.MemoryResponse(
                        success=False,
                        error=str(e)
                    )

            return jarvis_pb2.MemoryResponse(
                success=True
            )

        except Exception as e:
            logger.error(f"❌ Error storing memory: {e}")
            return jarvis_pb2.MemoryResponse(
                success=False,
                error=str(e)
            )

    def RetrieveMemory(self, request, context):
        """Retrieve memory items"""
        try:
            logger.info(f"🔍 Retrieving memory: {request.query[:50]}...")

            # ==========================================================
            # PhD-Level Enhancement: Integrated memory retrieval
            # ==========================================================
            orchestrator = orchestrator_proxy.get()

            if orchestrator and hasattr(orchestrator, 'memory'):
                try:
                    results = orchestrator.memory.retrieve(
                        request.query,
                        top_k=request.limit or 5,
                        memory_type=request.type if request.type else None
                    )

                    items = []
                    for result in results:
                        item = jarvis_pb2.MemoryItem(
                            text=result.get('text', ''),
                            score=result.get('score', 0.0),
                            metadata=result.get('metadata', {})
                        )
                        items.append(item)

                    return jarvis_pb2.MemoryResponse(
                        success=True,
                        items=items
                    )
                except Exception as e:
                    logger.error(f"❌ Memory retrieval error: {e}")
                    return jarvis_pb2.MemoryResponse(
                        success=False,
                        error=str(e)
                    )
            else:
                # Fallback: empty results
                return jarvis_pb2.MemoryResponse(
                    success=True,
                    items=[]
                )

        except Exception as e:
            logger.error(f"❌ Error retrieving memory: {e}")
            return jarvis_pb2.MemoryResponse(
                success=False,
                error=str(e)
            )

    def HealthCheck(self, request, context):
        """Health check endpoint"""
        uptime = int(time.time() - self.start_time)

        # Get orchestrator status
        orchestrator = orchestrator_proxy.get()
        orchestrator_status = {
            "type": orchestrator_proxy.get_type(),
            "available": orchestrator is not None,
            "has_memory": hasattr(orchestrator, 'memory') if orchestrator else False,
            "has_swarm": hasattr(orchestrator, 'swarm') if orchestrator else False
        }

        return jarvis_pb2.HealthResponse(
            healthy=True,
            status="running",
            metrics={
                "uptime_seconds": str(uptime),
                "request_count": str(self.request_count),
                "orchestrator_type": orchestrator_proxy.get_type(),
                "orchestrator_available": str(orchestrator is not None)
            }
        )

    def StreamEvents(self, request, context):
        """Stream events to client"""
        logger.info(f"📡 Client {request.client_id} connected to event stream")

        try:
            while context.is_active():
                # TODO: Integrate with event bus
                event = jarvis_pb2.Event(
                    type="heartbeat",
                    message="System running",
                    timestamp=int(time.time() * 1000)
                )
                yield event
                time.sleep(5)

        except Exception as e:
            logger.error(f"❌ Error streaming events: {e}")


def serve(port=50051):
    """Start gRPC server"""
    if not jarvis_pb2_grpc:
        logger.error("❌ Cannot start server: protobuf files not generated")
        return

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),  # 50MB
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),  # 50MB
        ]
    )

    jarvis_pb2_grpc.add_JarvisServiceServicer_to_server(
        JarvisServicer(), server
    )

    # Use 0.0.0.0 instead of [::] for Windows compatibility
    server.add_insecure_port(f'127.0.0.1:{port}')
    server.start()

    logger.info(f"🚀 JARVIS gRPC Server running on port {port}")
    logger.info(f"📊 Max workers: 10")
    logger.info(f"💾 Max message size: 50MB")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down gRPC server...")
        server.stop(0)


if __name__ == '__main__':
    serve()
