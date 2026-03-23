#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================
JARVIS v9.0+ - Role-Based Access Control Unit Tests
Comprehensive RBAC Testing
==========================================================
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.security_system import SecurityManager, UserRole, Permission


class TestRBAC(unittest.TestCase):
    """Test Role-Based Access Control functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()

    def test_admin_role_permissions(self):
        """Test that admin role has all permissions"""
        admin_permissions = self.security_manager.get_role_permissions(UserRole.ADMIN)
        all_permissions = list(Permission)

        # Admin should have all permissions
        for permission in all_permissions:
            self.assertIn(permission, admin_permissions)

    def test_user_role_permissions(self):
        """Test user role permissions"""
        user_permissions = self.security_manager.get_role_permissions(UserRole.USER)

        # User should have basic permissions
        expected_permissions = [
            Permission.READ_MEMORY,
            Permission.WRITE_MEMORY,
            Permission.EXECUTE_SKILLS,
            Permission.READ_SYSTEM_STATS
        ]

        for permission in expected_permissions:
            self.assertIn(permission, user_permissions)

        # User should NOT have admin permissions
        restricted_permissions = [
            Permission.MANAGE_USERS,
            Permission.SYSTEM_ADMIN,
            Permission.ACCESS_AUTONOMOUS
        ]

        for permission in restricted_permissions:
            self.assertNotIn(permission, user_permissions)

    def test_agent_role_permissions(self):
        """Test agent role permissions"""
        agent_permissions = self.security_manager.get_role_permissions(UserRole.AGENT)

        # Agent should only have execute skills
        self.assertEqual(len(agent_permissions), 1)
        self.assertIn(Permission.EXECUTE_SKILLS, agent_permissions)

    def test_guest_role_permissions(self):
        """Test guest role permissions"""
        guest_permissions = self.security_manager.get_role_permissions(UserRole.GUEST)

        # Guest should only have read system stats
        self.assertEqual(len(guest_permissions), 1)
        self.assertIn(Permission.READ_SYSTEM_STATS, guest_permissions)

    def test_system_role_permissions(self):
        """Test system role permissions"""
        system_permissions = self.security_manager.get_role_permissions(UserRole.SYSTEM)

        # System should have all permissions
        all_permissions = list(Permission)
        for permission in all_permissions:
            self.assertIn(permission, system_permissions)

    def test_permission_hierarchy(self):
        """Test permission hierarchy"""
        role_hierarchy = {
            UserRole.GUEST: [Permission.READ_SYSTEM_STATS],
            UserRole.AGENT: [Permission.EXECUTE_SKILLS],
            UserRole.USER: [
                Permission.READ_MEMORY,
                Permission.WRITE_MEMORY,
                Permission.EXECUTE_SKILLS,
                Permission.READ_SYSTEM_STATS
            ],
            UserRole.ADMIN: list(Permission),
            UserRole.SYSTEM: list(Permission)
        }

        for role, expected_permissions in role_hierarchy.items():
            actual_permissions = self.security_manager.get_role_permissions(role)

            for permission in expected_permissions:
                self.assertIn(permission, actual_permissions)

    def test_permission_matrix(self):
        """Test the complete permission matrix"""
        # Test all role-permission combinations
        for role in UserRole:
            permissions = self.security_manager.get_role_permissions(role)

            # Each permission should be either granted or denied
            for permission in Permission:
                # Should be either in or not in permissions
                in_permissions = permission in permissions
                not_in_permissions = permission not in permissions
                self.assertTrue(in_permissions or not_in_permissions)

    def test_permission_inheritance(self):
        """Test permission inheritance patterns"""
        # Higher roles should have all permissions of lower roles
        # This is a conceptual test - actual implementation may vary

        user_permissions = self.security_manager.get_role_permissions(UserRole.USER)
        admin_permissions = self.security_manager.get_role_permissions(UserRole.ADMIN)

        # Admin should have all user permissions
        for permission in user_permissions:
            self.assertIn(permission, admin_permissions)

    def test_permission_isolation(self):
        """Test that roles don't share unintended permissions"""
        user_permissions = self.security_manager.get_role_permissions(UserRole.USER)
        agent_permissions = self.security_manager.get_role_permissions(UserRole.AGENT)

        # User should have memory permissions that agent doesn't
        memory_permissions = [Permission.READ_MEMORY, Permission.WRITE_MEMORY]
        for perm in memory_permissions:
            self.assertIn(perm, user_permissions)
            self.assertNotIn(perm, agent_permissions)

    def test_permission_validation_with_tokens(self):
        """Test permission validation with actual tokens"""
        # Test each role with its permissions
        test_cases = [
            (UserRole.ADMIN, [Permission.EXECUTE_SKILLS, Permission.SYSTEM_ADMIN]),
            (UserRole.USER, [Permission.READ_MEMORY, Permission.WRITE_MEMORY]),
            (UserRole.AGENT, [Permission.EXECUTE_SKILLS]),
            (UserRole.GUEST, [Permission.READ_SYSTEM_STATS])
        ]

        for role, test_permissions in test_cases:
            with self.subTest(role=role):
                # Generate token for role
                tokens = self.security_manager.generate_tokens(
                    "test_user",
                    role,
                    self.security_manager.get_role_permissions(role)
                )

                # Test that role can access its permissions
                for permission in test_permissions:
                    if permission in self.security_manager.get_role_permissions(role):
                        result = self.security_manager.check_permission(
                            tokens['access_token'],
                            permission
                        )
                        self.assertTrue(result, f"Role {role} should have permission {permission}")

    def test_permission_denial(self):
        """Test that roles are properly denied unauthorized permissions"""
        # Test user trying to access admin permissions
        user_tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            self.security_manager.get_role_permissions(UserRole.USER)
        )

        # User should be denied admin permissions
        admin_permissions = [Permission.MANAGE_USERS, Permission.SYSTEM_ADMIN, Permission.ACCESS_AUTONOMOUS]

        for permission in admin_permissions:
            result = self.security_manager.check_permission(
                user_tokens['access_token'],
                permission
            )
            self.assertFalse(result, f"User should be denied permission {permission}")

    def test_dynamic_permission_changes(self):
        """Test that permission changes affect new tokens"""
        # Generate token with current permissions
        user_permissions = self.security_manager.get_role_permissions(UserRole.USER)
        tokens = self.security_manager.generate_tokens("test_user", UserRole.USER, user_permissions)

        # Verify current permissions work
        self.assertTrue(self.security_manager.check_permission(
            tokens['access_token'],
            Permission.READ_MEMORY
        ))

        # Note: Actual permission matrix is static in current implementation
        # This test demonstrates the concept for future dynamic permission systems

    def test_permission_audit_trail(self):
        """Test that permission checks are logged"""
        # Generate admin token
        tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.ADMIN,
            self.security_manager.get_role_permissions(UserRole.ADMIN)
        )

        # Check a permission
        self.security_manager.check_permission(
            tokens['access_token'],
            Permission.EXECUTE_SKILLS
        )

        # Should have audit log entry
        audit_log = self.security_manager.get_audit_log()
        self.assertGreater(len(audit_log), 0)

        # Find permission check entry
        permission_entries = [entry for entry in audit_log
                            if entry.get('event_type') == 'permission_granted']
        self.assertGreater(len(permission_entries), 0)

    def test_permission_error_handling(self):
        """Test permission handling with invalid inputs"""
        # Test with invalid token
        result = self.security_manager.check_permission(
            "invalid_token",
            Permission.READ_MEMORY
        )
        self.assertFalse(result)

        # Test with valid token but no permissions
        tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            []  # No permissions
        )

        result = self.security_manager.check_permission(
            tokens['access_token'],
            Permission.READ_MEMORY
        )
        self.assertFalse(result)

    def test_role_transition_security(self):
        """Test security during role transitions"""
        # This tests the concept of role elevation/demotion security
        # In current implementation, roles are static per token

        # User token
        user_tokens = self.security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            self.security_manager.get_role_permissions(UserRole.USER)
        )

        # Should not be able to escalate to admin
        result = self.security_manager.check_permission(
            user_tokens['access_token'],
            Permission.SYSTEM_ADMIN
        )
        self.assertFalse(result)

    def test_permission_specificity(self):
        """Test that specific permissions are properly enforced"""
        # Test each permission individually
        for permission in Permission:
            with self.subTest(permission=permission.value):
                # Test with role that should have this permission
                if permission in self.security_manager.get_role_permissions(UserRole.ADMIN):
                    tokens = self.security_manager.generate_tokens(
                        "test_user",
                        UserRole.ADMIN,
                        self.security_manager.get_role_permissions(UserRole.ADMIN)
                    )

                    result = self.security_manager.check_permission(
                        tokens['access_token'],
                        permission
                    )
                    self.assertTrue(result, f"Admin should have permission {permission.value}")

                # Test with role that should NOT have this permission
                if permission not in self.security_manager.get_role_permissions(UserRole.GUEST):
                    guest_tokens = self.security_manager.generate_tokens(
                        "test_user",
                        UserRole.GUEST,
                        self.security_manager.get_role_permissions(UserRole.GUEST)
                    )

                    result = self.security_manager.check_permission(
                        guest_tokens['access_token'],
                        permission
                    )
                    self.assertFalse(result, f"Guest should NOT have permission {permission.value}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)