#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Input Validator Unit Tests
Comprehensive Input Validation Testing
==========================================================
"""

import unittest
import re
from unittest.mock import patch, MagicMock
import sys
import os
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import InputValidator


class TestInputValidator(unittest.TestCase):
    """Test InputValidator class functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.validator = InputValidator()

    def test_sanitize_input_basic(self):
        """Test basic input sanitization"""
        test_input = 'Hello <script>alert("xss")</script> World'
        sanitized = self.validator.sanitize_input(test_input)

        # Should remove/escape HTML
        self.assertNotIn('<script>', sanitized)
        self.assertNotIn('>', sanitized)  # Basic check
        self.assertIn('Hello', sanitized)
        self.assertIn('World', sanitized)

    def test_sanitize_input_null_bytes(self):
        """Test null byte removal"""
        test_input = 'Test\x00with\x00null\x00bytes'
        sanitized = self.validator.sanitize_input(test_input)

        self.assertNotIn('\x00', sanitized)
        self.assertEqual(sanitized, 'Testwithnullbytes')

    def test_sanitize_input_whitespace(self):
        """Test whitespace normalization"""
        test_input = '  Too   much   whitespace  '
        sanitized = self.validator.sanitize_input(test_input)

        # Should normalize whitespace
        self.assertNotIn('  ', sanitized)
        self.assertEqual(sanitized, 'Too much whitespace')

    def test_sanitize_input_length_limit(self):
        """Test input length limiting"""
        long_input = 'A' * 100000  # Much longer than max
        sanitized = self.validator.sanitize_input(long_input, max_length=100)

        self.assertLessEqual(len(sanitized), 100)

    def test_validate_input_sql_injection(self):
        """Test SQL injection detection"""
        sql_inputs = [
            "SELECT * FROM users",
            "UNION SELECT password FROM admin",
            "DROP TABLE users",
            "INSERT INTO users VALUES ('test')",
            "UPDATE users SET password='hacked'"
        ]

        for sql_input in sql_inputs:
            # Should fail validation
            self.assertFalse(self.validator.validate_input(sql_input, 'sql'))
            # Should also fail general validation
            self.assertFalse(self.validator.validate_input(sql_input, 'general'))

    def test_validate_input_xss(self):
        """Test XSS detection"""
        xss_inputs = [
            '<script>alert("xss")</script>',
            'javascript:alert("xss")',
            '<img src=x onerror=alert(1)>',
            '<iframe src="http://evil.com"></iframe>'
        ]

        for xss_input in xss_inputs:
            # Should fail validation
            self.assertFalse(self.validator.validate_input(xss_input, 'xss'))
            # Should also fail general validation
            self.assertFalse(self.validator.validate_input(xss_input, 'general'))

    def test_validate_input_command_injection(self):
        """Test command injection detection"""
        command_inputs = [
            "rm -rf /",
            "cat /etc/passwd",
            "whoami; id",
            "cd /tmp && ls",
            "../../../etc/passwd"
        ]

        for cmd_input in command_inputs:
            # Should fail validation
            self.assertFalse(self.validator.validate_input(cmd_input, 'command'))
            # Should also fail general validation
            self.assertFalse(self.validator.validate_input(cmd_input, 'general'))

    def test_validate_input_safe_content(self):
        """Test validation of safe content"""
        safe_inputs = [
            "Hello world",
            "This is a test message",
            "User input: test123",
            "Valid email: user@example.com",
            "Query: search for documentation"
        ]

        for safe_input in safe_inputs:
            # Should pass general validation
            self.assertTrue(self.validator.validate_input(safe_input, 'general'))
            # Should pass specific validations too
            self.assertTrue(self.validator.validate_input(safe_input, 'sql'))
            self.assertTrue(self.validator.validate_input(safe_input, 'xss'))
            self.assertTrue(self.validator.validate_input(safe_input, 'command'))

    def test_validate_input_length_limits(self):
        """Test input length validation"""
        # Test various length limits
        test_cases = [
            ("short", 10, True),
            ("this is a longer input", 10, False),  # Too long
            ("", 10, True),  # Empty should be valid
            ("exactly ten", 11, True),  # At limit
            ("exactly ten", 10, False),  # At limit exactly
        ]

        for input_text, max_len, expected in test_cases:
            result = self.validator.validate_input(input_text, 'general', max_length=max_len)
            self.assertEqual(result, expected, f"Failed for input: '{input_text}' with max_len: {max_len}")

    def test_validate_file_path_safe(self):
        """Test safe file path validation"""
        safe_paths = [
            "documents/file.txt",
            "images/picture.jpg",
            "data/records.csv",
            "logs/app.log"
        ]

        for path in safe_paths:
            self.assertTrue(self.validator.validate_file_path(path))

    def test_validate_file_path_dangerous(self):
        """Test dangerous file path detection"""
        dangerous_paths = [
            "../../../etc/passwd",  # Directory traversal
            "/etc/passwd",  # Absolute path
            "../secret.txt",  # Simple traversal
            "file<>.txt",  # Suspicious characters
            "test:file.txt",  # Windows reserved character
            "con.txt",  # Windows reserved name
        ]

        for path in dangerous_paths:
            self.assertFalse(self.validator.validate_file_path(path))

    def test_validate_query_safe(self):
        """Test safe query validation"""
        safe_queries = [
            "user documentation",
            "how to use the system",
            "search for records",
            "what is JARVIS",
            "test query"
        ]

        for query in safe_queries:
            self.assertTrue(self.validator.validate_query(query))

    def test_validate_query_dangerous(self):
        """Test dangerous query validation"""
        dangerous_queries = [
            "SELECT * FROM users",
            "<script>alert('xss')</script>",
            "DROP TABLE system",
            "UNION SELECT password"
        ]

        for query in dangerous_queries:
            self.assertFalse(self.validator.validate_query(query))

    def test_validate_context_safe(self):
        """Test safe context validation"""
        safe_context = {
            "user_id": "test_user",
            "session": "abc123",
            "preferences": {
                "theme": "dark",
                "language": "en"
            },
            "metadata": "test data"
        }

        self.assertTrue(self.validator.validate_context(safe_context))

    def test_validate_context_dangerous(self):
        """Test dangerous context validation"""
        dangerous_context = {
            "query": "SELECT * FROM users",
            "script": "<script>alert('xss')</script>",
            "command": "rm -rf /",
            "nested": {
                "sql": "DROP TABLE test"
            }
        }

        self.assertFalse(self.validator.validate_context(dangerous_context))

    def test_validate_context_too_large(self):
        """Test context size validation"""
        # Create a large context
        large_context = {"data": "x" * 200000}  # Larger than max_context_length

        self.assertFalse(self.validator.validate_context(large_context))

    def test_validate_input_non_string(self):
        """Test validation with non-string inputs"""
        # Should handle non-string inputs gracefully
        self.assertFalse(self.validator.validate_input(None, 'general'))
        self.assertFalse(self.validator.validate_input(123, 'general'))
        self.assertFalse(self.validator.validate_input([], 'general'))
        self.assertFalse(self.validator.validate_input({}, 'general'))

    def test_sanitize_input_non_string(self):
        """Test sanitization with non-string inputs"""
        # Should handle non-string inputs gracefully
        self.assertEqual(self.validator.sanitize_input(None), "")
        self.assertEqual(self.validator.sanitize_input(123), "")
        self.assertEqual(self.validator.sanitize_input([]), "")

    def test_validate_input_edge_cases(self):
        """Test edge cases for input validation"""
        # Test empty string
        self.assertTrue(self.validator.validate_input("", 'general'))

        # Test whitespace only
        self.assertTrue(self.validator.validate_input("   ", 'general'))

        # Test very long safe content
        long_safe = "A" * 1000
        self.assertTrue(self.validator.validate_input(long_safe, 'general', max_length=2000))

    def test_pattern_compilation(self):
        """Test that regex patterns are properly compiled"""
        # Should have compiled patterns
        self.assertTrue(len(self.validator.sql_patterns) > 0)
        self.assertTrue(len(self.validator.xss_patterns) > 0)
        self.assertTrue(len(self.validator.command_patterns) > 0)

        # Patterns should be regex objects
        for pattern in self.validator.sql_patterns:
            self.assertIsInstance(pattern, re.Pattern)

    def test_validate_input_with_unicode(self):
        """Test input validation with Unicode characters"""
        unicode_inputs = [
            "Hello 世界",  # Chinese characters
            "Café français",  # French accents
            "Emoji: 🚀✨",  # Emojis
            "Special: @#$%^&*()",  # Special characters
        ]

        for unicode_input in unicode_inputs:
            # These should generally be safe
            self.assertTrue(self.validator.validate_input(unicode_input, 'general'))

    def test_validate_input_with_sql_keywords_in_context(self):
        """Test that SQL keywords in safe context are allowed"""
        safe_sql_context = [
            "I'm reading about SQL databases",
            "The word 'select' in a sentence",
            "SQL is a database language",
            "SELECT is a keyword in SQL"
        ]

        for context in safe_sql_context:
            # These contain SQL keywords but are not injection attempts
            self.assertTrue(self.validator.validate_input(context, 'general'))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)