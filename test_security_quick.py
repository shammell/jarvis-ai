#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick security test runner to verify tests work
"""

import sys
import os
import unittest

# Add project root to path
sys.path.insert(0, '/c/Users/AK/jarvis_project')

def run_security_tests():
    """Run security tests quickly"""

    # Test individual components
    print("Testing Security System Components...")

    try:
        # Test SecurityManager import
        from core.security_system import SecurityManager, UserRole, Permission
        print("✓ SecurityManager imports successfully")

        # Test basic functionality
        security_manager = SecurityManager()
        print("✓ SecurityManager initializes successfully")

        # Test password hashing
        hashed = security_manager.hash_password("test_password")
        verified = security_manager.verify_password("test_password", hashed)
        assert verified, "Password verification failed"
        print("✓ Password hashing/verification works")

        # Test token generation
        tokens = security_manager.generate_tokens(
            "test_user",
            UserRole.USER,
            [Permission.READ_MEMORY]
        )
        assert 'access_token' in tokens, "Token generation failed"
        print("✓ JWT token generation works")

        # Test token validation
        payload = security_manager.validate_token(tokens['access_token'], 'access')
        assert payload is not None, "Token validation failed"
        assert payload['user_id'] == 'test_user', "Token payload incorrect"
        print("✓ JWT token validation works")

        # Test permission checking
        has_permission = security_manager.check_permission(
            tokens['access_token'],
            Permission.READ_MEMORY
        )
        assert has_permission, "Permission checking failed"
        print("✓ Permission checking works")

        print("\n🎉 All basic security functionality tests PASSED!")

    except Exception as e:
        print(f"❌ Security test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == '__main__':
    success = run_security_tests()
    sys.exit(0 if success else 1)