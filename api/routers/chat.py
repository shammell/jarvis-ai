"""
Chat API router - conversation endpoints
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from fastapi.responses import StreamingResponse
from api.auth import AuthUser, CurrentUser
from api.db.supabase_client import get_supabase
from api.repositories.chat_repository import ChatRepository
from api.services.chat_service import ChatService
from api.rate_limit import InMemoryRateLimiter, RedisRateLimiter
from api.schemas.chat import (
    ChatCreate,
    ChatResponse,
    ChatList,
    MessageCreate,
    MessageResponse,
    MessageList,
    SendMessageResponse,
    StreamEvent
)
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/chats", tags=["chats"])

# Global orchestrator reference (will be set from main.py)
_orchestrator = None
# Redis-backed distributed limiters; fall back to allow-all if Redis is down
_send_limiter = RedisRateLimiter(max_requests=20, window_seconds=60)
_stream_limiter = RedisRateLimiter(max_requests=10, window_seconds=60)

def set_orchestrator(orchestrator):
    """Set global orchestrator instance"""
    global _orchestrator
    _orchestrator = orchestrator

def get_chat_service(user: AuthUser = CurrentUser) -> ChatService:
    """Dependency for CRUD endpoints (does not require orchestrator)"""
    supabase = get_supabase_for_user(user.token)  # Use user-specific client for RLS
    repository = ChatRepository(supabase)
    return ChatService(repository, _orchestrator)


def get_chat_service_with_orchestrator(user: AuthUser = CurrentUser) -> ChatService:
    """Dependency for send/stream endpoints (requires orchestrator)"""
    if _orchestrator is None:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Orchestrator not initialized")
    supabase = get_supabase_for_user(user.token)  # Use user-specific client for RLS
    repository = ChatRepository(supabase)
    return ChatService(repository, _orchestrator)

@router.post("", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    chat_data: ChatCreate,
    user: AuthUser = CurrentUser,
    service: ChatService = Depends(get_chat_service)
):
    """Create new chat thread"""
    chat = await service.create_chat(user.user_id, chat_data.title)
    return chat

@router.get("", response_model=ChatList)
async def list_chats(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: AuthUser = CurrentUser,
    service: ChatService = Depends(get_chat_service)
):
    """List user's chat threads"""
    chats, total = await service.get_user_chats(user.user_id, limit, offset)
    return {"chats": chats, "total": total}

@router.get("/{chat_id}/messages", response_model=MessageList)
async def get_messages(
    chat_id: str,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: AuthUser = CurrentUser,
    service: ChatService = Depends(get_chat_service)
):
    """Get messages for a chat"""
    messages, total, has_more = await service.get_chat_messages(
        chat_id, user.user_id, limit, offset
    )
    return {"messages": messages, "total": total, "has_more": has_more}

@router.post("/{chat_id}/messages", response_model=SendMessageResponse)
async def send_message(
    chat_id: str,
    message_data: MessageCreate,
    request: Request,
    user: AuthUser = CurrentUser,
    service: ChatService = Depends(get_chat_service_with_orchestrator)
):
    """Send message and get JARVIS response"""
    client_ip = request.client.host if request.client else "unknown"
    limit_key = f"send:{user.user_id}:{client_ip}"
    if not await _send_limiter.allow(limit_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    try:
        result = await service.send_message(
            chat_id=chat_id,
            user_id=user.user_id,
            content=message_data.content
        )
        return result
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found or access denied")
    except Exception:
        logger.exception("Error sending message")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

@router.post("/{chat_id}/stream")
async def stream_message(
    chat_id: str,
    message_data: MessageCreate,
    request: Request,
    user: AuthUser = CurrentUser,
    service: ChatService = Depends(get_chat_service_with_orchestrator)
):
    """Stream JARVIS response (SSE)"""
    client_ip = request.client.host if request.client else "unknown"
    limit_key = f"stream:{user.user_id}:{client_ip}"
    if not await _stream_limiter.allow(limit_key):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    async def event_generator():
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'start'})}\n\n"

            # Get response via orchestrator's streaming capability
            async for token_chunk in _orchestrator.stream_response(
                message=message_data.content,
                user_id=user.user_id
            ):
                if token_chunk.get("type") == "token":
                    # Stream individual tokens/chunks as they become available
                    yield f"data: {json.dumps({'type': 'chunk', 'content': token_chunk['content']})}\n\n"
                elif token_chunk.get("type") == "complete":
                    # Send end event with metadata when complete
                    yield f"data: {json.dumps({'type': 'end', 'metadata': token_chunk.get('metadata')})}\n\n"
                    break

        except Exception as e:
            logger.exception("Stream error")
            yield f"data: {json.dumps({'type': 'error', 'content': 'Failed to process stream'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: str,
    user: AuthUser = CurrentUser,
    service: ChatService = Depends(get_chat_service)
):
    """Archive (soft delete) chat"""
    success = await service.archive_chat(chat_id, user.user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return None
