# JARVIS v9.0+ Security Integration Guide

Complete guide for integrating the security system with FastAPI, gRPC, WhatsApp Bridge, and Autonomous Modules.

## Overview

This guide covers the integration of the comprehensive security system (Phase 1) with all JARVIS components:

- **FastAPI Routes**: Authentication and authorization for web API
- **gRPC Server**: Secure RPC calls with token validation
- **WhatsApp Bridge**: Token-based authentication for messaging
- **Autonomous Modules**: Permission-based decision making
- **Memory Controller**: Access control for memory operations

## Security Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   gRPC Server    │    │ WhatsApp Bridge │
│   Web API       │    │   RPC Service    │    │   Messaging     │
└─────────┬───────┘    └─────────┬────────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼─────────────┐
                    │     Security Middleware   │
                    │  - Authentication         │
                    │  - Authorization          │
                    │  - Input Validation       │
                    │  - Rate Limiting          │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │     Security Manager      │
                    │  - JWT Token Management   │
                    │  - Session Management     │
                    │  - Permission Checking    │
                    │  - Audit Logging          │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │    Core Components        │
                    │  - Memory Controller      │
                    │  - Autonomous Modules     │
                    │  - Skill System           │
                    └───────────────────────────┘
```

## 1. FastAPI Integration

### Current Implementation Status
✅ **ALREADY IMPLEMENTED** in `main.py`

The FastAPI routes already include comprehensive security:

```python
# Authentication and Authorization decorators
@app.post("/api/message")
async def process_message(request: MessageRequest):
    result = await orchestrator.process_message(
        request.message,
        request.context,
        request.user_id,
        request.auth_token  # ← JWT Token
    )
    return result

# Permission-based endpoints
@app.get("/api/automations")
async def get_automations(token: str = Header(None)):
    if not orchestrator.security_manager.check_permission(token, Permission.EXECUTE_SKILLS):
        return {"error": "Permission denied: execute skills required"}
    return {"suggestions": suggestions}

# Admin-only endpoints
@app.post("/api/decision")
async def make_decision(request: DecisionRequest, token: str = Header(None)):
    if not orchestrator.security_manager.check_permission(token, Permission.ACCESS_AUTONOMOUS):
        return {"error": "Permission denied: autonomous access required"}
    # ...
```

### Security Features in FastAPI
- **JWT Authentication**: All endpoints require valid JWT tokens
- **Role-Based Authorization**: Different permissions for different operations
- **Input Validation**: All inputs are validated and sanitized
- **Rate Limiting**: Protection against abuse
- **Audit Logging**: All security events are logged

## 2. gRPC Integration

### Current Implementation Status
⚠️ **NEEDS IMPLEMENTATION** in `grpc/python_server.py`

The gRPC server needs security integration:

```python
# Add to grpc/python_server.py
from core.security_system import SecurityManager, InputValidator, SecurityMiddleware

class JarvisServicer(jarvis_pb2_grpc.JarvisServicer):
    def __init__(self):
        self.security_manager = SecurityManager()
        self.input_validator = InputValidator()
        self.security_middleware = SecurityMiddleware(
            self.security_manager,
            self.input_validator
        )

    def Authenticate(self, request, context):
        """Authenticate user and return JWT tokens"""
        try:
            result = self.security_manager.authenticate_user(
                request.username,
                request.password,
                ip_address=context.peer(),
                user_agent=request.user_agent
            )

            if result:
                return jarvis_pb2.AuthenticateResponse(
                    success=True,
                    access_token=result['access_token'],
                    refresh_token=result['refresh_token'],
                    expires_in=result['expires_in'],
                    session_id=result['session_id']
                )
            else:
                return jarvis_pb2.AuthenticateResponse(
                    success=False,
                    error="Invalid credentials"
                )

        except Exception as e:
            return jarvis_pb2.AuthenticateResponse(
                success=False,
                error=str(e)
            )

    def ProcessMessage(self, request, context):
        """Process message with authentication"""
        try:
            # Authenticate request
            user_id = self.security_middleware.authenticate_request(
                {'Authorization': f'Bearer {request.auth_token}'},
                ip_address=context.peer()
            )

            if not user_id:
                return jarvis_pb2.ProcessMessageResponse(
                    success=False,
                    error="Authentication required"
                )

            # Check permissions
            if not self.security_manager.check_permission(
                request.auth_token,
                Permission.EXECUTE_SKILLS,
                ip_address=context.peer()
            ):
                return jarvis_pb2.ProcessMessageResponse(
                    success=False,
                    error="Permission denied"
                )

            # Validate input
            if not self.input_validator.validate_input(request.message, 'general'):
                return jarvis_pb2.ProcessMessageResponse(
                    success=False,
                    error="Invalid input detected"
                )

            # Process message
            response = self.orchestrator.process_message(
                request.message,
                request.context,
                user_id
            )

            return jarvis_pb2.ProcessMessageResponse(
                success=True,
                response_text=response["text"],
                processing_time_ms=response["metadata"]["latency_ms"]
            )

        except Exception as e:
            return jarvis_pb2.ProcessMessageResponse(
                success=False,
                error=str(e)
            )

    def RefreshToken(self, request, context):
        """Refresh JWT tokens"""
        try:
            result = self.security_manager.refresh_token(
                request.refresh_token,
                ip_address=context.peer()
            )

            if result:
                return jarvis_pb2.RefreshTokenResponse(
                    success=True,
                    access_token=result['access_token'],
                    refresh_token=result['refresh_token'],
                    session_id=result['session_id']
                )
            else:
                return jarvis_pb2.RefreshTokenResponse(
                    success=False,
                    error="Invalid refresh token"
                )

        except Exception as e:
            return jarvis_pb2.RefreshTokenResponse(
                success=False,
                error=str(e)
            )

    def ValidateToken(self, request, context):
        """Validate JWT token"""
        try:
            payload = self.security_manager.validate_token(
                request.token,
                'access',
                ip_address=context.peer()
            )

            if payload:
                return jarvis_pb2.ValidateTokenResponse(
                    valid=True,
                    user_id=payload['user_id'],
                    role=payload['role'],
                    permissions=payload['permissions']
                )
            else:
                return jarvis_pb2.ValidateTokenResponse(
                    valid=False,
                    error="Invalid or expired token"
                )

        except Exception as e:
            return jarvis_pb2.ValidateTokenResponse(
                valid=False,
                error=str(e)
            )
```

### gRPC Security Features
- **Token-based Authentication**: All RPC calls require JWT tokens
- **Permission Checking**: Role-based access to different operations
- **Input Validation**: Sanitize all incoming data
- **Audit Logging**: Log all authentication and authorization events
- **IP Address Binding**: Prevent token theft and reuse

## 3. WhatsApp Bridge Integration

### Current Implementation Status
⚠️ **NEEDS IMPLEMENTATION** in `whatsapp/baileys_bridge.js`

The WhatsApp bridge needs security integration:

```javascript
// Add to whatsapp/baileys_bridge.js
const { SecurityManager } = require('../core/security_system.js');

class SecureWhatsAppBridge extends WhatsAppBridge {
    constructor() {
        super();
        this.securityManager = new SecurityManager();
        this.activeTokens = new Map(); // Store tokens for users
    }

    async authenticateUser(username, password) {
        try {
            const result = await this.securityManager.authenticateUser({
                username,
                password,
                ipAddress: this.getClientIP(),
                userAgent: this.getUserAgent()
            });

            if (result.success) {
                this.activeTokens.set(username, {
                    accessToken: result.accessToken,
                    refreshToken: result.refreshToken,
                    expiresAt: Date.now() + (result.expiresIn * 1000)
                });
                return result;
            } else {
                this.logSecurityEvent('authentication_failed', username);
                return { success: false, error: 'Authentication failed' };
            }
        } catch (error) {
            this.logSecurityEvent('authentication_error', null, { error: error.message });
            return { success: false, error: 'Authentication service unavailable' };
        }
    }

    async getValidToken(username) {
        const tokenData = this.activeTokens.get(username);
        if (!tokenData) {
            return null;
        }

        // Check if token is expired
        if (Date.now() >= tokenData.expiresAt) {
            try {
                const result = await this.securityManager.refreshToken({
                    refreshToken: tokenData.refreshToken,
                    ipAddress: this.getClientIP()
                });

                if (result.success) {
                    this.activeTokens.set(username, {
                        accessToken: result.accessToken,
                        refreshToken: result.refreshToken,
                        expiresAt: Date.now() + (result.expiresIn * 1000)
                    });
                    return result.accessToken;
                } else {
                    this.activeTokens.delete(username);
                    return null;
                }
            } catch (error) {
                this.logSecurityEvent('token_refresh_failed', username, { error: error.message });
                this.activeTokens.delete(username);
                return null;
            }
        }

        return tokenData.accessToken;
    }

    async forwardMessageToGRPC(from, text) {
        try {
            // Get valid token for this user
            const token = await this.getValidToken(from);
            if (!token) {
                await this.sendMessageDirect(from, 'Please authenticate first. Send: /login username password');
                return;
            }

            // Validate input
            if (!this.securityManager.validateInput(text, 'general')) {
                await this.sendMessageDirect(from, 'Message contains invalid content.');
                this.logSecurityEvent('input_validation_failed', from, { content: text });
                return;
            }

            // Check permissions
            if (!await this.securityManager.checkPermission(token, 'EXECUTE_SKILLS')) {
                await this.sendMessageDirect(from, 'You do not have permission to execute skills.');
                this.logSecurityEvent('permission_denied', from, { permission: 'EXECUTE_SKILLS' });
                return;
            }

            // Forward to gRPC with authentication
            const response = await this.grpcClient.processMessage({
                from,
                text,
                auth_token: token
            });

            if (response.success) {
                await this.sendMessageDirect(from, response.responseText);
            } else {
                await this.sendMessageDirect(from, 'Error processing your request.');
                this.logSecurityEvent('grpc_error', from, { error: response.error });
            }

        } catch (error) {
            logger.error({ error }, 'Failed to forward message via gRPC');
            await this.sendMessageDirect(from, 'Service temporarily unavailable.');
            this.logSecurityEvent('grpc_forward_error', from, { error: error.message });
        }
    }

    logSecurityEvent(eventType, userId, details) {
        try {
            this.securityManager.logSecurityEvent({
                eventType,
                userId,
                ipAddress: this.getClientIP(),
                userAgent: this.getUserAgent(),
                details
            });
        } catch (error) {
            logger.error({ error }, 'Failed to log security event');
        }
    }
}
```

### WhatsApp Bridge Security Features
- **User Authentication**: Users must authenticate before using JARVIS
- **Token Management**: Automatic token refresh and validation
- **Input Validation**: Sanitize all incoming messages
- **Permission Checking**: Role-based access to different features
- **Security Logging**: Log all security events

## 4. Autonomous Module Integration

### Current Implementation Status
⚠️ **NEEDS IMPLEMENTATION** in autonomous modules

Autonomous modules need permission-based decision making:

```python
# Add to autonomous_decision.py or similar
class SecureAutonomousDecision:
    def __init__(self, security_manager):
        self.security_manager = security_manager

    def evaluate_decision(self, action, context, confidence, user_id, auth_token):
        """Evaluate autonomous decision with security checks"""

        # Check if user has permission for autonomous actions
        if not self.security_manager.check_permission(
            auth_token,
            Permission.ACCESS_AUTONOMOUS
        ):
            return {
                'decision': 'blocked',
                'reason': 'User lacks autonomous access permission',
                'risk_score': 10.0,
                'suggested_action': 'Request elevated permissions from administrator'
            }

        # Check if action requires elevated privileges
        high_risk_actions = [
            'system_configuration',
            'user_management',
            'security_policy_changes'
        ]

        if action in high_risk_actions:
            if not self.security_manager.check_permission(
                auth_token,
                Permission.SYSTEM_ADMIN
            ):
                return {
                    'decision': 'blocked',
                    'reason': f'Action {action} requires SYSTEM_ADMIN permission',
                    'risk_score': 9.0,
                    'suggested_action': 'Contact system administrator'
                }

        # Evaluate decision as normal
        decision = self._evaluate_normal_decision(action, context, confidence)

        # Log autonomous decision
        self.security_manager._log_security_event(
            "autonomous_decision",
            user_id,
            context.get('ip_address'),
            {
                'action': action,
                'decision': decision['decision'],
                'confidence': confidence,
                'risk_score': decision['risk_score']
            },
            "medium" if decision['risk_score'] < 5.0 else "high"
        )

        return decision

    def _evaluate_normal_decision(self, action, context, confidence):
        """Normal decision evaluation logic"""
        # ... existing logic ...
        return {
            'decision': 'proceed' if confidence > 0.7 else 'wait',
            'confidence': confidence,
            'risk_score': 3.0,
            'reasoning': 'Normal decision evaluation'
        }
```

### Autonomous Module Security Features
- **Permission-Based Decisions**: Only authorized users can trigger autonomous actions
- **Risk Assessment**: Evaluate security risk of autonomous decisions
- **Audit Logging**: Log all autonomous decision making
- **High-Risk Action Protection**: Block dangerous actions without proper permissions

## 5. Memory Controller Integration

### Current Implementation Status
⚠️ **NEEDS IMPLEMENTATION** in `memory/memory_controller.py`

Memory operations need access control:

```python
# Add to memory_controller.py
class SecureMemoryController:
    def __init__(self, security_manager):
        self.security_manager = security_manager
        # ... existing initialization ...

    def store(self, text, memory_type="conversation", metadata=None, auth_token=None, user_id=None):
        """Store memory with security checks"""

        # Validate input
        if not self.security_manager.input_validator.validate_input(text, 'general'):
            raise ValueError("Input contains invalid content")

        # Check permissions based on memory type
        required_permission = self._get_required_permission_for_memory_type(memory_type)

        if auth_token and not self.security_manager.check_permission(
            auth_token,
            required_permission
        ):
            raise PermissionError(f"Insufficient permissions for memory type: {memory_type}")

        # Store with security metadata
        security_metadata = {
            'stored_by': user_id,
            'stored_at': datetime.now().isoformat(),
            'memory_type': memory_type,
            'security_level': self._classify_security_level(text)
        }

        if metadata:
            security_metadata.update(metadata)

        # Call existing store method
        super().store(text, memory_type, security_metadata)

        # Log security event
        self.security_manager._log_security_event(
            "memory_stored",
            user_id,
            None,
            {
                'memory_type': memory_type,
                'security_level': security_metadata['security_level'],
                'text_length': len(text)
            },
            "low"
        )

    def retrieve(self, query, top_k=5, memory_type=None, auth_token=None, user_id=None):
        """Retrieve memory with security checks"""

        # Validate query
        if not self.security_manager.input_validator.validate_input(query, 'query'):
            raise ValueError("Query contains invalid content")

        # Check read permissions
        if auth_token and not self.security_manager.check_permission(
            auth_token,
            Permission.READ_MEMORY
        ):
            raise PermissionError("Insufficient permissions to read memory")

        # Filter results based on user permissions
        results = super().retrieve(query, top_k, memory_type)

        if auth_token and user_id:
            results = self._filter_results_by_permissions(results, user_id)

        return results

    def _get_required_permission_for_memory_type(self, memory_type):
        """Get required permission for different memory types"""
        permission_map = {
            'conversation': Permission.READ_MEMORY,
            'technical': Permission.READ_MEMORY,
            'project': Permission.READ_MEMORY,
            'admin': Permission.SYSTEM_ADMIN,
            'sensitive': Permission.SYSTEM_ADMIN,
            'autonomous': Permission.ACCESS_AUTONOMOUS
        }
        return permission_map.get(memory_type, Permission.READ_MEMORY)

    def _classify_security_level(self, text):
        """Classify security level of stored content"""
        # Check for sensitive information
        sensitive_keywords = ['password', 'secret', 'key', 'token', 'admin']
        if any(keyword in text.lower() for keyword in sensitive_keywords):
            return 'high'
        elif len(text) > 1000:
            return 'medium'
        else:
            return 'low'

    def _filter_results_by_permissions(self, results, user_id):
        """Filter memory results based on user permissions"""
        # This would implement fine-grained access control
        # For now, return all results for users with READ_MEMORY permission
        return results
```

### Memory Controller Security Features
- **Access Control**: Different permissions for different memory types
- **Input Validation**: Sanitize all stored content
- **Security Classification**: Classify memory based on sensitivity
- **Audit Logging**: Log all memory operations
- **Data Filtering**: Filter results based on user permissions

## Implementation Priority

### Phase 1: Core Security (Current)
1. ✅ **Security System Core**: Complete and tested
2. ✅ **FastAPI Integration**: Already implemented
3. 🔄 **gRPC Integration**: Needs implementation
4. 🔄 **WhatsApp Bridge**: Needs implementation
5. 🔄 **Autonomous Modules**: Needs implementation
6. 🔄 **Memory Controller**: Needs implementation

### Phase 2: Advanced Security (Future)
1. **Multi-Factor Authentication**: Add 2FA support
2. **Device Management**: Track and manage authorized devices
3. **Behavioral Analysis**: Detect anomalous user behavior
4. **Advanced Threat Detection**: ML-based attack detection
5. **Security Analytics**: Advanced security reporting and dashboards

## Testing Security Integration

### Integration Test Examples

```python
# test_security_integration.py
class TestSecurityIntegration(unittest.TestCase):
    def test_complete_auth_flow(self):
        """Test complete authentication flow across all components"""

        # 1. Authenticate via gRPC
        auth_response = grpc_client.authenticate(username="admin", password="password")

        # 2. Use token in FastAPI
        api_response = requests.post("/api/message", headers={
            "Authorization": f"Bearer {auth_response.access_token}"
        }, json={"message": "test"})

        # 3. Use token in WhatsApp bridge
        whatsapp_response = whatsapp_bridge.forward_message(
            user_id="admin",
            text="test message",
            auth_token=auth_response.access_token
        )

        # 4. Verify all components work together
        self.assertTrue(api_response.success)
        self.assertTrue(whatsapp_response.success)

    def test_permission_isolation(self):
        """Test that permissions are enforced across all components"""

        # Create user with limited permissions
        user_response = security_manager.authenticate_user(
            "limited_user",
            "password"
        )

        # Try to access admin-only features
        admin_api_response = requests.get("/api/system/stats", headers={
            "Authorization": f"Bearer {user_response.access_token}"
        })
        self.assertEqual(admin_api_response.status_code, 403)  # Forbidden

        # Try to trigger autonomous actions
        auto_response = grpc_client.make_autonomous_decision(
            action="system_configuration",
            auth_token=user_response.access_token
        )
        self.assertFalse(auto_response.success)
```

## Security Configuration

### Environment Variables

```bash
# Add to .env
JWT_SECRET=your_64_character_jwt_secret_key_here
JWT_ACCESS_EXPIRATION=1800        # 30 minutes
JWT_REFRESH_EXPIRATION=86400      # 24 hours
MAX_FAILED_ATTEMPTS=5
LOCKOUT_DURATION=900              # 15 minutes
MAX_SESSIONS_PER_USER=5
MAX_INPUT_LENGTH=50000
MAX_QUERY_LENGTH=10000
MAX_CONTEXT_LENGTH=100000
```

### Security Headers

```python
# Add to FastAPI middleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(
    HTTPSRedirectMiddleware,
    secure=True
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

## Monitoring and Alerting

### Security Metrics to Monitor

1. **Authentication Metrics**
   - Login success/failure rates
   - Token refresh frequency
   - Session duration and activity

2. **Authorization Metrics**
   - Permission denied events
   - Access attempts to restricted resources
   - Role escalation attempts

3. **Security Events**
   - Failed authentication attempts
   - Suspicious input patterns
   - Rate limiting violations

4. **Performance Metrics**
   - Authentication response time
   - Authorization check latency
   - Security middleware overhead

### Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: security_alerts
    rules:
      - alert: HighFailedLogins
        expr: rate(security_auth_failures[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High number of failed login attempts"

      - alert: PermissionDeniedHighRate
        expr: rate(security_permission_denied[5m]) > 20
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "High rate of permission denied events"

      - alert: SecurityMiddlewareHighLatency
        expr: histogram_quantile(0.95, rate(security_middleware_duration_seconds_bucket[5m])) > 0.5
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Security middleware response time is high"
```

## Conclusion

This integration guide provides a comprehensive roadmap for securing all JARVIS v9.0+ components. The security system is designed to be:

- **Comprehensive**: Covers all attack vectors and security concerns
- **Performant**: Minimal impact on system performance
- **Scalable**: Can handle high-volume authentication and authorization
- **Auditable**: Complete logging and monitoring capabilities
- **Maintainable**: Clear separation of concerns and well-documented code

The Phase 1 implementation focuses on core authentication and authorization, providing a solid foundation for the advanced security features planned for future phases.