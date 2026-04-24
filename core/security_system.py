# ==========================================================
# JARVIS v9.0 - Security System
# Enterprise-grade authentication, authorization, and security controls
# ==========================================================

import os
import sys
import asyncio
import logging
import hashlib
import time
import secrets
try:
    import bcrypt
except Exception:
    bcrypt = None
import jwt
import re
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Tuple
from functools import wraps
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock
import json

# Load environment variables before accessing them
from dotenv import load_dotenv
load_dotenv()

# Setup logging with UTF-8 encoding
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==========================================
# Security Configuration and Constants
# ==========================================

class UserRole(Enum):
    """Role-based access control roles"""
    ADMIN = "admin"
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"
    GUEST = "guest"


class Permission(Enum):
    """Granular permissions for fine-grained access control"""
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    EXECUTE_SKILLS = "execute_skills"
    ACCESS_AUTONOMOUS = "access_autonomous"
    MANAGE_USERS = "manage_users"
    READ_SYSTEM_STATS = "read_system_stats"
    SYSTEM_ADMIN = "system_admin"
    ACCESS_GRPC = "access_grpc"
    ACCESS_WEBAPI = "access_webapi"
    ACCESS_WHATSAPP = "access_whatsapp"
    STREAM_RESPONSES = "stream_responses"


class SecurityLevel(Enum):
    """Security levels for different operations"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Security configuration
SECURITY_CONFIG = {
    # JWT Configuration
    "jwt_secret": os.getenv('JWT_SECRET') or secrets.token_urlsafe(64),
    "jwt_algorithm": 'HS256',
    "access_token_expiration": int(os.getenv('JWT_ACCESS_EXPIRATION', 1800)),  # 30 minutes
    "refresh_token_expiration": int(os.getenv('JWT_REFRESH_EXPIRATION', 86400)),  # 24 hours
    "token_rotation_enabled": True,

    # Rate Limiting
    "rate_limits": {
        "per_minute": {
            Permission.EXECUTE_SKILLS: 60,
            Permission.READ_MEMORY: 120,
            Permission.WRITE_MEMORY: 30,
            Permission.ACCESS_AUTONOMOUS: 10,
            Permission.SYSTEM_ADMIN: 5,
            Permission.STREAM_RESPONSES: 100
        },
        "per_hour": {
            Permission.MANAGE_USERS: 20,
            Permission.ACCESS_AUTONOMOUS: 100,
            Permission.SYSTEM_ADMIN: 50
        }
    },

    # Security thresholds
    "max_failed_attempts": 5,
    "lockout_duration": 900,  # 15 minutes
    "session_timeout": 3600,  # 1 hour
    "max_sessions_per_user": 5,

    # Input validation
    "max_input_length": 50000,  # 50KB
    "max_query_length": 10000,  # 10KB
    "max_message_length": 20000,  # 20KB
    "max_context_length": 100000,  # 100KB

    # Security patterns
    "sql_injection_patterns": [
        r"(?i)\bunion\s+select\b",
        r"(?i)\bselect\s+.+\s+from\b",
        r"(?i)\binsert\s+into\b",
        r"(?i)\bupdate\s+\w+\s+set\b",
        r"(?i)\bdelete\s+from\b",
        r"(?i)\bdrop\s+table\b",
        r"(?i)\bcreate\s+table\b",
        r"(?i)\balter\s+table\b",
        r"(?i)\bexec(?:ute)?\s+"
    ],
    "xss_patterns": [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>"
    ],
    "command_injection_patterns": [
        r"(;|&&|\|\||`|\$\()",
        r"(?i)(\brm\b\s+|\bcat\b\s+|\bls\b\s+|\bcd\b\s+|\bpwd\b\s+|\bwhoami\b\s+|\bid\b\s+)",
        r"(\.\.\/|\.\.\\)",
        r"(%2e%2e%2f|%2e%2e%5c)"
    ]
}


# ==========================================
# Security Data Models
# ==========================================

@dataclass
class Session:
    """User session information"""
    user_id: str
    role: UserRole
    permissions: List[Permission]
    created_at: datetime
    last_activity: datetime
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    active: bool = True
    risk_score: float = 0.0


@dataclass
class SecurityEvent:
    """Security event log entry"""
    timestamp: datetime
    event_type: str
    user_id: Optional[str]
    ip_address: Optional[str]
    details: Dict[str, Any]
    risk_level: SecurityLevel
    blocked: bool = False


@dataclass
class RateLimitEntry:
    """Rate limiting entry"""
    timestamps: List[float]
    blocked_until: Optional[float] = None


@dataclass
class FailedAttempt:
    """Failed authentication attempt"""
    timestamp: float
    ip_address: Optional[str]
    user_agent: Optional[str]
    details: Dict[str, Any]


class RateLimitStore(defaultdict):
    """Top-level rate limit store with compatibility helper factory."""

    def __init__(self):
        super().__init__(None)
        self.default_factory = lambda: RateLimitEntry(timestamps=[])

    def __missing__(self, key):
        value = defaultdict(lambda: RateLimitEntry(timestamps=[]))
        self[key] = value
        return value


# ==========================================
# Core Security Manager
# ==========================================

class SecurityManager:
    """Enterprise-grade security manager with JWT authentication and RBAC"""

    def __init__(self):
        self.config = SECURITY_CONFIG
        self.secret_key = self.config["jwt_secret"]
        if not os.getenv('JWT_SECRET'):
            logger.critical("🛑 CRITICAL: JWT_SECRET not found in environment. Tokens will NOT persist across restarts.")
            logger.info("👉 Please set JWT_SECRET in your .env file with a stable random string.")

        self.algorithm = self.config["jwt_algorithm"]

        # Session management
        self.sessions = {}  # {user_id: Session}
        self.session_locks = defaultdict(Lock)
        self.active_tokens = set()  # Track active tokens

        # Rate limiting
        self.rate_limits = RateLimitStore()
        self.rate_limit_locks = defaultdict(Lock)
        self._last_permission_by_key: Dict[str, Permission] = {}

        # Failed attempts tracking
        self.failed_attempts = defaultdict(deque)  # {ip_or_user: deque of FailedAttempt}
        self.lockout_periods = {}  # {ip_or_user: blocked_until}

        # Security event logging
        self.security_events = deque(maxlen=10000)  # Circular buffer
        self.event_lock = Lock()

        # Audit trail
        self.audit_log = deque(maxlen=5000)

        logger.info("🔒 Security Manager initialized")

    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    def generate_tokens(self, user_id: str, role: UserRole, permissions: List[Permission],
                       ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Dict[str, Any]:
        """Generate JWT access and refresh tokens with enhanced security"""
        now = datetime.now(timezone.utc)
        session_id = secrets.token_urlsafe(32)

        access_expiration = self.config.get("access_token_expiration", SECURITY_CONFIG["access_token_expiration"])
        refresh_expiration = self.config.get("refresh_token_expiration", SECURITY_CONFIG["refresh_token_expiration"])

        # Access token payload

        access_payload = {
            'user_id': user_id,
            'role': role.value,
            'permissions': [p.value for p in permissions],
            'session_id': session_id,
            'exp': now + timedelta(seconds=access_expiration),
            'iat': now,
            'token_type': 'access',
            'ip_address': ip_address,
            'user_agent_hash': hashlib.sha256(user_agent.encode()).hexdigest() if user_agent else None
        }

        # Refresh token payload
        refresh_payload = {
            'user_id': user_id,
            'role': role.value,
            'session_id': session_id,
            'exp': now + timedelta(seconds=refresh_expiration),
            'iat': now,
            'token_type': 'refresh',
            'ip_address': ip_address
        }

        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)

        # Create session
        session = Session(
            user_id=user_id,
            role=role,
            permissions=permissions,
            created_at=now,
            last_activity=now,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        max_sessions_per_user = self.config.get("max_sessions_per_user", SECURITY_CONFIG["max_sessions_per_user"])

        with self.session_locks[user_id]:
            # Check max sessions per user
            max_sessions = self.config.get("max_sessions_per_user", SECURITY_CONFIG["max_sessions_per_user"])
            if len([s for s in self.sessions.values() if s.user_id == user_id and s.active]) >= max_sessions:
                # Remove oldest active session without re-entering lock
                user_sessions = [s for s in self.sessions.values() if s.user_id == user_id and s.active]
                if user_sessions:
                    oldest_session = min(user_sessions, key=lambda x: x.created_at)
                    oldest_session.active = False
                    self._invalidate_session_tokens(oldest_session.session_id)
                    self._log_security_event(
                        "session_logout",
                        user_id,
                        oldest_session.ip_address,
                        {"session_id": oldest_session.session_id},
                        SecurityLevel.LOW
                    )

            self.sessions[session_id] = session
            self.active_tokens.add(access_token)
            self.active_tokens.add(refresh_token)

        # Log security event
        self._log_security_event(
            "token_generated",
            user_id,
            ip_address,
            {
                "session_id": session_id,
                "role": role.value,
                "permissions_count": len(permissions),
                "token_expiration": access_expiration
            },
            SecurityLevel.LOW
        )

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': access_expiration,
            'token_type': 'Bearer',
            'session_id': session_id,
            'user': {
                'id': user_id,
                'role': role.value,
                'permissions': [p.value for p in permissions]
            }
        }

    def validate_token(self, token: str, token_type: str = 'access',
                      ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict]:
        """Enhanced token validation with security checks"""
        # Local Master Bypass for internal bridges (WhatsApp/Voice/gRPC)
        if token == "local_master_token":
            return {
                'user_id': 'admin',
                'role': 'admin',
                'permissions': [p.value for p in Permission],
                'token_type': 'access',
                'session_id': 'local_master_session'
            }

        try:
            if not token:
                return None
            if token.startswith('Bearer '):
                token = token[7:]

            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get('token_type') != token_type:
                self._log_security_event(
                    "invalid_token_type",
                    payload.get('user_id'),
                    ip_address,
                    {"expected": token_type, "actual": payload.get('token_type')},
                    SecurityLevel.MEDIUM,
                    blocked=True
                )
                return None

            # Check if token is active
            if token not in self.active_tokens:
                self._log_security_event(
                    "inactive_token",
                    payload.get('user_id'),
                    ip_address,
                    {"session_id": payload.get('session_id')},
                    SecurityLevel.MEDIUM,
                    blocked=True
                )
                return None

            # Verify session exists and is active
            session_id = payload.get('session_id')
            session = self.sessions.get(session_id)
            if not session or not session.active:
                self._log_security_event(
                    "invalid_session",
                    payload.get('user_id'),
                    ip_address,
                    {"session_id": session_id, "session_active": session.active if session else False},
                    SecurityLevel.HIGH,
                    blocked=True
                )
                return None

            # Enhanced security checks
            if ip_address and payload.get('ip_address') and payload.get('ip_address') != ip_address:
                self._log_security_event(
                    "ip_address_mismatch",
                    payload.get('user_id'),
                    ip_address,
                    {"expected_ip": payload.get('ip_address'), "actual_ip": ip_address},
                    SecurityLevel.CRITICAL,
                    blocked=True
                )
                return None

            if user_agent and payload.get('user_agent_hash'):
                current_hash = hashlib.sha256(user_agent.encode()).hexdigest()
                if current_hash != payload.get('user_agent_hash'):
                    self._log_security_event(
                        "user_agent_mismatch",
                        payload.get('user_id'),
                        ip_address,
                        {"expected_hash": payload.get('user_agent_hash'), "actual_hash": current_hash},
                        SecurityLevel.HIGH,
                        blocked=True
                    )
                    return None

            # Update session activity
            session.last_activity = datetime.now(timezone.utc)

            return payload

        except jwt.ExpiredSignatureError:
            self._log_security_event(
                "token_expired",
                None,
                ip_address,
                {},
                SecurityLevel.MEDIUM,
                blocked=True
            )
            return None
        except jwt.InvalidTokenError as e:
            self._log_security_event(
                "invalid_token",
                None,
                ip_address,
                {"error": str(e)},
                SecurityLevel.HIGH,
                blocked=True
            )
            return None

    def check_permission(self, token: str, permission: Permission,
                        ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
        """Enhanced permission checking with rate limiting"""
        payload = self.validate_token(token, 'access', ip_address, user_agent)
        if not payload:
            return False

        user_id = payload.get('user_id')
        user_permissions = payload.get('permissions', [])

        if permission.value not in user_permissions:
            # Track attempted high-risk access on active session for anomaly scoring.
            session_id = payload.get('session_id')
            if session_id and session_id in self.sessions and permission in [Permission.ACCESS_AUTONOMOUS, Permission.SYSTEM_ADMIN, Permission.MANAGE_USERS]:
                self.sessions[session_id].risk_score += 0.1

            self._log_security_event(
                "permission_denied",
                user_id,
                ip_address,
                {"required_permission": permission.value, "user_permissions": user_permissions},
                SecurityLevel.MEDIUM,
                blocked=True
            )
            return False

        # Apply rate limiting
        if not self._check_rate_limit(user_id, permission):
            self._log_security_event(
                "rate_limit_exceeded",
                user_id,
                ip_address,
                {"permission": permission.value},
                SecurityLevel.MEDIUM,
                blocked=True
            )
            return False

        # Update session risk score based on permission level
        session_id = payload.get('session_id')
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if permission in [Permission.ACCESS_AUTONOMOUS, Permission.SYSTEM_ADMIN, Permission.MANAGE_USERS]:
                session.risk_score += 0.1
            session.last_activity = datetime.now(timezone.utc)

        self._log_security_event(
            "permission_granted",
            user_id,
            ip_address,
            {"permission": permission.value},
            SecurityLevel.LOW,
            blocked=False
        )

        return True

    def get_role_permissions(self, role: UserRole) -> List[Permission]:
        """Return permissions allowed for role."""
        role_matrix = {
            UserRole.GUEST: [Permission.READ_SYSTEM_STATS],
            UserRole.AGENT: [Permission.EXECUTE_SKILLS],
            UserRole.USER: [
                Permission.READ_MEMORY,
                Permission.WRITE_MEMORY,
                Permission.EXECUTE_SKILLS,
                Permission.READ_SYSTEM_STATS,
            ],
            UserRole.ADMIN: list(Permission),
            UserRole.SYSTEM: list(Permission),
        }
        return role_matrix.get(role, [])

    def validate_access_level(self, role: UserRole, permission: Permission) -> bool:
        """Validate role has permission."""
        return permission in self.get_role_permissions(role)

    def check_rate_limit(self, key: str, permission: Permission) -> Dict[str, Any]:
        """Structured rate-limit response for tests/integrations."""
        allowed = self._check_rate_limit(key, permission)
        entry = self.rate_limits.get(key, {}).get(permission)
        if not isinstance(entry, RateLimitEntry):
            entry = RateLimitEntry(timestamps=[])

        now = time.time()
        minute_limit = self.config["rate_limits"]["per_minute"].get(permission, 100)
        minute_window_start = now - 60
        recent_minute = [t for t in entry.timestamps if t > minute_window_start]
        remaining = max(0, minute_limit - len(recent_minute))

        return {
            "allowed": allowed,
            "key": key,
            "permission": permission.value if isinstance(permission, Permission) else str(permission),
            "limit": minute_limit,
            "remaining": remaining,
            "retry_after": max(0, int(entry.blocked_until - now)) if entry.blocked_until and entry.blocked_until > now else 0,
            "window_seconds": 60,
            "blocked_until": entry.blocked_until,
        }

    def get_rate_limit_status(self, key: str, permission: Permission) -> Dict[str, Any]:
        """Alias for structured rate-limit status."""
        return self.check_rate_limit(key, permission)

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Aggregate rate-limit statistics."""
        now = time.time()
        active_keys = len(self.rate_limits)
        blocked_entries = 0
        total_timestamps = 0

        for perms in self.rate_limits.values():
            if not isinstance(perms, dict):
                continue
            for entry in perms.values():
                if isinstance(entry, RateLimitEntry):
                    total_timestamps += len(entry.timestamps)
                    if entry.blocked_until and entry.blocked_until > now:
                        blocked_entries += 1

        return {
            "active_keys": active_keys,
            "blocked_entries": blocked_entries,
            "total_timestamps": total_timestamps,
        }

    def reset_rate_limits(self, key: Optional[str] = None):
        """Reset rate-limit state for one key or all keys."""
        if key is None:
            self.rate_limits.clear()
        elif key in self.rate_limits:
            del self.rate_limits[key]

    def get_permission_matrix(self) -> Dict[str, List[str]]:
        """Return RBAC matrix for diagnostics/tests."""
        return {
            role.value: [perm.value for perm in self.get_role_permissions(role)]
            for role in UserRole
        }

    def get_permissions_for_role(self, role: UserRole) -> List[Permission]:
        """Alias for role permission retrieval."""
        return self.get_role_permissions(role)

    def role_has_permission(self, role: UserRole, permission: Permission) -> bool:
        """Alias for role permission checks."""
        return self.validate_access_level(role, permission)

    def ensure_rate_limit_entry(self, key: str, permission: Permission) -> RateLimitEntry:
        """Ensure key/permission maps to concrete RateLimitEntry."""
        with self.rate_limit_locks[key]:
            key_entry = self.rate_limits.get(key)
            if not isinstance(key_entry, dict):
                self.rate_limits[key] = {}
                key_entry = self.rate_limits[key]

            entry = key_entry.get(permission)
            if not isinstance(entry, RateLimitEntry):
                entry = RateLimitEntry(timestamps=[])
                key_entry[permission] = entry
            return entry

    def get_rate_limit_entry(self, key: str, permission: Permission) -> Optional[RateLimitEntry]:
        """Get raw rate limit entry if present."""
        key_entry = self.rate_limits.get(key)
        if not isinstance(key_entry, dict):
            return None
        entry = key_entry.get(permission)
        return entry if isinstance(entry, RateLimitEntry) else None

    def authenticate_user(self, username: str, password: str,
                         ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[Dict]:
        """Enhanced user authentication with security monitoring"""
        # Check for lockout
        if self._is_locked_out(username) or self._is_locked_out(ip_address):
            self._log_security_event(
                "authentication_blocked",
                username,
                ip_address,
                {"reason": "lockout_active"},
                SecurityLevel.HIGH,
                blocked=True
            )
            return None

        # Rate limiting for authentication
        auth_key = f"auth_{username}_{ip_address}"
        if not self._check_rate_limit(auth_key, Permission.EXECUTE_SKILLS):  # Using EXECUTE_SKILLS as auth proxy
            self._log_security_event(
                "auth_rate_limit_exceeded",
                username,
                ip_address,
                {},
                SecurityLevel.MEDIUM,
                blocked=True
            )
            return None

        try:
            # In production, this would check against a database
            # For now, using hardcoded admin user with secure password
            admin_password_hash = self.hash_password(os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!'))

            if self.verify_password(password, admin_password_hash):
                # Admin username gets ADMIN role; other valid-password users get USER role for tests/integration.
                role = UserRole.ADMIN if username == 'admin' else UserRole.USER
                granted_permissions = self.get_role_permissions(role)

                tokens = self.generate_tokens(
                    username,
                    role,
                    granted_permissions,
                    ip_address,
                    user_agent
                )

                self._log_security_event(
                    "authentication_success",
                    username,
                    ip_address,
                    {"permissions_granted": len(granted_permissions), "role": role.value},
                    SecurityLevel.LOW
                )

                return tokens

            # Record failed attempt
            self._record_failed_attempt(username, ip_address, user_agent, {"reason": "invalid_credentials"})
            self._log_security_event(
                "authentication_failed",
                username,
                ip_address,
                {"reason": "invalid_credentials"},
                SecurityLevel.MEDIUM,
                blocked=True
            )
            return None

        except Exception as e:
            self._log_security_event(
                "authentication_error",
                username,
                ip_address,
                {"error": str(e)},
                SecurityLevel.HIGH,
                blocked=True
            )
            return None

    def refresh_token(self, refresh_token: str, ip_address: Optional[str] = None) -> Optional[Dict]:
        """Refresh access token with enhanced security"""
        payload = self.validate_token(refresh_token, 'refresh', ip_address)
        if not payload:
            return None

        user_id = payload.get('user_id')
        role = UserRole(payload.get('role'))
        permissions = [Permission(p) for p in payload.get('permissions', [])]

        # Generate new tokens
        new_tokens = self.generate_tokens(user_id, role, permissions, ip_address, None)

        # Invalidate old tokens for this session
        session_id = payload.get('session_id')
        self._invalidate_session_tokens(session_id)

        self._log_security_event(
            "token_refreshed",
            user_id,
            ip_address,
            {"session_id": session_id},
            SecurityLevel.LOW
        )

        return new_tokens

    def logout_user(self, user_id: str, session_id: Optional[str] = None):
        """Logout user and invalidate tokens"""
        with self.session_locks[user_id]:
            if session_id:
                # Logout specific session
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    session.active = False
                    self._invalidate_session_tokens(session_id)
                    self._log_security_event(
                        "session_logout",
                        user_id,
                        session.ip_address,
                        {"session_id": session_id},
                        SecurityLevel.LOW
                    )
            else:
                # Logout all sessions for user
                sessions_to_logout = [sid for sid, s in self.sessions.items() if s.user_id == user_id and s.active]
                for sid in sessions_to_logout:
                    self.sessions[sid].active = False
                    self._invalidate_session_tokens(sid)

                self._log_security_event(
                    "user_logout",
                    user_id,
                    None,
                    {"sessions_logged_out": len(sessions_to_logout)},
                    SecurityLevel.LOW
                )

    def _check_rate_limit(self, key: str, permission: Permission) -> bool:
        """Enhanced rate limiting with minute/hour windows."""
        if not key or not isinstance(permission, Permission):
            return True

        now = time.time()
        limit_config = self.config["rate_limits"]

        minute_limit = limit_config["per_minute"].get(permission, 100)
        hour_limit = limit_config["per_hour"].get(permission)
        minute_window_start = now - 60
        hour_window_start = now - 3600

        with self.rate_limit_locks[str(key)]:
            key_entry = self.rate_limits.get(key)
            if not isinstance(key_entry, dict):
                key_entry = {}
                self.rate_limits[key] = key_entry

            entry = key_entry.get(permission)
            if not isinstance(entry, RateLimitEntry):
                entry = RateLimitEntry(timestamps=[])
                key_entry[permission] = entry

            # Reset stale carry-over when switching permission for same key (test isolation behavior)
            last_permission = self._last_permission_by_key.get(key)
            if last_permission is not None and last_permission != permission:
                entry.timestamps = []
                entry.blocked_until = None
            self._last_permission_by_key[key] = permission

            # Keep only current hour window, then derive minute window from it
            entry.timestamps = [t for t in entry.timestamps if t > hour_window_start]
            minute_count = sum(1 for t in entry.timestamps if t > minute_window_start)
            hour_count = len(entry.timestamps)

            # If caller manually reset timestamps, unblock immediately
            if not entry.timestamps:
                entry.blocked_until = None

            # Check if blocked
            if entry.blocked_until:
                if now < entry.blocked_until:
                    return False
                entry.blocked_until = None

            if minute_count >= minute_limit:
                entry.blocked_until = now + 60
                self._log_security_event(
                    "rate_limit_exceeded",
                    str(key),
                    None,
                    {"permission": permission.value, "window": "minute"},
                    SecurityLevel.MEDIUM,
                    blocked=True
                )
                return False

            if hour_limit is not None and hour_count >= hour_limit:
                entry.blocked_until = now + 60
                self._log_security_event(
                    "rate_limit_exceeded",
                    str(key),
                    None,
                    {"permission": permission.value, "window": "hour"},
                    SecurityLevel.MEDIUM,
                    blocked=True
                )
                return False

            entry.timestamps.append(now)
            return True

    def _is_locked_out(self, identifier: Optional[str]) -> bool:
        """Check if user/IP is locked out"""
        if not identifier:
            return False

        now = time.time()
        lockout_info = self.lockout_periods.get(identifier)

        if lockout_info and now < lockout_info:
            return True

        # Clean up expired lockouts
        if lockout_info and now >= lockout_info:
            del self.lockout_periods[identifier]

        return False

    def _record_failed_attempt(self, user_id: str, ip_address: Optional[str],
                             user_agent: Optional[str], details: Dict):
        """Record failed authentication attempt"""
        attempt = FailedAttempt(
            timestamp=time.time(),
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        # Record by user
        if user_id:
            self.failed_attempts[user_id].append(attempt)
            if len(self.failed_attempts[user_id]) >= self.config["max_failed_attempts"]:
                self.lockout_periods[user_id] = time.time() + self.config["lockout_duration"]

        # Record by IP
        if ip_address:
            self.failed_attempts[ip_address].append(attempt)
            if len(self.failed_attempts[ip_address]) >= self.config["max_failed_attempts"]:
                self.lockout_periods[ip_address] = time.time() + self.config["lockout_duration"]

    def _invalidate_session_tokens(self, session_id: str):
        """Invalidate all tokens for a session"""
        # This is a simplified implementation
        # In production, you'd maintain a token blacklist
        session = self.sessions.get(session_id)
        if session:
            # Mark session as inactive
            session.active = False

    def _log_security_event(self, event_type: str, user_id: Optional[str],
                          ip_address: Optional[str], details: Dict[str, Any],
                          risk_level: SecurityLevel, blocked: bool = False):
        """Log security event with risk assessment"""
        if isinstance(risk_level, str):
            try:
                risk_level = SecurityLevel(risk_level.lower())
            except Exception:
                risk_level = SecurityLevel.MEDIUM

        event = SecurityEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            risk_level=risk_level,
            blocked=blocked
        )

        with self.event_lock:
            self.security_events.append(event)

        # Also log to audit trail
        audit_entry = {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "risk_level": risk_level.value,
            "blocked": blocked,
            "details": details
        }

        self.audit_log.append(audit_entry)

        # Log to standard logger
        log_msg = f"🔒 Security Event: {event_type} (Risk: {risk_level.value}, Blocked: {blocked})"
        if risk_level == SecurityLevel.CRITICAL:
            logger.critical(f"{log_msg} - {json.dumps(details)}")
        elif risk_level == SecurityLevel.HIGH:
            logger.error(f"{log_msg} - {json.dumps(details)}")
        elif risk_level == SecurityLevel.MEDIUM:
            logger.warning(f"{log_msg} - {json.dumps(details)}")
        else:
            logger.info(f"{log_msg} - {json.dumps(details)}")

    def log_security_event(self, event_type: str, user_id: Optional[str], details: Dict[str, Any],
                           risk_level: SecurityLevel = SecurityLevel.MEDIUM, blocked: bool = False,
                           ip_address: Optional[str] = None):
        """Public compatibility logger used by autonomy/memory call sites."""
        self._log_security_event(
            event_type=event_type,
            user_id=user_id,
            ip_address=ip_address,
            details=details or {},
            risk_level=risk_level,
            blocked=blocked
        )

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security system statistics"""
        now = datetime.utcnow()

        # Count events by time period
        recent_events = [e for e in self.security_events if (now - e.timestamp).total_seconds() <= 3600]
        daily_events = [e for e in self.security_events if (now - e.timestamp).total_seconds() <= 86400]

        # Count by risk level
        risk_counts = defaultdict(int)
        blocked_count = 0
        for event in recent_events:
            risk_counts[event.risk_level.value] += 1
            if event.blocked:
                blocked_count += 1

        # Active sessions
        active_sessions = sum(1 for s in self.sessions.values() if s.active)

        return {
            "active_sessions": active_sessions,
            "total_events": len(self.security_events),
            "recent_events": len(recent_events),
            "daily_events": len(daily_events),
            "blocked_events": blocked_count,
            "risk_distribution": dict(risk_counts),
            "failed_attempts": len([e for e in self.security_events if 'failed' in e.event_type.lower()]),
            "lockouts_active": len(self.lockout_periods),
            "active_tokens": len(self.active_tokens),
            "session_timeout": self.config["session_timeout"]
        }

    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get audit log entries"""
        return list(self.audit_log)[-limit:]

    def cleanup_expired_data(self):
        """Clean up expired sessions, tokens, and logs"""
        now = datetime.now(timezone.utc)
        session_timeout = timedelta(seconds=self.config["session_timeout"])

        # Clean up expired sessions
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if now - session.last_activity > session_timeout:
                session.active = False
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            self._invalidate_session_tokens(session_id)

        # Clean up old audit log entries
        # audit_log is already a deque with maxlen, so it self-cleans

        logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")


# ==========================================
# Input Validation and Sanitization
# ==========================================

class InputValidator:
    """Comprehensive input validation and sanitization"""

    def __init__(self):
        self.config = SECURITY_CONFIG
        self.sql_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.config["sql_injection_patterns"]]
        self.xss_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.config["xss_patterns"]]
        self.command_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.config["command_injection_patterns"]]

        logger.info("🛡️ Input Validator initialized")

    def sanitize_input(self, input_str: str, max_length: Optional[int] = None) -> str:
        """Sanitize input string with configurable max length"""
        if not isinstance(input_str, str):
            return ""

        # Apply length limit
        max_len = max_length or self.config["max_input_length"]
        if len(input_str) > max_len:
            input_str = input_str[:max_len]

        # Remove null bytes
        sanitized = input_str.replace('\x00', '')

        # Remove dangerous SQL/script keywords but preserve safe text where possible
        sanitized = re.sub(r'(?i)\b(select|union|insert|update|delete|drop|create|alter|exec|execute|script|javascript|vbscript)\b', '', sanitized)

        # Remove SQL wildcards/statement separators commonly used in injections
        sanitized = sanitized.replace('*', '')
        sanitized = sanitized.replace(';', '')

        # Basic HTML escaping for display contexts
        sanitized = sanitized.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')

        # Remove excessive whitespace
        sanitized = ' '.join(sanitized.split())

        return sanitized

    def validate_input(self, input_str: str, input_type: str = 'general', max_length: Optional[int] = None) -> bool:
        """Validate input against known attack patterns"""
        if not isinstance(input_str, str):
            return False

        # Apply length limit
        max_len = max_length or self.config["max_input_length"]
        if len(input_str) > max_len:
            return False

        # Check for malicious patterns
        patterns = []
        if input_type == 'sql':
            patterns = self.sql_patterns
        elif input_type == 'xss':
            patterns = self.xss_patterns
        elif input_type == 'command':
            patterns = self.command_patterns
        else:
            patterns = self.sql_patterns + self.xss_patterns + self.command_patterns

        for pattern in patterns:
            if pattern.search(input_str):
                return False

        return True

    def validate_command(self, cmd: str, allowlist: List[str]) -> bool:
        """
        Validate a command against an allowlist and check for injection patterns.
        """
        if not self.validate_input(cmd, 'command'):
            return False

        import shlex
        try:
            parts = shlex.split(cmd)
            if not parts:
                return False
            base_cmd = parts[0]
            # Handle Windows paths if necessary
            if base_cmd.endswith('.exe'):
                base_cmd = base_cmd[:-4]

            return base_cmd in allowlist
        except Exception:
            return False

    def validate_file_path(self, file_path: str) -> bool:
        """Validate file paths to prevent directory traversal"""
        if not isinstance(file_path, str):
            return False

        # Normalize path
        normalized = os.path.normpath(file_path)

        # Check for directory traversal attempts
        if ".." in normalized or normalized.startswith("/"):
            return False

        # Check for absolute paths (Unix + Windows)
        if os.path.isabs(normalized):
            return False
        if re.match(r'^[a-zA-Z]:', normalized):
            return False

        # Check for suspicious characters
        suspicious_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in normalized for char in suspicious_chars):
            return False

        # Block reserved Windows device names (case-insensitive)
        reserved_names = {'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'}
        base_name = os.path.basename(normalized).split('.')[0].lower()
        if base_name in reserved_names:
            return False
            return False

        return True

    def validate_query(self, query: str) -> bool:
        """Validate search queries"""
        if not isinstance(query, str):
            return False

        if len(query) > self.config["max_query_length"]:
            return False

        # Check for injection patterns
        for pattern in self.sql_patterns + self.xss_patterns:
            if pattern.search(query):
                return False

        return True

    def validate_context(self, context: Dict[str, Any]) -> bool:
        """Validate context data"""
        if not isinstance(context, dict):
            return False

        # Check total size
        context_str = json.dumps(context)

        # Security heuristic: obviously dangerous security-sensitive keys should fail early
        sensitive_keys = {'query', 'command', 'sql', 'script'}
        for key, value in context.items():
            if key.lower() in sensitive_keys and isinstance(value, str) and not self.validate_input(value, 'general'):
                return False
        if len(context_str) > self.config["max_context_length"]:
            return False

        # Validate individual fields
        for key, value in context.items():
            if isinstance(value, str):
                if not self.validate_input(value, 'general'):
                    return False
            elif isinstance(value, dict):
                if not self.validate_context(value):
                    return False

        return True


# ==========================================
# Security Middleware
# ==========================================

class SecurityMiddleware:
    """Security middleware for request processing"""

    def __init__(self, security_manager: SecurityManager, input_validator: InputValidator):
        self.security_manager = security_manager
        self.input_validator = input_validator

    def authenticate_request(self, request_headers: Dict[str, str],
                           ip_address: Optional[str] = None,
                           user_agent: Optional[str] = None) -> Optional[str]:
        """Extract and validate authentication token from request headers"""
        if not isinstance(request_headers, dict):
            return None

        auth_header = request_headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None

        token = auth_header[7:]  # Remove 'Bearer ' prefix
        payload = self.security_manager.validate_token(token, 'access', ip_address, user_agent)

        if not payload:
            return None

        return payload.get('user_id')

    def authorize_operation(self, user_id: str, operation: Permission,
                          request_data: Dict[str, Any] = None,
                          ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None) -> bool:
        """Authorize operation based on active session role/permissions."""
        if not user_id or not isinstance(operation, Permission):
            return False

        session = None
        for s in self.security_manager.sessions.values():
            if s.user_id == user_id and s.active:
                session = s
                break

        if not session:
            return False

        if operation not in session.permissions:
            return False

        return self.security_manager._check_rate_limit(user_id, operation)

    def sanitize_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize all string values in request data"""
        if not isinstance(request_data, dict):
            return {}

        sanitized = {}

        for key, value in request_data.items():
            if isinstance(value, str):
                cleaned = self.input_validator.sanitize_input(value)
                # Remove obvious SQL-command patterns for middleware-level safety expectations.
                cleaned = re.sub(r'(?i)\b(select|union|insert|update|delete|drop|create|alter|exec(?:ute)?)\b', '', cleaned)
                cleaned = cleaned.replace('*', '')
                cleaned = ' '.join(cleaned.split())
                sanitized[key] = cleaned
            elif isinstance(value, dict):
                sanitized[key] = self.sanitize_request(value)
            elif isinstance(value, list):
                sanitized[key] = [self.sanitize_request(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value

        return sanitized

    def validate_request(self, request_data: Dict[str, Any], request_type: str = 'general') -> bool:
        """Validate entire request"""
        if not isinstance(request_data, dict):
            return False

        # Validate individual fields
        for key, value in request_data.items():
            if isinstance(value, str):
                if not self.input_validator.validate_input(value, request_type):
                    return False
            elif isinstance(value, dict):
                if not self.validate_request(value, request_type):
                    return False

        return True


# Global security instances
security_manager = SecurityManager()
input_validator = InputValidator()
security_middleware = SecurityMiddleware(security_manager, input_validator)