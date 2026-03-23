# JARVIS v9.0+ Security Testing Framework

Comprehensive security testing suite for the JARVIS v9.0+ authentication and authorization system.

## Overview

This security testing framework provides:

- **Unit Tests**: Test individual security components in isolation
- **Integration Tests**: Test security components working together
- **End-to-End Tests**: Test complete security flows from authentication to authorization
- **Coverage Analysis**: Verify test coverage across all security components
- **Performance Tests**: Ensure security doesn't impact system performance

## Test Structure

```
tests/security/
├── README.md                           # This file
├── run_security_tests.py              # Main test runner
├── test_security_coverage.py          # Coverage analysis
├── test_security_manager.py           # SecurityManager unit tests
├── test_input_validator.py            # InputValidator unit tests
├── test_security_middleware.py        # SecurityMiddleware unit tests
├── test_jwt_auth.py                   # JWT authentication tests
├── test_rbac.py                       # Role-based access control tests
├── test_rate_limiting.py              # Rate limiting tests
├── test_security_integration.py       # Integration tests
└── test_security_e2e.py               # End-to-end security tests
```

## Security Components Tested

### 1. SecurityManager
- JWT token generation and validation
- User authentication and session management
- Permission checking and role-based access
- Rate limiting and failed attempt tracking
- Security event logging and audit trails

### 2. InputValidator
- SQL injection prevention
- XSS attack prevention
- Command injection prevention
- Input sanitization and validation
- File path validation
- Query and context validation

### 3. SecurityMiddleware
- Request authentication and authorization
- Input sanitization at middleware level
- Security event correlation
- Integration with SecurityManager and InputValidator

### 4. JWT Authentication
- Token structure and claims validation
- Token expiration and refresh
- IP address and user agent binding
- Token rotation and invalidation
- Secret key management

### 5. Role-Based Access Control (RBAC)
- Permission hierarchy validation
- Role isolation and separation
- Dynamic permission checking
- Permission escalation prevention

### 6. Rate Limiting
- Per-user and per-permission rate limits
- Time window enforcement
- Temporary blocking mechanisms
- Rate limit monitoring and alerting

## Running Tests

### Quick Start

```bash
# Run all security tests
python tests/security/run_security_tests.py

# Run individual test files
python -m unittest tests.security.test_security_manager -v
python -m unittest tests.security.test_jwt_auth -v
python -m unittest tests.security.test_rbac -v

# Run with pytest (recommended)
pytest tests/security/ -v

# Run with coverage
coverage run -m pytest tests/security/
coverage report -m
coverage html  # Generate HTML report
```

### Test Execution Options

```bash
# Run specific test suites
python -m unittest tests.security.test_jwt_auth.TestJWTAuthentication.test_jwt_token_structure

# Run with detailed output
python -m unittest tests.security.test_security_manager -v -k test_authenticate_user

# Run integration tests only
python -m unittest tests.security.test_security_integration -v

# Run E2E tests only
python -m unittest tests.security.test_security_e2e -v
```

## Test Coverage Requirements

### Minimum Coverage Standards
- **Overall Coverage**: 80%+ for all security components
- **Critical Security Paths**: 95%+ coverage
- **Attack Vector Tests**: 100% coverage of known vulnerabilities
- **Error Handling**: 100% coverage of error conditions

### Coverage Analysis
The framework includes automated coverage analysis:

```python
from tests.security.test_security_coverage import SecurityCoverageAnalyzer
analyzer = SecurityCoverageAnalyzer()
coverage_stats = analyzer.run_coverage_analysis()
```

## Security Test Categories

### 1. Authentication Tests
- Valid user authentication
- Invalid credentials handling
- Token generation and validation
- Session management
- Multi-factor authentication (if implemented)

### 2. Authorization Tests
- Permission checking
- Role-based access control
- Resource access validation
- Privilege escalation prevention

### 3. Input Validation Tests
- SQL injection attacks
- XSS attacks
- Command injection attacks
- Directory traversal attacks
- Input sanitization

### 4. Rate Limiting Tests
- Per-user rate limits
- Per-permission rate limits
- Time window enforcement
- Lockout mechanisms

### 5. Security Monitoring Tests
- Audit logging
- Security event generation
- Alerting mechanisms
- Performance impact measurement

## Security Attack Simulations

The framework includes comprehensive attack simulations:

### SQL Injection Attacks
```python
sql_payloads = [
    "'; DROP TABLE users; --",
    "1' UNION SELECT password FROM admin --",
    "' OR '1'='1"
]
```

### XSS Attacks
```python
xss_payloads = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert('xss')"
]
```

### Command Injection Attacks
```python
cmd_payloads = [
    "rm -rf /",
    "cat /etc/passwd",
    "whoami; id"
]
```

## Performance Testing

Security tests include performance validation:

```python
# Authentication performance
auth_per_second = 100 / auth_time
assert auth_per_second > 10  # At least 10 auth/sec

# Permission checking performance
perm_per_second = 1000 / perm_time
assert perm_per_second > 100  # At least 100 checks/sec

# Input validation performance
validation_per_second = 500 / validation_time
assert validation_per_second > 500  # At least 500 validations/sec
```

## Integration with CI/CD

### GitHub Actions Integration
```yaml
name: Security Tests
on: [push, pull_request]
jobs:
  security-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install coverage pytest
      - name: Run security tests
        run: |
          coverage run -m pytest tests/security/
          coverage report -m
          coverage xml
      - name: Upload coverage
        uses: codecov/codecov-action@v1
        with:
          file: ./coverage.xml
```

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
echo "Running security tests before commit..."
python tests/security/run_security_tests.py
if [ $? -ne 0 ]; then
    echo "Security tests failed. Commit blocked."
    exit 1
fi
```

## Security Test Best Practices

### 1. Test Isolation
- Each test should be independent
- Use test fixtures and mocks appropriately
- Clean up test data after each test

### 2. Test Data Management
- Use test-specific user accounts
- Generate unique test data for each run
- Clean up test data in tearDown methods

### 3. Security Test Principles
- Test both positive and negative cases
- Test edge cases and boundary conditions
- Test concurrent access scenarios
- Test with malformed and malicious input

### 4. Performance Considerations
- Security tests should not significantly slow down CI/CD
- Use appropriate timeouts
- Optimize test data generation
- Consider parallel test execution

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure PYTHONPATH is set correctly
   export PYTHONPATH=/path/to/jarvis_project:$PYTHONPATH
   ```

2. **Missing Dependencies**
   ```bash
   pip install -r requirements.txt
   pip install coverage pytest
   ```

3. **Test Failures**
   - Check test output for specific error messages
   - Verify security configuration in `.env`
   - Ensure required services are running

4. **Coverage Issues**
   - Ensure source files are included in coverage
   - Check coverage configuration
   - Verify test files are in correct location

### Debug Mode
```bash
# Run tests in debug mode
python -m unittest tests.security.test_security_manager -v -b

# Run with detailed traceback
python -m unittest tests.security.test_jwt_auth -v -f

# Run specific test method
python -m unittest tests.security.test_rbac.TestRBAC.test_admin_role_permissions -v
```

## Security Test Maintenance

### Regular Updates
- Update test cases when security requirements change
- Add new attack vector tests as vulnerabilities are discovered
- Review and update test data regularly
- Maintain test documentation

### Security Review Process
1. **Code Review**: All security tests must be reviewed by security team
2. **Test Review**: Regular review of test effectiveness
3. **Coverage Review**: Monthly coverage analysis and improvement
4. **Performance Review**: Monitor test execution time and optimize

## Contributing

### Adding New Security Tests
1. Identify the security component to test
2. Create appropriate test class in `tests/security/`
3. Follow naming convention: `test_[component].py`
4. Include comprehensive test cases
5. Add to test runner if needed
6. Update this README

### Test Development Guidelines
- Use descriptive test method names
- Include docstrings for complex tests
- Use appropriate assertions
- Clean up test resources
- Document test dependencies

## Security Compliance

This testing framework helps ensure compliance with:

- **OWASP Top 10**: Tests for common web application security risks
- **NIST Cybersecurity Framework**: Security testing and validation
- **ISO 27001**: Information security management
- **SOC 2**: Security controls testing

## Support

For questions or issues with the security testing framework:

1. Check this README for common solutions
2. Review test output for specific error messages
3. Check GitHub issues for known problems
4. Contact the security team for complex issues

---

**Note**: This security testing framework is critical for maintaining the security posture of JARVIS v9.0+. All security changes must include appropriate tests and maintain the required coverage levels.