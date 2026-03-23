#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - JWT Authentication Unit Tests
Comprehensive JWT Authentication Testing
==========================================================
"""

import unittest
import time
import secrets
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import SecurityManager, UserRole, Permission


class TestJWTAuthentication(unittest.TestCase):
    """Test JWT authentication functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()
        self.test_user_id = "jwt_test_user"
        self.test_role = UserRole.ADMIN
        self.test_permissions = [
            Permission.READ_MEMORY,
            Permission.WRITE_MEMORY,
            Permission.EXECUTE_SKILLS
        ]

    def test_jwt_token_structure(self):
        """Test JWT token structure and claims"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions,
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )

        # Decode access token
        access_payload = jwt.decode(
            tokens['access_token'],
            self.security_manager.secret_key,
            algorithms=[self.security_manager.algorithm]
        )

        # Verify required claims
        required_claims = [
            'user_id', 'role', 'permissions', 'session_id',
            'exp', 'iat', 'token_type', 'ip_address'
        ]

        for claim in required_claims:
            self.assertIn(claim, access_payload)

        # Verify claim values
        self.assertEqual(access_payload['user_id'], self.test_user_id)
        self.assertEqual(access_payload['role'], self.test_role.value)
        self.assertEqual(access_payload['token_type'], 'access')
        self.assertEqual(access_payload['ip_address'], "192.168.1.100")

        # Verify permissions
        self.assertEqual(len(access_payload['permissions']), len(self.test_permissions))
        for perm in self.test_permissions:
            self.assertIn(perm.value, access_payload['permissions'])

    def test_jwt_refresh_token_structure(self):
        """Test JWT refresh token structure"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        refresh_payload = jwt.decode(
            tokens['refresh_token'],
            self.security_manager.secret_key,
            algorithms=[self.security_manager.algorithm]
        )

        # Verify refresh token claims
        self.assertEqual(refresh_payload['token_type'], 'refresh')
        self.assertEqual(refresh_payload['user_id'], self.test_user_id)
        self.assertEqual(refresh_payload['role'], self.test_role.value)
        self.assertIn('session_id', refresh_payload)

        # Refresh tokens should not have permissions directly
        self.assertNotIn('permissions', refresh_payload)

    def test_jwt_token_expiration(self):
        """Test JWT token expiration"""
        # Test with short expiration
        with patch.object(self.security_manager, 'config', {
            'access_token_expiration': 1,  # 1 second
            'refresh_token_expiration': 2   # 2 seconds
        }):
            tokens = self.security_manager.generate_tokens(
                self.test_user_id,
                self.test_role,
                self.test_permissions
            )

            # Should be valid immediately
            access_payload = self.security_manager.validate_token(tokens['access_token'], 'access')
            self.assertIsNotNone(access_payload)

            # Wait for expiration
            time.sleep(1.5)

            # Should be expired now
            expired_payload = self.security_manager.validate_token(tokens['access_token'], 'access')
            self.assertIsNone(expired_payload)

    def test_jwt_token_algorithm(self):
        """Test JWT token algorithm enforcement"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Try to decode with wrong algorithm
        with self.assertRaises(jwt.InvalidTokenError):
            jwt.decode(tokens['access_token'], self.security_manager.secret_key, algorithms=['HS512'])

    def test_jwt_secret_key_rotation(self):
        """Test JWT secret key changes"""
        # Generate token with current secret
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Change secret key
        old_secret = self.security_manager.secret_key
        self.security_manager.secret_key = secrets.token_urlsafe(64)

        # Old token should be invalid
        payload = self.security_manager.validate_token(tokens['access_token'], 'access')
        self.assertIsNone(payload)

        # New token should work
        new_tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        new_payload = self.security_manager.validate_token(new_tokens['access_token'], 'access')
        self.assertIsNotNone(new_payload)

    def test_jwt_session_id_uniqueness(self):
        """Test that session IDs are unique"""
        session_ids = set()

        # Generate multiple tokens
        for i in range(10):
            tokens = self.security_manager.generate_tokens(
                self.test_user_id,
                self.test_role,
                self.test_permissions
            )
            session_ids.add(tokens['session_id'])

        # All session IDs should be unique
        self.assertEqual(len(session_ids), 10)

    def test_jwt_ip_address_binding(self):
        """Test IP address binding in tokens"""
        original_ip = "192.168.1.100"
        different_ip = "10.0.0.1"

        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions,
            ip_address=original_ip
        )

        # Should validate with original IP
        payload = self.security_manager.validate_token(
            tokens['access_token'],
            'access',
            ip_address=original_ip
        )
        self.assertIsNotNone(payload)

        # Should reject with different IP
        payload = self.security_manager.validate_token(
            tokens['access_token'],
            'access',
            ip_address=different_ip
        )
        self.assertIsNone(payload)

    def test_jwt_user_agent_binding(self):
        """Test user agent binding in tokens"""
        original_ua = "Mozilla/5.0 (Test)"
        different_ua = "Mozilla/5.0 (Different)"

        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions,
            user_agent=original_ua
        )

        # Should validate with original user agent
        payload = self.security_manager.validate_token(
            tokens['access_token'],
            'access',
            user_agent=original_ua
        )
        self.assertIsNotNone(payload)

        # Should reject with different user agent
        payload = self.security_manager.validate_token(
            tokens['access_token'],
            'access',
            user_agent=different_ua
        )
        self.assertIsNone(payload)

    def test_jwt_token_rotation(self):
        """Test JWT token rotation during refresh"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Refresh the token
        new_tokens = self.security_manager.refresh_token(
            tokens['refresh_token'],
            ip_address="192.168.1.100"
        )

        self.assertIsNotNone(new_tokens)
        self.assertIn('access_token', new_tokens)
        self.assertIn('refresh_token', new_tokens)

        # New tokens should have different session ID
        self.assertNotEqual(tokens['session_id'], new_tokens['session_id'])

    def test_jwt_refresh_token_validation(self):
        """Test refresh token specific validation"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Should validate as refresh token
        payload = self.security_manager.validate_token(tokens['refresh_token'], 'refresh')
        self.assertIsNotNone(payload)
        self.assertEqual(payload['token_type'], 'refresh')

        # Should not validate as access token
        payload = self.security_manager.validate_token(tokens['refresh_token'], 'access')
        self.assertIsNone(payload)

    def test_jwt_token_invalidation_on_logout(self):
        """Test token invalidation on logout"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Should be valid before logout
        payload = self.security_manager.validate_token(tokens['access_token'], 'access')
        self.assertIsNotNone(payload)

        # Logout
        self.security_manager.logout_user(self.test_user_id, tokens['session_id'])

        # Should be invalid after logout
        payload = self.security_manager.validate_token(tokens['access_token'], 'access')
        self.assertIsNone(payload)

    def test_jwt_token_payload_integrity(self):
        """Test JWT token payload integrity"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Decode and verify payload integrity
        payload = jwt.decode(
            tokens['access_token'],
            self.security_manager.secret_key,
            algorithms=[self.security_manager.algorithm]
        )

        # Verify all expected fields are present and correct
        self.assertEqual(payload['user_id'], self.test_user_id)
        self.assertEqual(payload['role'], self.test_role.value)
        self.assertEqual(payload['session_id'], tokens['session_id'])

        # Verify timestamps
        self.assertIn('iat', payload)
        self.assertIn('exp', payload)
        self.assertGreater(payload['exp'], payload['iat'])

    def test_jwt_multiple_token_validation(self):
        """Test validation of multiple tokens simultaneously"""
        tokens_list = []

        # Generate multiple tokens
        for i in range(5):
            tokens = self.security_manager.generate_tokens(
                f"user_{i}",
                self.test_role,
                self.test_permissions
            )
            tokens_list.append(tokens)

        # All should be valid initially
        for tokens in tokens_list:
            payload = self.security_manager.validate_token(tokens['access_token'], 'access')
            self.assertIsNotNone(payload)

        # Logout one user
        self.security_manager.logout_user("user_2", tokens_list[2]['session_id'])

        # That token should be invalid, others should still work
        for i, tokens in enumerate(tokens_list):
            payload = self.security_manager.validate_token(tokens['access_token'], 'access')
            if i == 2:
                self.assertIsNone(payload)  # Should be invalid
            else:
                self.assertIsNotNone(payload)  # Should still be valid

    def test_jwt_token_size_limits(self):
        """Test JWT token size limits"""
        # Create user with many permissions to test token size
        many_permissions = list(Permission)  # All permissions

        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            many_permissions
        )

        # Tokens should not be excessively large
        self.assertLess(len(tokens['access_token']), 8000)  # 8KB limit
        self.assertLess(len(tokens['refresh_token']), 4000)  # 4KB limit

    def test_jwt_claims_validation(self):
        """Test JWT claims validation"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        payload = jwt.decode(
            tokens['access_token'],
            self.security_manager.secret_key,
            algorithms=[self.security_manager.algorithm]
        )

        # Verify required claims exist
        required_claims = ['user_id', 'role', 'permissions', 'session_id', 'exp', 'iat', 'token_type']
        for claim in required_claims:
            self.assertIn(claim, payload)
            self.assertIsNotNone(payload[claim])

        # Verify claim types
        self.assertIsInstance(payload['user_id'], str)
        self.assertIsInstance(payload['role'], str)
        self.assertIsInstance(payload['permissions'], list)
        self.assertIsInstance(payload['session_id'], str)
        self.assertIsInstance(payload['exp'], int)
        self.assertIsInstance(payload['iat'], int)
        self.assertIsInstance(payload['token_type'], str)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)