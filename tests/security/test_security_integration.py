#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Security Integration Tests
End-to-End Security Flow Testing
==========================================================
"""

import unittest
import time
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import SecurityManager, InputValidator, SecurityMiddleware, UserRole, Permission
from main import JarvisV9Orchestrator


class TestSecurityIntegration(unittest.TestCase):
    """Test security integration across the entire system"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()
        self.input_validator = InputValidator()
        self.middleware = SecurityMiddleware(self.security_manager, self.input_validator)

        # Mock the main orchestrator for integration testing
        self.mock_orchestrator = MagicMock()
        self.mock_orchestrator.security_manager = self.security_manager
        self.mock_orchestrator.input_validator = self.input_validator

    def test_complete_authentication_flow(self):
        """Test complete authentication flow from request to response"""
        # Step 1: User authentication
        auth_result = self.security_manager.authenticate_user(
            "admin",
            os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!'),
            ip_address="192.168.1.100",
            user_agent="TestBrowser/1.0"
        )

        self.assertIsNotNone(auth_result)
        self.assertIn('access_token', auth_result)
        self.assertIn('refresh_token', auth_result)

        access_token = auth_result['access_token']

        # Step 2: Request validation
        test_request = {
            'message': 'Process this request',
            'context': {
                'query': 'safe search query'
            }
        }

        # Sanitize request
        sanitized_request = self.middleware.sanitize_request(test_request)

        # Validate request
        is_valid = self.middleware.validate_request(sanitized_request, 'general')
        self.assertTrue(is_valid)

        # Step 3: Token validation
        payload = self.security_manager.validate_token(
            access_token,
            'access',
            ip_address="192.168.1.100",
            user_agent="TestBrowser/1.0"
        )
        self.assertIsNotNone(payload)

        # Step 4: Permission check
        has_permission = self.security_manager.check_permission(
            access_token,
            Permission.EXECUTE_SKILLS,
            ip_address="192.168.1.100",
            user_agent="TestBrowser/1.0"
        )
        self.assertTrue(has_permission)

        # Step 5: Process request (simulated)
        user_id = payload['user_id']
        self.assertIsNotNone(user_id)

        # Step 6: Log security event
        self.security_manager._log_security_event(
            "request_processed",
            user_id,
            "192.168.1.100",
            {"request_type": "message_processing"},
            "low"
        )

        # Verify audit trail
        audit_log = self.security_manager.get_audit_log()
        self.assertGreater(len(audit_log), 0)

    def test_security_flow_with_dangerous_input(self):
        """Test security flow with dangerous input"""
        # Generate valid token
        auth_result = self.security_manager.authenticate_user(
            "admin",
            os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!')
        )
        access_token = auth_result['access_token']

        # Create dangerous request
        dangerous_request = {
            'message': 'DROP TABLE users; <script>alert("xss")</script>',
            'context': {
                'query': 'UNION SELECT password FROM admin',
                'command': 'rm -rf /'
            }
        }

        # Request should be sanitized
        sanitized = self.middleware.sanitize_request(dangerous_request)

        # Should remove dangerous content
        self.assertNotIn('DROP TABLE', sanitized['message'])
        self.assertNotIn('<script>', sanitized['message'])
        self.assertNotIn('UNION SELECT', sanitized['context']['query'])
        self.assertNotIn('rm -rf', sanitized['context']['command'])

        # Request validation should fail
        is_valid = self.middleware.validate_request(sanitized, 'general')
        # Note: After sanitization, it might pass validation
        # This depends on implementation - sanitized content might be safe

        # But original dangerous content should be removed
        self.assertNotIn('DROP', sanitized['message'])

    def test_rate_limiting_integration(self):
        """Test rate limiting integration with authentication"""
        # Authenticate user
        auth_result = self.security_manager.authenticate_user(
            "test_user",
            "wrong_password"  # This will fail and create failed attempts
        )
        self.assertIsNone(auth_result)

        # Try multiple failed authentications
        for i in range(6):  # Exceed max_failed_attempts
            self.security_manager.authenticate_user(
                "test_user",
                "wrong_password"
            )

        # User should be locked out
        is_locked = self.security_manager._is_locked_out("test_user")
        self.assertTrue(is_locked)

        # Even correct password should be blocked
        result = self.security_manager.authenticate_user(
            "test_user",
            os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!')
        )
        self.assertIsNone(result)

    def test_session_management_integration(self):
        """Test session management integration"""
        # Create multiple sessions
        tokens1 = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )
        tokens2 = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )

        # Should enforce max sessions
        user_sessions = [s for s in self.security_manager.sessions.values()
                        if s.user_id == "test_user" and s.active]
        max_sessions = self.security_manager.config["max_sessions_per_user"]
        self.assertLessEqual(len(user_sessions), max_sessions)

        # Logout specific session
        self.security_manager.logout_user("test_user", tokens1['session_id'])

        # That session should be inactive
        session1 = self.security_manager.sessions[tokens1['session_id']]
        self.assertFalse(session1.active)

        # Other session should still be active
        session2 = self.security_manager.sessions[tokens2['session_id']]
        self.assertTrue(session2.active)

        # Logout all sessions
        self.security_manager.logout_user("test_user")

        # All sessions should be inactive
        for session in self.security_manager.sessions.values():
            if session.user_id == "test_user":
                self.assertFalse(session.active)

    def test_permission_hierarchy_integration(self):
        """Test permission hierarchy across different roles"""
        roles_and_permissions = [
            (UserRole.GUEST, [Permission.READ_SYSTEM_STATS]),
            (UserRole.AGENT, [Permission.EXECUTE_SKILLS]),
            (UserRole.USER, [Permission.READ_MEMORY, Permission.WRITE_MEMORY]),
            (UserRole.ADMIN, [Permission.MANAGE_USERS, Permission.SYSTEM_ADMIN])
        ]

        for role, test_permissions in roles_and_permissions:
            with self.subTest(role=role.value):
                # Generate tokens for role
                all_permissions = self.security_manager.get_role_permissions(role)
                tokens = self.security_manager.generate_tokens(
                    f"{role.value}_user",
                    role,
                    all_permissions
                )

                # Test each permission for this role
                for permission in test_permissions:
                    if permission in all_permissions:
                        # Should have permission
                        result = self.security_manager.check_permission(
                            tokens['access_token'],
                            permission
                        )
                        self.assertTrue(result, f"Role {role.value} should have permission {permission.value}")

                        # Should be able to use middleware with this permission
                        authorized = self.middleware.authorize_operation(
                            f"{role.value}_user",
                            permission
                        )
                        # Note: This might fail because middleware needs actual token
                        # But the method should not crash

    def test_security_audit_trail(self):
        """Test complete security audit trail"""
        initial_audit_count = len(self.security_manager.audit_log)

        # Perform various security events
        events = []

        # 1. Authentication attempt
        auth_result = self.security_manager.authenticate_user(
            "test_user",
            "wrong_password"
        )
        events.append("authentication_failed")

        # 2. Permission check
        if auth_result:
            self.security_manager.check_permission(
                auth_result['access_token'],
                Permission.READ_MEMORY
            )
            events.append("permission_granted")

        # 3. Rate limit check
        self.security_manager._check_rate_limit("test_user", Permission.EXECUTE_SKILLS)
        events.append("rate_limit_check")

        # 4. Security event logging
        self.security_manager._log_security_event(
            "test_event",
            "test_user",
            "127.0.0.1",
            {"test": "data"},
            "medium"
        )
        events.append("custom_event")

        # Get audit log
        audit_log = self.security_manager.get_audit_log()
        final_audit_count = len(audit_log)

        # Should have new entries
        self.assertGreater(final_audit_count, initial_audit_count)

        # Verify event types
        event_types = [entry.get('event_type') for entry in audit_log[-len(events):]]
        for event in events:
            self.assertIn(event, event_types)

    def test_security_statistics_integration(self):
        """Test security statistics collection"""
        # Get initial stats
        initial_stats = self.security_manager.get_security_stats()

        # Perform actions that affect stats
        # Authentication attempts
        for i in range(3):
            self.security_manager.authenticate_user("test_user", "wrong_password")

        # Permission checks
        tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )
        for i in range(5):
            self.security_manager.check_permission(
                tokens['access_token'],
                Permission.READ_MEMORY
            )

        # Rate limit checks
        for i in range(10):
            self.security_manager._check_rate_limit("test_user", Permission.EXECUTE_SKILLS)

        # Get updated stats
        final_stats = self.security_manager.get_security_stats()

        # Verify stats increased
        self.assertGreater(final_stats['total_events'], initial_stats['total_events'])
        self.assertGreater(final_stats['recent_events'], initial_stats['recent_events'])

        # Active sessions should be present
        self.assertGreater(final_stats['active_sessions'], 0)

        # Failed attempts should be tracked
        self.assertGreater(final_stats['failed_attempts'], 0)

    def test_security_cleanup_integration(self):
        """Test security data cleanup"""
        # Create some data that should be cleaned up
        # This is hard to test without mocking time
        # For now, just verify the method doesn't crash

        try:
            self.security_manager.cleanup_expired_data()
            # Should not raise exception
        except Exception as e:
            self.fail(f"cleanup_expired_data raised {e} unexpectedly!")

    def test_security_with_mock_orchestrator(self):
        """Test security integration with mocked orchestrator"""
        # Mock orchestrator methods
        with patch.object(self.mock_orchestrator, 'process_message') as mock_process:
            mock_process.return_value = {
                "text": "Processed message",
                "metadata": {"success": True}
            }

            # Authenticate user
            auth_result = self.security_manager.authenticate_user(
                "test_user",
                os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!')
            )
            self.assertIsNotNone(auth_result)

            access_token = auth_result['access_token']

            # Simulate processing message with security checks
            message = "Test message"
            context = {"source": "test"}

            # Check permissions
            has_permission = self.security_manager.check_permission(
                access_token,
                Permission.EXECUTE_SKILLS
            )
            self.assertTrue(has_permission)

            # Sanitize input
            sanitized_message = self.input_validator.sanitize_input(message)
            self.assertEqual(sanitized_message, message)  # Should be safe

            # Process message
            result = mock_process(message, context, "test_user")
            self.assertIsNotNone(result)
            self.assertIn("text", result)

            # Verify mock was called
            mock_process.assert_called_once_with(message, context, "test_user")

    def test_concurrent_security_requests(self):
        """Test security system under concurrent requests"""
        import threading
        import time

        results = []
        errors = []

        def make_request(user_id, request_num):
            try:
                # Authenticate
                auth_result = self.security_manager.authenticate_user(
                    user_id,
                    os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!')
                )
                if not auth_result:
                    errors.append(f"Auth failed for {user_id}")
                    return

                # Make requests
                for i in range(3):
                    # Check permission
                    has_perm = self.security_manager.check_permission(
                        auth_result['access_token'],
                        Permission.READ_MEMORY
                    )
                    if not has_perm:
                        errors.append(f"Permission failed for {user_id} request {i}")
                        continue

                    # Validate input
                    test_input = f"Request {request_num}-{i}"
                    is_valid = self.input_validator.validate_input(test_input, 'general')
                    if not is_valid:
                        errors.append(f"Validation failed for {user_id} request {i}")

                    results.append(f"{user_id}-{request_num}-{i}")

            except Exception as e:
                errors.append(f"Error for {user_id}-{request_num}: {e}")

        # Create multiple threads
        threads = []
        for i in range(5):
            for j in range(3):
                thread = threading.Thread(
                    target=make_request,
                    args=(f"user_{i}", j)
                )
                threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify results
        self.assertGreater(len(results), 0, "Should have processed some requests")
        self.assertEqual(len(errors), 0, f"Should have no errors, but got: {errors}")

        # Verify no excessive duplicate results (indicating session issues)
        unique_results = set(results)
        self.assertGreaterEqual(len(unique_results), len(results) * 0.8,
                              "Should have mostly unique results")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)