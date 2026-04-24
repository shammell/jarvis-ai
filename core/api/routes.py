# ==========================================================
# JARVIS v9.0 - API Routes
# FastAPI routes extracted from main.py
# ==========================================================

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import datetime
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

        context = request.context or {}
        team_name = context.get("team_name") or "standard_workflow"

        result = await orchestrator.autonomy_system.execute_with_agent_team(
            task_description=request.goal,
            team_name=team_name,
            context={**context, "requested_agents": request.agents}
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

        tokens = orchestrator.security_manager.authenticate_user(username, password)
        if not tokens:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return tokens

    @app.post("/api/auth/logout")
    async def logout(request: Dict[str, str]):
        """User logout"""
        token = request.get("token")
        if token:
            payload = orchestrator.security_manager.validate_token(token)
            if not payload:
                raise HTTPException(status_code=401, detail="Invalid token")
            orchestrator.security_manager.logout_user(
                user_id=payload.get("user_id"),
                session_id=payload.get("session_id")
            )
        return {"message": "Logged out successfully"}

    @app.get("/api/security/health")
    async def security_health():
        """Security system health check"""
        return {
            "status": "healthy",
            "jwt_configured": orchestrator.config.get("jwt_secret_set", False),
            "security_enabled": orchestrator.config.get("security_enabled", True)
        }

    # Web contract stubs (Phase 5) - /api/v1/chats/*
    @app.get("/api/v1/chats")
    async def list_chats_v1(token: str = Header(None)):
        """List chats (stub)"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        return {"chats": [], "total": 0}

    @app.post("/api/v1/chats")
    async def create_chat_v1(request: Dict[str, str], token: str = Header(None)):
        """Create chat (stub)"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        return {"id": "stub-chat-id", "user_id": "stub", "title": request.get("title"), "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "archived": False}

    @app.get("/api/v1/chats/{chat_id}/messages")
    async def get_messages_v1(chat_id: str, token: str = Header(None), limit: int = 50, offset: int = 0):
        """Get chat messages (stub)"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        return {"messages": [], "total": 0, "has_more": False}

    @app.post("/api/v1/chats/{chat_id}/messages")
    async def send_message_v1(chat_id: str, request: Dict[str, str], token: str = Header(None)):
        """Send message (stub)"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        return {
            "user_message": {"id": "u1", "chat_id": chat_id, "user_id": "stub", "role": "user", "content": request.get("content", ""), "created_at": datetime.now().isoformat()},
            "assistant_message": {"id": "a1", "chat_id": chat_id, "user_id": "system", "role": "assistant", "content": "Stub response", "created_at": datetime.now().isoformat()}
        }

    @app.delete("/api/v1/chats/{chat_id}")
    async def delete_chat_v1(chat_id: str, token: str = Header(None)):
        """Delete chat (stub)"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        return {"deleted": True}

    @app.post("/api/v1/chats/{chat_id}/stream")
    async def stream_message_v1(chat_id: str, request: Dict[str, str], token: str = Header(None)):
        """Stream message (stub - returns plain response)"""
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        return {"stream_stub": True, "chat_id": chat_id}

    logger.info("✅ API routes configured")
