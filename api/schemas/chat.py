"""
Pydantic schemas for chat API
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

# Chat schemas
class ChatCreate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)

class ChatResponse(BaseModel):
    id: str
    user_id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    archived: bool = False

class ChatList(BaseModel):
    chats: List[ChatResponse]
    total: int

# Message schemas
class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)

class MessageResponse(BaseModel):
    id: str
    chat_id: str
    user_id: str
    role: str  # 'user' | 'assistant' | 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

class MessageList(BaseModel):
    messages: List[MessageResponse]
    total: int
    has_more: bool

# Stream event schemas
class StreamEvent(BaseModel):
    type: str  # 'start' | 'chunk' | 'end' | 'error'
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

# Send message response
class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
