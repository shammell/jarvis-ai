# ==========================================================
# JARVIS v9.0 - API Routes
# FastAPI routes extracted from main.py
# ==========================================================

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging

from core.security_system import Permission

logger = logging.getLogger(__name__)


# Request models
class MessageRequest(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None


class DecisionRequest(BaseModel):
    action: str
    context: Optional[Dict[str, Any]] = None


class AgentTeamRequest(BaseModel):
    goal: str
    agents: List[str]
    context: Optional[Dict[str, Any]] = None


def setup_routes(app: FastAPI, orchestrator):
    """Setup all API routes"""

    @app.post("/api/message")
    async def process_message(request: MessageRequest):
        """Process a message through JARVIS"""
        return await orchestrator.process_message(request.message, request.context)

    @app.post("/api/first-principles")
    async def first_principles_analysis(request: MessageRequest):
        """Analyze using first principles reasoning"""
        try:
            analysis = orchestrator.first_principles.analyze(
                request.message,
                request.context or {}
            )
            return {"success": True, "analysis": analysis}
        except Exception as e:
            logger.error(f"First principles analysis failed: {e}")
            return {"success": False, "error": str(e)}

    @app.get("/api/automations")
    async def get_automations(token: str = Header(None)):
        """Get detected automations"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")

        payload = orchestrator.security_manager.validate_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        automations = orchestrator.hyper_automation.get_automations()
        return {"automations": automations}

    @app.post("/api/decision")
    async def make_decision(request: DecisionRequest, token: str = Header(None)):
        """Make autonomous decision"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")

        payload = orchestrator.security_manager.validate_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        if not orchestrator.security_manager.check_permission(token, Permission.ACCESS_AUTONOMOUS):
            raise HTTPException(status_code=403, detail="Permission denied")

        decision = orchestrator.autonomous.evaluate_decision(
            request.action,
            request.context or {}
        )
        return {"decision": decision}

    @app.post("/api/agent-team")
    async def execute_agent_team(request: AgentTeamRequest, token: str = Header(None)):
        """Execute multi-agent team"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")

        payload = orchestrator.security_manager.validate_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        result = await orchestrator.autonomy_system.swarm_coordinator.coordinate(
            request.goal,
            request.agents,
            request.context or {}
        )
        return result

    @app.get("/api/stats")
    async def get_stats(token: str = Header(None)):
        """Get system statistics"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")

        payload = orchestrator.security_manager.validate_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        return orchestrator.get_system_stats()

    @app.post("/api/optimize")
    async def optimize(token: str = Header(None)):
        """Run system optimization"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")

        payload = orchestrator.security_manager.validate_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")

        if not orchestrator.security_manager.check_permission(token, Permission.SYSTEM_ADMIN):
            raise HTTPException(status_code=403, detail="Admin privileges required")

        return await orchestrator.optimize_system()

    @app.get("/health")
    async def health_check():
        """Health check endpoint (no auth required)"""
        return {
            "status": "healthy",
            "version": "9.0.0",
            "timestamp": orchestrator.start_time.isoformat()
        }

    @app.post("/api/auth/login")
    async def login(request: Dict[str, str]):
        """User login"""
        username = request.get("username")
        password = request.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")

        token = orchestrator.security_manager.authenticate(username, password)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return {"token": token}

    @app.post("/api/auth/logout")
    async def logout(request: Dict[str, str]):
        """User logout"""
        token = request.get("token")
        if token:
            orchestrator.security_manager.revoke_token(token)
        return {"message": "Logged out successfully"}

    @app.get("/api/security/health")
    async def security_health():
        """Security system health check"""
        return {
            "status": "healthy",
            "jwt_configured": orchestrator.config.get("jwt_secret_set", False),
            "security_enabled": orchestrator.config.get("security_enabled", True)
        }

    logger.info("✅ API routes configured")
