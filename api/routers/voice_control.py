"""Voice control API router for hands-free orchestration."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

_voice_runtime = None
_orchestrator = None


def set_voice_runtime(runtime: Any) -> None:
    global _voice_runtime
    _voice_runtime = runtime


def set_orchestrator(orchestrator: Any) -> None:
    global _orchestrator
    _orchestrator = orchestrator


class VoiceCommandRequest(BaseModel):
    text: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@router.get("/status")
async def voice_status() -> Dict[str, Any]:
    runtime = _voice_runtime
    if not runtime:
        return {"voice_runtime": "not_configured", "running": False}
    return {"voice_runtime": "configured", "running": bool(getattr(runtime, "running", False))}


@router.post("/command")
async def voice_command(req: VoiceCommandRequest) -> Dict[str, Any]:
    runtime = _voice_runtime
    if runtime and getattr(runtime, "bridge", None):
        reply = await runtime.bridge.handle(req.text)
        return {"success": True, "reply": reply}

    if _orchestrator:
        result = await _orchestrator.process_message(req.text, req.context, req.user_id)
        return {"success": True, "reply": result.get("text", ""), "metadata": result.get("metadata", {})}

    raise HTTPException(status_code=503, detail="Voice service unavailable")
