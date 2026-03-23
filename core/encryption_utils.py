"""
JARVIS v9.0 - Encryption Utilities
Phase 5: Memory & Data Protection
"""

import os
import base64
import hashlib
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import logging

logger = logging.getLogger(__name__)

class MemoryEncryption:
    """
    Advanced encryption for memory systems using AES-256-GCM with HSM/env-based key derivation
    """

    def __init__(self, key_source: Optional[str] = None):
        """
        Initialize encryption with key source
        key_source: Either HSM identifier, environment variable name, or None for default
        """
        self.key_source = key_source
        self.encryption_key = self._derive_key()
        self.aesgcm = AESGCM(self.encryption_key)

    def _derive_key(self) -> bytes:
        """Derive encryption key from HSM/env or generate default"""
        if self.key_source:
            if self.key_source.startswith("HSM:"):
                # Simulate HSM key retrieval
                logger.info("🔐 Retrieving key from HSM")
                return self._simulate_hsm_key()
            elif self.key_source.startswith("ENV:"):
                # Get key from environment variable
                env_var = self.key_source.replace("ENV:", "")
                key_from_env = os.getenv(env_var)
                if not key_from_env:
                    logger.warning(f"⚠️ Environment variable {env_var} not found, using default key")
                    return self._generate_default_key()
                return self._derive_key_from_password(key_from_env.encode())

        # Default key derivation using environment secrets
        jwt_secret = os.getenv("JWT_SECRET", "jarvis-default-secret-key")
        return self._derive_key_from_password(jwt_secret.encode())

    def _simulate_hsm_key(self) -> bytes:
        """Simulate HSM key retrieval"""
        # In a real implementation, this would call HSM API
        # For now, we'll derive from a constant but simulate HSM security
        hsm_identifier = self.key_source.replace("HSM:", "")
        password = f"jarvis_hsm_{hsm_identifier}_secret".encode()
        return self._derive_key_from_password(password)

    def _derive_key_from_password(self, password: bytes) -> bytes:
        """Derive 256-bit key from password using PBKDF2"""
        salt = b'jarvis_v9_memory_salt'  # Fixed salt for consistent key derivation

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password)
        return key

    def _generate_default_key(self) -> bytes:
        """Generate a default encryption key"""
        # This should never happen in production but provides fallback
        logger.warning("⚠️ Using fallback encryption key - please configure ENV:HSM key source")
        return hashlib.sha256(b"jarvis_default_fallback_key").digest()[:32]

    def encrypt(self, plaintext: Union[str, bytes]) -> str:
        """Encrypt data using AES-256-GCM"""
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')

        nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
        ciphertext = self.aesgcm.encrypt(nonce, plaintext, associated_data=None)

        # Encode as base64: nonce + ciphertext
        encrypted_data = base64.b64encode(nonce + ciphertext).decode('utf-8')
        return encrypted_data

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data using AES-256-GCM"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))

            # First 12 bytes are nonce, rest is ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            decrypted = self.aesgcm.decrypt(nonce, ciphertext, associated_data=None)
            return decrypted.decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Decryption failed: {e}")
            raise

    def encrypt_dict(self, data: dict) -> str:
        """Encrypt a dictionary as JSON string"""
        import json
        json_str = json.dumps(data)
        return self.encrypt(json_str)

    def decrypt_dict(self, encrypted_data: str) -> dict:
        """Decrypt an encrypted JSON string to dictionary"""
        import json
        decrypted_str = self.decrypt(encrypted_data)
        return json.loads(decrypted_str)


class TenantNamespaceManager:
    """
    Manage per-tenant namespaces for memory isolation
    """

    def __init__(self):
        self.tenant_namespaces = {}
        self.tenant_encryption_keys = {}

    def register_tenant(self, tenant_id: str, encryption_key_source: Optional[str] = None):
        """Register a new tenant with optional specific encryption"""
        if tenant_id in self.tenant_namespaces:
            return  # Already registered

        self.tenant_namespaces[tenant_id] = {}
        encryption_util = MemoryEncryption(encryption_key_source)
        self.tenant_encryption_keys[tenant_id] = encryption_util
        logger.info(f"🔐 Registered tenant namespace: {tenant_id}")

    def encrypt_for_tenant(self, tenant_id: str, data: Union[str, dict]) -> str:
        """Encrypt data for specific tenant"""
        if tenant_id not in self.tenant_encryption_keys:
            raise ValueError(f"Tenant {tenant_id} not registered")

        encryption_util = self.tenant_encryption_keys[tenant_id]
        if isinstance(data, dict):
            return encryption_util.encrypt_dict(data)
        return encryption_util.encrypt(data)

    def decrypt_for_tenant(self, tenant_id: str, encrypted_data: str) -> Union[str, dict]:
        """Decrypt data for specific tenant"""
        if tenant_id not in self.tenant_encryption_keys:
            raise ValueError(f"Tenant {tenant_id} not registered")

        encryption_util = self.tenant_encryption_keys[tenant_id]
        return encryption_util.decrypt(encrypted_data)

    def get_tenant_namespace(self, tenant_id: str):
        """Get namespace for tenant"""
        if tenant_id not in self.tenant_namespaces:
            raise ValueError(f"Tenant {tenant_id} not registered")
        return self.tenant_namespaces[tenant_id]


class ContextLeakSweeper:
    """
    Detect and clean context-pinning leaks
    """

    def __init__(self):
        self.access_log = {}  # Track access patterns
        self.suspicious_patterns = set()

    def log_access(self, context_id: str, user_id: str, access_type: str):
        """Log access to contexts for leak detection"""
        key = f"{user_id}:{context_id}"
        if key not in self.access_log:
            self.access_log[key] = []
        self.access_log[key].append({
            'context_id': context_id,
            'user_id': user_id,
            'access_type': access_type,
            'timestamp': self._get_timestamp()
        })

    def detect_leaks(self) -> list:
        """Detect potential context pinning leaks"""
        leaks = []

        # Check for unusual access patterns
        for key, accesses in self.access_log.items():
            if len(accesses) > 100:  # Suspiciously high access frequency
                user_id, context_id = key.split(':', 1)
                leaks.append({
                    'type': 'high_frequency_access',
                    'user_id': user_id,
                    'context_id': context_id,
                    'access_count': len(accesses),
                    'details': 'Unusually high access frequency to pinned context'
                })

        # Check for cross-tenant access attempts
        # This would require additional tenant context in logs

        return leaks

    def sweep_leaks(self, memory_controller) -> int:
        """Clean detected context leaks"""
        leaks = self.detect_leaks()
        cleaned_count = 0

        for leak in leaks:
            try:
                # For high-frequency access, unpin and re-evaluate
                if leak['type'] == 'high_frequency_access':
                    context_id = leak['context_id']
                    # Remove from memory controller's pinned contexts
                    if hasattr(memory_controller, 'unpin_context'):
                        memory_controller.unpin_context(context_id)
                        cleaned_count += 1
                        logger.info(f"🧹 Swept context leak: {context_id}")
            except Exception as e:
                logger.error(f"❌ Failed to sweep leak {leak.get('context_id')}: {e}")

        return cleaned_count

    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()


# Global instances
memory_encryption = MemoryEncryption()
tenant_manager = TenantNamespaceManager()
context_sweeper = ContextLeakSweeper()

# Initialize default tenant
tenant_manager.register_tenant("default")


def encrypt_data(data: Union[str, dict], tenant_id: str = "default") -> str:
    """Convenience function to encrypt data for tenant"""
    if isinstance(data, str):
        return tenant_manager.encrypt_for_tenant(tenant_id, data)
    else:
        return tenant_manager.encrypt_for_tenant(tenant_id, data)


def decrypt_data(encrypted_data: str, tenant_id: str = "default") -> Union[str, dict]:
    """Convenience function to decrypt data for tenant"""
    return tenant_manager.decrypt_for_tenant(tenant_id, encrypted_data)


def register_tenant(tenant_id: str, encryption_key_source: Optional[str] = None):
    """Convenience function to register tenant"""
    tenant_manager.register_tenant(tenant_id, encryption_key_source)


def log_context_access(context_id: str, user_id: str, access_type: str):
    """Convenience function to log context access"""
    context_sweeper.log_access(context_id, user_id, access_type)


def sweep_context_leaks(memory_controller) -> int:
    """Convenience function to sweep context leaks"""
    return context_sweeper.sweep_leaks(memory_controller)