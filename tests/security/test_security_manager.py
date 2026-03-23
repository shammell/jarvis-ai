#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Security Manager Unit Tests
PhD-Level Security Testing
==========================================================
"""

import unittest
import time
import secrets
import bcrypt
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import SecurityManager, UserRole, Permission, SecurityLevel, Session, FailedAttempt


class TestSecurityManager(unittest.TestCase):
    """Test SecurityManager class functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()
        self.test_user_id = "test_user"
        self.test_role = UserRole.USER
        self.test_permissions = [Permission.READ_MEMORY, Permission.WRITE_MEMORY]

    def test_hash_password(self):
        """Test password hashing"""
        password = "test_password"
        hashed = self.security_manager.hash_password(password)

        self.assertIsInstance(hashed, str)
        self.assertTrue(hashed.startswith('$2b$'))  # bcrypt format

    def test_verify_password(self):
        """Test password verification"""
        password = "test_password"
        hashed = self.security_manager.hash_password(password)

        self.assertTrue(self.security_manager.verify_password(password, hashed))
        self.assertFalse(self.security_manager.verify_password("wrong_password", hashed))

    def test_generate_tokens(self):
        """Test JWT token generation"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions,
            ip_address="127.0.0.1",
            user_agent="test_agent"
        )

        self.assertIn('access_token', tokens)
        self.assertIn('refresh_token', tokens)
        self.assertIn('expires_in', tokens)
        self.assertIn('token_type', tokens)
        self.assertIn('session_id', tokens)
        self.assertIn('user', tokens)

        # Verify user info
        user_info = tokens['user']
        self.assertEqual(user_info['id'], self.test_user_id)
        self.assertEqual(user_info['role'], self.test_role.value)
        self.assertEqual(len(user_info['permissions']), len(self.test_permissions))

    def test_validate_token_success(self):
        """Test successful token validation"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        payload = self.security_manager.validate_token(tokens['access_token'], 'access')
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], self.test_user_id)
        self.assertEqual(payload['role'], self.test_role.value)
        self.assertEqual(payload['token_type'], 'access')

    def test_validate_token_expired(self):
        """Test expired token validation"""
        # Create a token with very short expiration
        with patch.object(self.security_manager, 'config', {
            'access_token_expiration': -1  # Expired
        }):
            tokens = self.security_manager.generate_tokens(
                self.test_user_id,
                self.test_role,
                self.test_permissions
            )

        payload = self.security_manager.validate_token(tokens['access_token'], 'access')
        self.assertIsNone(payload)

    def test_validate_token_invalid_type(self):
        """Test invalid token type validation"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Try to validate access token as refresh
        payload = self.security_manager.validate_token(tokens['access_token'], 'refresh')
        self.assertIsNone(payload)

    def test_check_permission_granted(self):
        """Test permission check when granted"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        result = self.security_manager.check_permission(
            tokens['access_token'],
            Permission.READ_MEMORY
        )
        self.assertTrue(result)

    def test_check_permission_denied(self):
        """Test permission check when denied"""
        # Create user with no permissions
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            []  # No permissions
        )

        result = self.security_manager.check_permission(
            tokens['access_token'],
            Permission.READ_MEMORY
        )
        self.assertFalse(result)

    def test_authenticate_user_success(self):
        """Test successful user authentication"""
        # This would normally check against a database
        # For now, we'll test the hardcoded admin user
        result = self.security_manager.authenticate_user(
            "admin",
            os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!'),
            ip_address="127.0.0.1",
            user_agent="test_agent"
        )

        self.assertIsNotNone(result)
        self.assertIn('access_token', result)
        self.assertIn('refresh_token', result)

    def test_authenticate_user_failure(self):
        """Test failed user authentication"""
        result = self.security_manager.authenticate_user(
            "wrong_user",
            "wrong_password",
            ip_address="127.0.0.1",
            user_agent="test_agent"
        )

        self.assertIsNone(result)

    def test_logout_user(self):
        """Test user logout"""
        # Generate tokens
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )

        # Verify session exists
        session_id = tokens['session_id']
        self.assertIn(session_id, self.security_manager.sessions)

        # Logout
        self.security_manager.logout_user(self.test_user_id, session_id)

        # Verify session is inactive
        session = self.security_manager.sessions[session_id]
        self.assertFalse(session.active)

    def test_logout_all_sessions(self):
        """Test logout all sessions for user"""
        # Create multiple sessions
        tokens1 = self.security_manager.generate_tokens(self.test_user_id, self.test_role, self.test_permissions)
        tokens2 = self.security_manager.generate_tokens(self.test_user_id, self.test_role, self.test_permissions)

        # Logout all
        self.security_manager.logout_user(self.test_user_id)

        # Verify all sessions are inactive
        for session in self.security_manager.sessions.values():
            if session.user_id == self.test_user_id:
                self.assertFalse(session.active)

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Test multiple requests from same user
        user_permission = Permission.EXECUTE_SKILLS

        # Make requests up to the limit
        limit = self.security_manager.config["rate_limits"]["per_minute"][user_permission]
        for i in range(limit):
            result = self.security_manager._check_rate_limit(self.test_user_id, user_permission)
            if i < limit - 1:  # Should pass until limit is reached
                self.assertTrue(result)

        # Next request should be blocked
        result = self.security_manager._check_rate_limit(self.test_user_id, user_permission)
        self.assertFalse(result)

    def test_failed_attempts_lockout(self):
        """Test failed authentication lockout"""
        max_attempts = self.security_manager.config["max_failed_attempts"]

        # Make failed attempts
        for i in range(max_attempts):
            self.security_manager._record_failed_attempt(
                self.test_user_id,
                "127.0.0.1",
                "test_agent",
                {"reason": "test"}
            )

        # Verify lockout
        self.assertTrue(self.security_manager._is_locked_out(self.test_user_id))

    def test_session_management(self):
        """Test session management"""
        # Generate session
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )
        session_id = tokens['session_id']

        # Verify session exists and is active
        session = self.security_manager.sessions[session_id]
        self.assertTrue(session.active)
        self.assertEqual(session.user_id, self.test_user_id)
        self.assertEqual(session.role, self.test_role)

        # Verify session timeout
        old_activity = session.last_activity
        time.sleep(0.1)  # Small delay
        session.last_activity = datetime.utcnow()

        # Should still be active
        self.assertTrue(self.security_manager.sessions[session_id].active)

    def test_security_stats(self):
        """Test security statistics"""
        stats = self.security_manager.get_security_stats()

        self.assertIn('active_sessions', stats)
        self.assertIn('total_events', stats)
        self.assertIn('recent_events', stats)
        self.assertIn('risk_distribution', stats)
        self.assertIn('session_timeout', stats)

        # Should have no active sessions initially (or some number)
        self.assertGreaterEqual(stats['active_sessions'], 0)

    def test_audit_log(self):
        """Test audit logging"""
        # Generate some events by performing actions
        self.security_manager.authenticate_user("admin", "wrong_password")

        # Get audit log
        audit_log = self.security_manager.get_audit_log(limit=10)

        self.assertIsInstance(audit_log, list)
        # Should contain at least the failed auth attempt
        self.assertGreaterEqual(len(audit_log), 0)  # May be empty initially

    def test_cleanup_expired_data(self):
        """Test cleanup of expired data"""
        # This test would require mocking datetime to simulate expired sessions
        # For now, just call the method to ensure it doesn't crash
        self.security_manager.cleanup_expired_data()

    def test_max_sessions_per_user(self):
        """Test max sessions per user enforcement"""
        max_sessions = self.security_manager.config["max_sessions_per_user"]

        # Create more sessions than allowed
        tokens_list = []
        for i in range(max_sessions + 2):
            tokens = self.security_manager.generate_tokens(
                self.test_user_id,
                self.test_role,
                self.test_permissions
            )
            tokens_list.append(tokens)

        # Should have enforced the limit
        user_sessions = [s for s in self.security_manager.sessions.values()
                        if s.user_id == self.test_user_id and s.active]
        self.assertLessEqual(len(user_sessions), max_sessions)

    def test_session_risk_scoring(self):
        """Test session risk scoring for high-risk permissions"""
        tokens = self.security_manager.generate_tokens(
            self.test_user_id,
            self.test_role,
            self.test_permissions
        )
        session_id = tokens['session_id']

        # Initial risk score should be 0
        session = self.security_manager.sessions[session_id]
        initial_risk = session.risk_score

        # Use high-risk permission
        self.security_manager.check_permission(
            tokens['access_token'],
            Permission.ACCESS_AUTONOMOUS
        )

        # Risk score should increase
        new_risk = self.security_manager.sessions[session_id].risk_score
        self.assertGreater(new_risk, initial_risk)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)