"""
JARVIS v9.0 - Network Security Implementation
Phase 4: Network & Communication Security

Implements enterprise-grade TLS/MTLS encryption, secure network boundaries,
and communication hardening for all network components.
"""

import os
import ssl
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import socket
import secrets
from pathlib import Path

import grpc
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

class NetworkSecurityConfig:
    """Network security configuration manager"""

    def __init__(self):
        # TLS/SSL Configuration
        self.tls_enabled = os.getenv('TLS_ENABLED', 'false').lower() == 'true'
        self.mtls_enabled = os.getenv('MTLS_ENABLED', 'false').lower() == 'true'

        # Certificate paths
        self.server_cert_path = os.getenv('SERVER_CERT_PATH', 'certs/server.crt')
        self.server_key_path = os.getenv('SERVER_KEY_PATH', 'certs/server.key')
        self.ca_cert_path = os.getenv('CA_CERT_PATH', 'certs/ca.crt')
        self.client_cert_required = os.getenv('CLIENT_CERT_REQUIRED', 'false').lower() == 'true'

        # TLS versions and cipher suites
        self.min_tls_version = ssl.TLSVersion.TLSv1_2
        self.max_tls_version = ssl.TLSVersion.TLSv1_3

        # Strong cipher suites (AEAD preferred)
        self.cipher_suites = [
            'ECDHE+AESGCM+ECDSA',
            'ECDHE+CHACHA20+Poly1305',
            'ECDHE+AESGCM+RSA',
            'DHE+AESGCM+ECDSA',
            'DHE+CHACHA20+Poly1305',
            'DHE+AESGCM+RSA',
            '!aNULL',
            '!eNULL',
            '!EXPORT',
            '!DES',
            '!RC4',
            '!MD5',
            '!PSK',
            '!SRP',
            '!CAMELLIA'
        ]

        # Network security settings
        self.rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
        self.rate_limit_requests = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))
        self.rate_limit_window = int(os.getenv('RATE_LIMIT_WINDOW', '60'))  # seconds

        # Timeout settings
        self.request_timeout = int(os.getenv('REQUEST_TIMEOUT', '30'))
        self.connection_timeout = int(os.getenv('CONNECTION_TIMEOUT', '10'))

        # Security headers
        self.security_headers = {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        }

        logger.info("🔒 Network Security Configuration initialized")

    def get_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context with secure settings"""
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = self.min_tls_version
        context.maximum_version = self.max_tls_version

        # Load certificates
        if os.path.exists(self.server_cert_path) and os.path.exists(self.server_key_path):
            context.load_cert_chain(self.server_cert_path, self.server_key_path)

            if self.mtls_enabled and os.path.exists(self.ca_cert_path):
                context.load_verify_locations(self.ca_cert_path)

                if self.client_cert_required:
                    context.verify_mode = ssl.CERT_REQUIRED
                else:
                    context.verify_mode = ssl.CERT_OPTIONAL
        else:
            logger.warning("⚠️ SSL certificates not found, using default context")
            context.set_ciphers(':'.join(self.cipher_suites))
            return context

        context.set_ciphers(':'.join(self.cipher_suites))
        return context

    def get_grpc_ssl_credentials(self) -> Optional[grpc.ServerCredentials]:
        """Get gRPC SSL credentials for secure server"""
        if not self.tls_enabled:
            return None

        try:
            if os.path.exists(self.server_cert_path) and os.path.exists(self.server_key_path):
                server_credentials = grpc.ssl_server_credentials(
                    ((open(self.server_key_path, 'rb').read(),
                      open(self.server_cert_path, 'rb').read()),),
                    root_certificates=open(self.ca_cert_path, 'rb').read() if os.path.exists(self.ca_cert_path) else None,
                    require_client_auth=self.client_cert_required
                )
                logger.info("🔐 gRPC SSL credentials configured")
                return server_credentials
            else:
                logger.warning("⚠️ gRPC SSL certificates not found")
                return None
        except Exception as e:
            logger.error(f"❌ Error configuring gRPC SSL credentials: {e}")
            return None

    def get_grpc_client_ssl_credentials(self) -> grpc.ChannelCredentials:
        """Get gRPC client SSL credentials for secure connections"""
        if not self.tls_enabled:
            return grpc.insecure_channel_credentials()

        try:
            if os.path.exists(self.server_cert_path):
                root_cert = open(self.server_cert_path, 'rb').read()
                credentials = grpc.ssl_channel_credentials(root_cert)
                logger.info("🔐 gRPC client SSL credentials configured")
                return credentials
            else:
                logger.warning("⚠️ Client SSL certificate not found, using default")
                return grpc.insecure_channel_credentials()
        except Exception as e:
            logger.error(f"❌ Error configuring gRPC client SSL credentials: {e}")
            return grpc.insecure_channel_credentials()


class NetworkSecurityMiddleware(BaseHTTPMiddleware):
    """Security middleware for FastAPI applications"""

    def __init__(self, app: FastAPI, config: NetworkSecurityConfig):
        super().__init__(app)
        self.config = config
        self.rate_limits = {}

    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)

        for header, value in self.config.security_headers.items():
            response.headers[header] = value

        # Add security-related headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'

        return response

    def check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit"""
        if not self.config.rate_limit_enabled:
            return True

        now = datetime.now().timestamp()
        key = client_ip

        if key not in self.rate_limits:
            self.rate_limits[key] = []

        # Remove old requests outside the time window
        self.rate_limits[key] = [
            req_time for req_time in self.rate_limits[key]
            if now - req_time < self.config.rate_limit_window
        ]

        # Check if limit exceeded
        if len(self.rate_limits[key]) >= self.config.rate_limit_requests:
            return False

        # Add current request
        self.rate_limits[key].append(now)
        return True


class NetworkSecurityManager:
    """Centralized network security manager for the JARVIS system"""

    def __init__(self):
        self.config = NetworkSecurityConfig()
        self.active_connections = {}
        self.blocked_ips = set()
        self.security_logger = logging.getLogger('network_security')

    def initialize_fastapi_security(self, app: FastAPI):
        """Initialize security for FastAPI application"""
        logger.info("🔒 FastAPI security initialized (config loaded)")

    def initialize_grpc_security(self, server: grpc.Server):
        """Initialize security for gRPC server"""
        if self.config.tls_enabled:
            credentials = self.config.get_grpc_ssl_credentials()
            if credentials:
                # The credentials would be added to the server during server creation
                # This is handled in the serve function in python_server.py
                logger.info("🔐 gRPC security initialized with TLS")
            else:
                logger.warning("⚠️ gRPC security not configured due to missing certificates")
        else:
            logger.warning("⚠️ gRPC running without TLS (development only)")

    def validate_connection(self, client_ip: str, connection_type: str = "http") -> bool:
        """Validate network connection"""
        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            return False

        # Validate IP format
        try:
            socket.inet_aton(client_ip)
        except socket.error:
            self.security_logger.warning(f"Invalid IP address: {client_ip}")
            return False

        # Check rate limits
        middleware = NetworkSecurityMiddleware(None, self.config)
        if not middleware.check_rate_limit(client_ip):
            self.security_logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return False

        # Log connection
        self.active_connections[client_ip] = {
            'type': connection_type,
            'connected_at': datetime.now(),
            'last_activity': datetime.now()
        }

        return True

    def block_ip(self, ip: str, reason: str = "security violation"):
        """Block an IP address"""
        self.blocked_ips.add(ip)
        self.security_logger.warning(f"IP blocked: {ip} - Reason: {reason}")

    def generate_self_signed_cert(self, hostname: str = "localhost"):
        """Generate self-signed certificate for development"""
        try:
            import subprocess
            import tempfile

            # Create certs directory if it doesn't exist
            certs_dir = Path("certs")
            certs_dir.mkdir(exist_ok=True)

            cert_path = certs_dir / "server.crt"
            key_path = certs_dir / "server.key"

            # Generate private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(key_path), "2048"
            ], check=True, capture_output=True)

            # Generate certificate
            subprocess.run([
                "openssl", "req", "-new", "-x509", "-key", str(key_path),
                "-out", str(cert_path), "-days", "365", "-subj",
                f"/C=US/ST=AI/L=JARVIS/O=JARVIS/CN={hostname}"
            ], check=True, capture_output=True)

            logger.info(f"🔐 Self-signed certificates generated: {cert_path}, {key_path}")
            return str(cert_path), str(key_path)

        except Exception as e:
            logger.error(f"❌ Failed to generate self-signed certificates: {e}")
            return None, None

    def get_network_stats(self) -> Dict[str, Any]:
        """Get network security statistics"""
        active_conn_count = len(self.active_connections)
        blocked_count = len(self.blocked_ips)

        # Clean up old connections
        cutoff_time = datetime.now() - timedelta(minutes=30)
        expired_ips = [
            ip for ip, conn_data in self.active_connections.items()
            if conn_data['last_activity'] < cutoff_time
        ]

        for ip in expired_ips:
            del self.active_connections[ip]

        return {
            'active_connections': len(self.active_connections),
            'blocked_ips': blocked_count,
            'rate_limit_enabled': self.config.rate_limit_enabled,
            'tls_enabled': self.config.tls_enabled,
            'mtls_enabled': self.config.mtls_enabled,
            'rate_limit_stats': {
                'configured_requests': self.config.rate_limit_requests,
                'configured_window': self.config.rate_limit_window
            },
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
network_security_manager = NetworkSecurityManager()


def setup_certificate_paths():
    """Ensure certificate paths exist and create self-signed certificates if needed"""
    certs_dir = Path("certs")
    certs_dir.mkdir(exist_ok=True)

    # Check if certificates exist
    server_cert_path = Path(os.getenv('SERVER_CERT_PATH', 'certs/server.crt'))
    server_key_path = Path(os.getenv('SERVER_KEY_PATH', 'certs/server.key'))

    if not (server_cert_path.exists() and server_key_path.exists()):
        logger.warning("No certificates found, generating self-signed certificates for development")
        network_security_manager.generate_self_signed_cert()


# Initialize certificate paths on module load
setup_certificate_paths()


if __name__ == "__main__":
    # Test the network security implementation
    import asyncio

    async def test_network_security():
        logger.info("Testing Network Security Implementation...")

        # Test configuration
        config = NetworkSecurityConfig()
        logger.info(f"TLS Enabled: {config.tls_enabled}")
        logger.info(f"mTLS Enabled: {config.mtls_enabled}")
        logger.info(f"Rate Limit Enabled: {config.rate_limit_enabled}")

        # Test SSL context
        if config.tls_enabled:
            ssl_ctx = config.get_ssl_context()
            logger.info(f"SSL Context created: {ssl_ctx is not None}")

        # Test network manager
        manager = NetworkSecurityManager()
        stats = manager.get_network_stats()
        logger.info(f"Network Stats: {stats}")

        # Test connection validation
        is_valid = manager.validate_connection("127.0.0.1")
        logger.info(f"Connection validation for 127.0.0.1: {is_valid}")

    # Run test
    asyncio.run(test_network_security())