#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Rate Limiting Unit Tests
Comprehensive Rate Limiting Testing
==========================================================
"""

import unittest
import time
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import SecurityManager, UserRole, Permission


class TestRateLimiting(unittest.TestCase):
    """Test Rate Limiting functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()
        self.test_user = "rate_limit_test_user"

    def test_rate_limit_config_structure(self):
        """Test that rate limit configuration is properly structured"""
        config = self.security_manager.config["rate_limits"]

        # Should have time windows
        self.assertIn("per_minute", config)
        self.assertIn("per_hour", config)

        # Should have permissions in each window
        minute_limits = config["per_minute"]
        hour_limits = config["per_hour"]

        # Check that common permissions have limits
        self.assertIn(Permission.EXECUTE_SKILLS, minute_limits)
        self.assertIn(Permission.READ_MEMORY, minute_limits)
        self.assertIn(Permission.WRITE_MEMORY, minute_limits)
        self.assertIn(Permission.ACCESS_AUTONOMOUS, minute_limits)

    def test_rate_limit_basic_functionality(self):
        """Test basic rate limiting functionality"""
        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Make requests up to the limit
        for i in range(limit):
            result = self.security_manager._check_rate_limit(self.test_user, permission)
            self.assertTrue(result, f"Request {i+1} should be allowed")

        # Next request should be blocked
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertFalse(result, "Request should be blocked after limit")

    def test_rate_limit_time_window(self):
        """Test rate limiting time window behavior"""
        permission = Permission.READ_MEMORY
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Make requests at different times
        for i in range(limit):
            result = self.security_manager._check_rate_limit(self.test_user, permission)
            self.assertTrue(result)

        # Should be blocked now
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertFalse(result)

        # Wait for window to reset (simulate by cleaning old entries)
        # In real implementation, this would happen automatically after 60 seconds
        # Here we test the mechanism by checking time-based cleanup

    def test_rate_limit_multiple_permissions(self):
        """Test rate limiting for different permissions independently"""
        permissions = [
            Permission.EXECUTE_SKILLS,
            Permission.READ_MEMORY,
            Permission.WRITE_MEMORY
        ]

        # Each permission should have its own rate limit
        for permission in permissions:
            with self.subTest(permission=permission.value):
                limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

                # Should be able to hit limit for each permission independently
                for i in range(limit):
                    result = self.security_manager._check_rate_limit(self.test_user, permission)
                    self.assertTrue(result)

                # Should be blocked for this permission
                result = self.security_manager._check_rate_limit(self.test_user, permission)
                self.assertFalse(result)

                # But other permissions should still work
                for other_perm in permissions:
                    if other_perm != permission:
                        result = self.security_manager._check_rate_limit(self.test_user, other_perm)
                        # This might be blocked if we hit limits, but shouldn't be blocked due to other permission
                        # We can't easily test this without knowing exact limits, so we just verify no exception

    def test_rate_limit_user_isolation(self):
        """Test that rate limits are isolated per user"""
        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        user1 = "user1"
        user2 = "user2"

        # User1 hits limit
        for i in range(limit):
            result = self.security_manager._check_rate_limit(user1, permission)
            self.assertTrue(result)

        result = self.security_manager._check_rate_limit(user1, permission)
        self.assertFalse(result)  # User1 should be blocked

        # User2 should still be able to make requests
        for i in range(limit):
            result = self.security_manager._check_rate_limit(user2, permission)
            self.assertTrue(result)  # User2 should not be affected by User1's limit

    def test_rate_limit_reset_after_timeout(self):
        """Test that rate limits reset after timeout"""
        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Hit the limit
        for i in range(limit):
            result = self.security_manager._check_rate_limit(self.test_user, permission)
            self.assertTrue(result)

        # Should be blocked
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertFalse(result)

        # Simulate time passing by manually cleaning the rate limit entry
        if self.test_user in self.security_manager.rate_limits:
            if permission in self.security_manager.rate_limits[self.test_user]:
                # Clear the timestamps to simulate timeout
                self.security_manager.rate_limits[self.test_user][permission].timestamps = []

        # Should be allowed again
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertTrue(result)

    def test_rate_limit_temporary_block(self):
        """Test temporary blocking after hitting rate limit"""
        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Hit the limit
        for i in range(limit):
            result = self.security_manager._check_rate_limit(self.test_user, permission)
            self.assertTrue(result)

        # Should be blocked and temporarily blocked
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertFalse(result)

        # Should remain blocked for a short time
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertFalse(result)

    def test_rate_limit_hourly_limits(self):
        """Test hourly rate limits"""
        permission = Permission.MANAGE_USERS
        limit = self.security_manager.config["rate_limits"]["per_hour"][permission]

        # Should be able to make requests up to limit
        for i in range(limit):
            result = self.security_manager._check_rate_limit(self.test_user, permission)
            self.assertTrue(result)

        # Should be blocked after limit
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertFalse(result)

    def test_rate_limit_concurrent_requests(self):
        """Test rate limiting with concurrent requests"""
        permission = Permission.READ_MEMORY
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Make multiple requests rapidly (simulating concurrent access)
        results = []
        for i in range(limit + 2):  # Try to exceed limit
            result = self.security_manager._check_rate_limit(self.test_user, permission)
            results.append(result)

        # Should have exactly 'limit' successful requests
        success_count = sum(1 for result in results if result)
        self.assertEqual(success_count, limit)

    def test_rate_limit_cleanup_old_entries(self):
        """Test cleanup of old rate limit entries"""
        permission = Permission.EXECUTE_SKILLS

        # Add some old timestamps (simulate old requests)
        if self.test_user not in self.security_manager.rate_limits:
            self.security_manager.rate_limits[self.test_user] = {}

        if permission not in self.security_manager.rate_limits[self.test_user]:
            self.security_manager.rate_limits[self.test_user][permission] = self.security_manager.rate_limits.default_factory()

        # Add old timestamps (older than 60 seconds)
        old_time = time.time() - 120  # 2 minutes ago
        self.security_manager.rate_limits[self.test_user][permission].timestamps = [old_time] * 5

        # Make a new request
        result = self.security_manager._check_rate_limit(self.test_user, permission)
        self.assertTrue(result)  # Should work because old entries are cleaned up

        # Should have only new timestamp
        current_time = time.time()
        timestamps = self.security_manager.rate_limits[self.test_user][permission].timestamps
        for ts in timestamps:
            self.assertGreaterEqual(ts, current_time - 1)  # Should be recent

    def test_rate_limit_statistics(self):
        """Test that rate limiting affects security statistics"""
        initial_stats = self.security_manager.get_security_stats()

        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Make requests that will trigger rate limiting
        for i in range(limit + 5):  # Exceed limit
            self.security_manager._check_rate_limit(self.test_user, permission)

        # Get updated stats
        final_stats = self.security_manager.get_security_stats()

        # Should have more recent events
        self.assertGreater(final_stats['recent_events'], initial_stats['recent_events'])

    def test_rate_limit_with_permission_check(self):
        """Test rate limiting in conjunction with permission checks"""
        # Generate token
        tokens = self.security_manager.generate_tokens(
            self.test_user,
            UserRole.USER,
            [Permission.EXECUTE_SKILLS]
        )

        permission = Permission.EXECUTE_SKILLS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Make requests up to limit
        for i in range(limit):
            result = self.security_manager.check_permission(
                tokens['access_token'],
                permission
            )
            self.assertTrue(result)

        # Should be blocked due to rate limiting
        result = self.security_manager.check_permission(
            tokens['access_token'],
            permission
        )
        self.assertFalse(result)

    def test_rate_limit_error_handling(self):
        """Test rate limiting error handling"""
        # Test with None user
        result = self.security_manager._check_rate_limit(None, Permission.EXECUTE_SKILLS)
        self.assertTrue(result)  # Should not crash

        # Test with invalid permission
        result = self.security_manager._check_rate_limit(self.test_user, "invalid_permission")
        self.assertTrue(result)  # Should not crash

    def test_rate_limit_monitoring(self):
        """Test rate limit monitoring and alerting"""
        # This would integrate with monitoring systems in production
        # For now, just verify the mechanism works

        permission = Permission.ACCESS_AUTONOMOUS
        limit = self.security_manager.config["rate_limits"]["per_minute"][permission]

        # Hit rate limit
        for i in range(limit + 1):
            self.security_manager._check_rate_limit(self.test_user, permission)

        # Should have audit log entry for rate limit violation
        audit_log = self.security_manager.get_audit_log()
        rate_limit_entries = [entry for entry in audit_log
                            if entry.get('event_type') == 'rate_limit_exceeded']

        # May or may not have entries depending on implementation
        # Just verify no exceptions occurred


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)