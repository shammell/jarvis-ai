"""
JARVIS v9.0 - gRPC Python Server
Secure gRPC bridge with JWT/RBAC enforcement.
"""

import sys
import os
import time
import logging
import asyncio
from concurrent import futures
from typing import Dict, Any, Optional

import grpc

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# Add project and grpc_service dirs to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.security_system import security_manager, Permission, input_validator

try:
    import jarvis_pb2
    import jarvis_pb2_grpc
except ImportError:
    print("⚠️ Protobuf files not generated. Run protoc for grpc_service/jarvis.proto")
    jarvis_pb2 = None
    jarvis_pb2_grpc = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OrchestratorProxy:
    """Lazy-loading proxy for main orchestrator."""

    def __init__(self):
        self._orchestrator = None
        self._orchestrator_type = None
        self._load_attempts = 0
        self._max_attempts = 3

    def _load_orchestrator(self):
        if self._load_attempts >= self._max_attempts:
            logger.error("❌ Max orchestrator load attempts reached")
            return None

        self._load_attempts += 1

        try:
            from main_genesis import orchestrator
            self._orchestrator = orchestrator
            self._orchestrator_type = "v11.0 GENESIS"
            logger.info("✅ Loaded JARVIS v11.0 GENESIS orchestrator")
            return self._orchestrator
        except Exception as e:
            logger.warning(f"⚠️ Could not load v11.0 GENESIS: {e}")

        try:
            from main import orchestrator
            self._orchestrator = orchestrator
            self._orchestrator_type = "v9.0 ULTRA"
            logger.info("✅ Loaded JARVIS v9.0 ULTRA orchestrator")
            return self._orchestrator
        except Exception as e:
            logger.warning(f"⚠️ Could not load v9.0 ULTRA: {e}")

        logger.error("❌ No orchestrator available")
        return None

    def get(self):
        if self._orchestrator is None:
            self._load_orchestrator()
        return self._orchestrator


orchestrator_proxy = OrchestratorProxy()


def validate_auth_token(token: str, permission: Permission, context) -> Dict[str, Any]:
    if not token:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Authentication token is required")

    payload = security_manager.validate_token(token, 'access')
    if not payload:
        context.abort(grpc.StatusCode.UNAUTHENTICATED, "Invalid or expired token")

    if not security_manager.check_permission(token, permission):
        context.abort(grpc.StatusCode.PERMISSION_DENIED, f"Permission denied: {permission.value}")

    return payload


def sanitize_request_data(data: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = input_validator.sanitize_input(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_request_data(value)
        else:
            sanitized[key] = value
    return sanitized


class JarvisServicer(jarvis_pb2_grpc.JarvisServiceServicer):
    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        logger.info("🚀 JARVIS gRPC Servicer initialized with auth/RBAC")

    def Authenticate(self, request, context):
        tokens = security_manager.authenticate_user(
            request.username,
            request.password,
            ip_address=context.peer()
        )
        if not tokens:
            return jarvis_pb2.AuthResponse(success=False, error="Authentication failed")

        user = tokens.get('user', {})
        return jarvis_pb2.AuthResponse(
            success=True,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            expires_in=tokens['expires_in'],
            token_type=tokens['token_type'],
            user_info=jarvis_pb2.User(
                id=user.get('id', ''),
                username=user.get('id', ''),
                role=user.get('role', ''),
                permissions=user.get('permissions', []),
                created_at=int(time.time()),
                last_login=int(time.time())
            )
        )

    def RefreshToken(self, request, context):
        tokens = security_manager.refresh_token(request.refresh_token, ip_address=context.peer())
        if not tokens:
            return jarvis_pb2.AuthResponse(success=False, error="Invalid refresh token")

        user = tokens.get('user', {})
        return jarvis_pb2.AuthResponse(
            success=True,
            access_token=tokens['access_token'],
            refresh_token=tokens['refresh_token'],
            expires_in=tokens['expires_in'],
            token_type=tokens['token_type'],
            user_info=jarvis_pb2.User(
                id=user.get('id', ''),
                username=user.get('id', ''),
                role=user.get('role', ''),
                permissions=user.get('permissions', []),
                created_at=int(time.time()),
                last_login=int(time.time())
            )
        )

    def ValidateToken(self, request, context):
        payload = security_manager.validate_token(request.token, 'access')
        if not payload:
            return jarvis_pb2.TokenValidationResponse(valid=False, error="Invalid or expired token")

        return jarvis_pb2.TokenValidationResponse(
            valid=True,
            user_id=payload.get('user_id', ''),
            role=payload.get('role', ''),
            expires_at=int(payload.get('exp', 0)),
            permissions=payload.get('permissions', [])
        )

    def ProcessMessage(self, request, context):
        start = time.time()
        self.request_count += 1

        payload = validate_auth_token(request.auth_token, Permission.ACCESS_GRPC, context)

        if not input_validator.validate_input(request.text, 'general'):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid message content")

        data = sanitize_request_data({
            'from': request.from_,
            'text': request.text,
            'metadata': dict(request.metadata)
        })

        orchestrator = orchestrator_proxy.get()
        if not orchestrator:
            context.abort(grpc.StatusCode.UNAVAILABLE, "Orchestrator not available")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                orchestrator.process_message(
                    data['text'],
                    {'source': 'whatsapp', 'metadata': data['metadata']},
                    payload.get('user_id'),
                    request.auth_token
                )
            )
            loop.close()
        except Exception as e:
            logger.error(f"❌ Orchestrator error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Orchestrator error: {str(e)}")

        return jarvis_pb2.MessageResponse(
            success=True,
            response_text=response.get('text', ''),
            processing_time_ms=int((time.time() - start) * 1000)
        )

    def ExecuteAgent(self, request, context):
        payload = validate_auth_token(request.auth_token, Permission.EXECUTE_SKILLS, context)

        if not input_validator.validate_input(request.task, 'general'):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid task content")

        orchestrator = orchestrator_proxy.get()
        if not orchestrator or not hasattr(orchestrator, 'swarm'):
            context.abort(grpc.StatusCode.UNAVAILABLE, "Swarm coordinator not available")

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                orchestrator.swarm.execute_agent_task(
                    request.agent_type,
                    request.task,
                    request.context,
                    user_id=payload.get('user_id'),
                    auth_token=request.auth_token
                )
            )
            loop.close()
        except Exception as e:
            logger.error(f"❌ Agent execution error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Agent execution error: {str(e)}")

        return jarvis_pb2.AgentResponse(success=True, result=str(result))

    def StoreMemory(self, request, context):
        validate_auth_token(request.auth_token, Permission.WRITE_MEMORY, context)

        if not input_validator.validate_input(request.text, 'general'):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid memory content")

        orchestrator = orchestrator_proxy.get()
        if not orchestrator or not hasattr(orchestrator, 'memory'):
            context.abort(grpc.StatusCode.UNAVAILABLE, "Memory controller not available")

        try:
            orchestrator.memory.store(
                request.text,
                memory_type=request.type,
                metadata=dict(request.metadata),
                auth_token=request.auth_token
            )
        except Exception as e:
            logger.error(f"❌ Memory storage error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Memory storage error: {str(e)}")

        return jarvis_pb2.MemoryResponse(success=True)

    def RetrieveMemory(self, request, context):
        validate_auth_token(request.auth_token, Permission.READ_MEMORY, context)

        if not input_validator.validate_input(request.query, 'general'):
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, "Invalid query content")

        orchestrator = orchestrator_proxy.get()
        if not orchestrator or not hasattr(orchestrator, 'memory'):
            context.abort(grpc.StatusCode.UNAVAILABLE, "Memory controller not available")

        try:
            results = orchestrator.memory.retrieve(
                request.query,
                top_k=request.limit or 5,
                memory_type=request.type if request.type else None,
                auth_token=request.auth_token
            )
            items = [
                jarvis_pb2.MemoryItem(
                    text=r.get('text', ''),
                    score=r.get('score', 0.0),
                    metadata=r.get('metadata', {})
                )
                for r in results
            ]
        except Exception as e:
            logger.error(f"❌ Memory retrieval error: {e}")
            context.abort(grpc.StatusCode.INTERNAL, f"Memory retrieval error: {str(e)}")

        return jarvis_pb2.MemoryResponse(success=True, items=items)

    def HealthCheck(self, request, context):
        token = getattr(request, 'auth_token', '')
        validate_auth_token(token, Permission.READ_SYSTEM_STATS, context)
        uptime = int(time.time() - self.start_time)
        return jarvis_pb2.HealthResponse(
            healthy=True,
            status="running",
            metrics={
                "uptime_seconds": str(uptime),
                "request_count": str(self.request_count),
                "timestamp": str(int(time.time()))
            }
        )

    def StreamEvents(self, request, context):
        validate_auth_token(request.auth_token, Permission.STREAM_RESPONSES, context)

        while context.is_active():
            yield jarvis_pb2.Event(
                type="heartbeat",
                message="System running",
                timestamp=int(time.time() * 1000),
                data={"client_id": request.client_id}
            )
            time.sleep(5)


def serve(port=50051, secure=False, cert_file=None, key_file=None, ca_cert_file=None):
    if not jarvis_pb2_grpc:
        logger.error("❌ Cannot start server: protobuf files not generated")
        return

    # Import network security configuration
    from core.network_security import NetworkSecurityConfig
    security_config = NetworkSecurityConfig()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_frame_size', 16384),
            ('grpc.http2.min_time_between_pings_ms', 300000),
            ('grpc.http2.min_ping_interval_without_data_ms', 300000),
            ('grpc.http2.max_pings_without_data', 2),
            ('grpc.http2.bdp_probe', 1),
        ]
    )

    jarvis_pb2_grpc.add_JarvisServiceServicer_to_server(JarvisServicer(), server)

    if secure:
        if not cert_file or not key_file:
            logger.error("❌ TLS requires cert_file and key_file")
            # Try to generate self-signed certificates for development
            from core.network_security import network_security_manager
            cert_file, key_file = network_security_manager.generate_self_signed_cert()
            if not cert_file or not key_file:
                logger.error("❌ Could not generate certificates, exiting")
                return

        # Handle mTLS if CA certificate is provided
        if ca_cert_file and os.path.exists(ca_cert_file):
            # mTLS with client certificate verification
            with open(key_file, 'rb') as kf, open(cert_file, 'rb') as cf, open(ca_cert_file, 'rb') as caf:
                server_credentials = grpc.ssl_server_credentials(
                    private_key_certificate_chain_pairs=[(kf.read(), cf.read())],
                    root_certificates=caf.read(),
                    require_client_auth=True
                )
            server.add_secure_port(f'0.0.0.0:{port}', server_credentials)
            logger.info(f"🔐🔐 gRPC server running with mTLS on port {port}")
        else:
            # Standard TLS
            with open(key_file, 'rb') as kf, open(cert_file, 'rb') as cf:
                server_credentials = grpc.ssl_server_credentials(
                    private_key_certificate_chain_pairs=[(kf.read(), cf.read())]
                )
            server.add_secure_port(f'0.0.0.0:{port}', server_credentials)
            logger.info(f"🔐 gRPC server running with TLS on port {port}")
    else:
        # For development, allow insecure connections but log a warning
        server.add_insecure_port(f'[::]:{port}')  # Listen on all interfaces
        logger.warning("⚠️ gRPC running without TLS (development only)")

    server.start()
    logger.info(f"🚀 JARVIS gRPC Server running on port {port}")

    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        logger.info("🛑 Shutting down gRPC server...")
        server.stop(0)


if __name__ == '__main__':
    serve(
        secure=os.getenv('GRPC_SECURE') == 'true',
        cert_file=os.getenv('GRPC_CERT_FILE'),
        key_file=os.getenv('GRPC_KEY_FILE')
    )
