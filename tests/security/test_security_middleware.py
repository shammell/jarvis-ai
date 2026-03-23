#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Security Middleware Unit Tests
Comprehensive Middleware Testing
==========================================================
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import SecurityManager, InputValidator, SecurityMiddleware, UserRole, Permission


class TestSecurityMiddleware(unittest.TestCase):
    """Test SecurityMiddleware class functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()
        self.input_validator = InputValidator()
        self.middleware = SecurityMiddleware(self.security_manager, self.input_validator)

    def test_authenticate_request_success(self):
        """Test successful request authentication"""
        # Generate valid token
        tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )

        # Mock request headers
        headers = {
            'Authorization': f'Bearer {tokens["access_token"]}',
            'X-Forwarded-For': '192.168.1.100',
            'User-Agent': 'TestAgent/1.0'
        }

        # Authenticate
        user_id = self.middleware.authenticate_request(
            headers,
            ip_address='192.168.1.100',
            user_agent='TestAgent/1.0'
        )

        self.assertEqual(user_id, "test_user")

    def test_authenticate_request_no_auth_header(self):
        """Test authentication without Authorization header"""
        headers = {
            'Content-Type': 'application/json'
        }

        user_id = self.middleware.authenticate_request(headers)
        self.assertIsNone(user_id)

    def test_authenticate_request_invalid_auth_header(self):
        """Test authentication with invalid Authorization header"""
        headers = {
            'Authorization': 'Basic dXNlcjpwYXNz',  # Basic auth instead of Bearer
        }

        user_id = self.middleware.authenticate_request(headers)
        self.assertIsNone(user_id)

    def test_authenticate_request_expired_token(self):
        """Test authentication with expired token"""
        # Create token with short expiration
        with patch.object(self.security_manager, 'config', {
            'access_token_expiration': -1  # Expired
        }):
            tokens = self.security_manager.generate_tokens(
                "test_user",
                UserRole.USER,
                [Permission.READ_MEMORY]
            )

        headers = {
            'Authorization': f'Bearer {tokens["access_token"]}',
        }

        user_id = self.middleware.authenticate_request(headers)
        self.assertIsNone(user_id)

    def test_authenticate_request_ip_mismatch(self):
        """Test authentication with IP address mismatch"""
        tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY],
            ip_address="192.168.1.100"
        )

        headers = {
            'Authorization': f'Bearer {tokens["access_token"]}',
        }

        # Try to authenticate from different IP
        user_id = self.middleware.authenticate_request(
            headers,
            ip_address="10.0.0.1",  # Different IP
            user_agent="TestAgent/1.0"
        )

        self.assertIsNone(user_id)

    def test_authorize_operation_success(self):
        """Test successful operation authorization"""
        # Generate admin token with all permissions
        tokens = self.security_manager.generate_tokens(
            "admin_user",
            UserRole.ADMIN,
            list(Permission)
        )

        # Mock a valid authorization check
        # Note: This test would need the actual token in a real implementation
        # For now, we test the method structure
        result = self.middleware.authorize_operation(
            "admin_user",
            Permission.EXECUTE_SKILLS,
            request_data={"action": "test"},
            ip_address="192.168.1.100",
            user_agent="TestAgent/1.0"
        )

        # Should return True for valid authorization
        self.assertTrue(result)

    def test_authorize_operation_denied(self):
        """Test denied operation authorization"""
        # Generate user token with limited permissions
        tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY]  # No EXECUTE_SKILLS
        )

        result = self.middleware.authorize_operation(
            "test_user",
            Permission.EXECUTE_SKILLS,  # Not in permissions
            request_data={"action": "test"}
        )

        self.assertFalse(result)

    def test_sanitize_request_basic(self):
        """Test basic request sanitization"""
        dirty_request = {
            'message': 'Hello <script>alert("xss")</script> World',
            'context': {
                'query': 'SELECT * FROM users',
                'data': 'Normal text'
            },
            'list_data': [
                {'name': '<script>malicious</script>'},
                {'name': 'safe'}
            ],
            'number': 123,
            'boolean': True
        }

        sanitized = self.middleware.sanitize_request(dirty_request)

        # Text should be sanitized
        self.assertNotIn('<script>', sanitized['message'])
        self.assertNotIn('>', sanitized['message'])

        # SQL should be sanitized
        self.assertNotIn('SELECT', sanitized['context']['query'])
        self.assertNotIn('*', sanitized['context']['query'])

        # Safe text should remain
        self.assertIn('Normal text', sanitized['context']['data'])

        # List items should be sanitized
        self.assertNotIn('<script>', sanitized['list_data'][0]['name'])
        self.assertIn('safe', sanitized['list_data'][1]['name'])

        # Non-string types should be preserved
        self.assertEqual(sanitized['number'], 123)
        self.assertEqual(sanitized['boolean'], True)

    def test_sanitize_request_nested(self):
        """Test nested request sanitization"""
        nested_request = {
            'level1': {
                'level2': {
                    'level3': {
                        'dangerous': '<script>alert("deep")</script>'
                    }
                }
            }
        }

        sanitized = self.middleware.sanitize_request(nested_request)

        # Deep nesting should be sanitized
        self.assertNotIn('<script>', sanitized['level1']['level2']['level3']['dangerous'])
        self.assertIn('deep', sanitized['level1']['level2']['level3']['dangerous'])

    def test_sanitize_request_edge_cases(self):
        """Test edge cases in request sanitization"""
        edge_cases = {
            'empty_string': '',
            'whitespace': '   \t\n  ',
            'null_value': None,
            'empty_list': [],
            'empty_dict': {},
            'special_chars': '!@#$%^&*()_+-=[]{}|;:,.<>?',
            'unicode': 'Hello 世界 🚀'
        }

        sanitized = self.middleware.sanitize_request(edge_cases)

        # These should be preserved or handled gracefully
        self.assertIsInstance(sanitized['empty_string'], str)
        self.assertIsInstance(sanitized['whitespace'], str)
        self.assertEqual(sanitized['empty_list'], [])
        self.assertEqual(sanitized['empty_dict'], {})
        self.assertIn('!', sanitized['special_chars'])
        self.assertIn('世界', sanitized['unicode'])

    def test_validate_request_basic(self):
        """Test basic request validation"""
        valid_request = {
            'message': 'Hello world',
            'context': {
                'query': 'search for documentation',
                'user_id': 'test_user'
            }
        }

        result = self.middleware.validate_request(valid_request, 'general')
        self.assertTrue(result)

    def test_validate_request_dangerous_content(self):
        """Test request validation with dangerous content"""
        dangerous_request = {
            'message': 'DROP TABLE users',
            'context': {
                'query': '<script>alert("xss")</script>',
                'command': 'rm -rf /'
            }
        }

        result = self.middleware.validate_request(dangerous_request, 'general')
        self.assertFalse(result)

    def test_validate_request_size_limits(self):
        """Test request validation with size limits"""
        # Create large request
        large_request = {
            'message': 'x' * 100000,  # Very large
            'context': {
                'data': 'y' * 50000
            }
        }

        # Should fail due to size
        result = self.middleware.validate_request(large_request, 'general')
        self.assertFalse(result)

        # Smaller request should pass
        smaller_request = {
            'message': 'x' * 1000,
            'context': {
                'data': 'y' * 500
            }
        }

        result = self.middleware.validate_request(smaller_request, 'general')
        self.assertTrue(result)

    def test_validate_request_non_dict(self):
        """Test request validation with non-dict input"""
        # String input
        result = self.middleware.validate_request("not a dict", 'general')
        self.assertFalse(result)

        # List input
        result = self.middleware.validate_request(["not", "a", "dict"], 'general')
        self.assertFalse(result)

        # None input
        result = self.middleware.validate_request(None, 'general')
        self.assertFalse(result)

    def test_middleware_integration(self):
        """Test complete middleware integration"""
        # Generate valid token
        tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY, Permission.WRITE_MEMORY]
        )

        # Create request
        request = {
            'message': 'Hello world',
            'context': {
                'query': 'safe query'
            }
        }

        # Authenticate
        headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
        user_id = self.middleware.authenticate_request(headers)

        self.assertEqual(user_id, "test_user")

        # Sanitize (should not change much for safe content)
        sanitized = self.middleware.sanitize_request(request)

        # Validate
        is_valid = self.middleware.validate_request(sanitized, 'general')
        self.assertTrue(is_valid)

        # Authorize (should work for READ_MEMORY)
        authorized = self.middleware.authorize_operation(
            user_id,
            Permission.READ_MEMORY,
            sanitized
        )
        self.assertTrue(authorized)

    def test_middleware_security_events(self):
        """Test that middleware generates security events"""
        initial_events = len(self.security_manager.security_events)

        # Try to authenticate with invalid token
        headers = {'Authorization': 'Bearer invalid_token'}
        user_id = self.middleware.authenticate_request(headers)

        self.assertIsNone(user_id)

        # Should have generated security event
        final_events = len(self.security_manager.security_events)
        self.assertGreater(final_events, initial_events)

    def test_middleware_error_handling(self):
        """Test middleware error handling"""
        # Test with None inputs
        result = self.middleware.authenticate_request(None)
        self.assertIsNone(result)

        result = self.middleware.sanitize_request(None)
        self.assertEqual(result, {})

        result = self.middleware.validate_request(None, 'general')
        self.assertFalse(result)

        # Test with empty inputs
        result = self.middleware.authenticate_request({})
        self.assertIsNone(result)

        result = self.middleware.sanitize_request({})
        self.assertEqual(result, {})

        result = self.middleware.validate_request({}, 'general')
        self.assertTrue(result)  # Empty dict should be valid

    def test_middleware_performance(self):
        """Test middleware performance with large requests"""
        import time

        # Create large request
        large_request = {
            'message': 'x' * 10000,
            'context': {
                'data': 'y' * 10000,
                'nested': {
                    'deep': 'z' * 10000
                }
            }
        }

        # Time sanitization
        start_time = time.time()
        sanitized = self.middleware.sanitize_request(large_request)
        sanitize_time = time.time() - start_time

        # Time validation
        start_time = time.time()
        is_valid = self.middleware.validate_request(sanitized, 'general')
        validate_time = time.time() - start_time

        # Should complete in reasonable time (less than 1 second)
        self.assertLess(sanitize_time, 1.0)
        self.assertLess(validate_time, 1.0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)