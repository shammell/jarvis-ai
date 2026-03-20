"""
Database access layer for chats and messages with proper RLS support
"""
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from supabase import Client

class ChatRepository:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    async def _execute(self, builder):
        """Run blocking Supabase execute() off the event loop."""
        return await asyncio.to_thread(builder.execute)

    # Chat operations
    async def create_chat(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create new chat thread"""
        chat_data = {
            "id": str(uuid4()),
            "user_id": user_id,
            "title": title or "New Chat",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "archived": False
        }

        result = await self._execute(self.supabase.table("chats").insert(chat_data))
        return result.data[0] if result.data else None

    async def get_user_chats(self, user_id: str, limit: int = 50, offset: int = 0) -> tuple[List[Dict[str, Any]], int]:
        """Get user's chat threads with pagination"""
        # Get chats - RLS should enforce that user can only see their own chats
        query = (
            self.supabase.table("chats")
            .select("*")
            .eq("user_id", user_id)
            .eq("archived", False)
            .order("updated_at", desc=True)
            .range(offset, offset + limit - 1)
        )

        result = await self._execute(query)
        chats = result.data or []

        # Get total count - RLS should enforce that user can only count their own chats
        count_result = await self._execute(
            self.supabase.table("chats")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .eq("archived", False)
        )

        total = count_result.count or 0
        return chats, total

    async def get_chat(self, chat_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get single chat by ID (with ownership check)"""
        # RLS should enforce that user can only access their own chats
        result = await self._execute(
            self.supabase.table("chats")
            .select("*")
            .eq("id", chat_id)
            .eq("user_id", user_id)
        )

        return result.data[0] if result.data else None

    async def update_chat_timestamp(self, chat_id: str, user_id: str) -> None:
        """Update chat's updated_at timestamp"""
        # RLS should enforce that user can only update their own chats
        await self._execute(
            self.supabase.table("chats")
            .update({"updated_at": datetime.utcnow().isoformat()})
            .eq("id", chat_id)
            .eq("user_id", user_id)
        )

    async def archive_chat(self, chat_id: str, user_id: str) -> bool:
        """Archive (soft delete) a chat"""
        # RLS should enforce that user can only archive their own chats
        result = await self._execute(
            self.supabase.table("chats")
            .update({"archived": True})
            .eq("id", chat_id)
            .eq("user_id", user_id)
        )

        return len(result.data) > 0 if result.data else False

    # Message operations
    async def create_message(
        self,
        chat_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new message in chat"""
        message_data = {
            "id": str(uuid4()),
            "chat_id": chat_id,
            "user_id": user_id,
            "role": role,
            "content": content,
            "metadata": metadata or {},
            "created_at": datetime.utcnow().isoformat()
        }

        result = await self._execute(self.supabase.table("messages").insert(message_data))
        return result.data[0] if result.data else None

    async def get_chat_messages(
        self,
        chat_id: str,
        user_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Dict[str, Any]], int, bool]:
        """Get messages for a chat with pagination"""
        # Verify chat ownership - RLS should enforce access control
        chat = await self.get_chat(chat_id, user_id)
        if not chat:
            return [], 0, False

        # Get messages - RLS should enforce that user can only see messages from their chats
        query = (
            self.supabase.table("messages")
            .select("*")
            .eq("chat_id", chat_id)
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .range(offset, offset + limit - 1)
        )

        result = await self._execute(query)
        messages = result.data or []

        # Get total count - RLS should enforce that user can only count messages from their chats
        count_result = await self._execute(
            self.supabase.table("messages")
            .select("id", count="exact")
            .eq("chat_id", chat_id)
            .eq("user_id", user_id)
        )

        total = count_result.count or 0
        has_more = (offset + limit) < total

        return messages, total, has_more
