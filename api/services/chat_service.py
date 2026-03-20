"""
Chat service - orchestrates chat operations and JARVIS integration with proper RLS support
"""
import logging
from typing import Dict, Any, Optional
from api.repositories.chat_repository import ChatRepository

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, repository: ChatRepository, orchestrator):
        self.repository = repository
        self.orchestrator = orchestrator

    async def send_message(
        self,
        chat_id: str,
        user_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Send user message and get JARVIS response
        Returns both user and assistant messages
        """
        # Verify chat ownership
        chat = await self.repository.get_chat(chat_id, user_id)
        if not chat:
            raise ValueError("Chat not found or access denied")

        # 1. Persist user message
        user_message = await self.repository.create_message(
            chat_id=chat_id,
            user_id=user_id,
            role="user",
            content=content
        )

        # 2. Call JARVIS orchestrator (reuse existing process_message)
        try:
            jarvis_response = await self.orchestrator.process_message(content)

            # Extract response data from orchestrator contract: {"text": ..., "metadata": {...}}
            assistant_content = jarvis_response.get("text", "")
            response_metadata = jarvis_response.get("metadata", {}) or {}
            metadata = {
                "latency_ms": response_metadata.get("latency_ms"),
                "source": response_metadata.get("source"),
                "complex_reasoning": response_metadata.get("complex_reasoning", False),
                "request_id": response_metadata.get("request_id")
            }

            # 3. Persist assistant message
            assistant_message = await self.repository.create_message(
                chat_id=chat_id,
                user_id=user_id,
                role="assistant",
                content=assistant_content or "I couldn't generate a response. Please try again.",
                metadata=metadata
            )

            # 4. Update chat timestamp
            await self.repository.update_chat_timestamp(chat_id, user_id)

            return {
                "user_message": user_message,
                "assistant_message": assistant_message
            }

        except Exception:
            logger.exception("Error processing message")
            # Store error message
            error_message = await self.repository.create_message(
                chat_id=chat_id,
                user_id=user_id,
                role="assistant",
                content="I encountered an error processing your request. Please try again.",
                metadata={"error": "internal_error"}
            )

            return {
                "user_message": user_message,
                "assistant_message": error_message
            }

    async def create_chat(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create new chat thread"""
        return await self.repository.create_chat(user_id, title)

    async def get_user_chats(self, user_id: str, limit: int = 50, offset: int = 0):
        """Get user's chat list"""
        return await self.repository.get_user_chats(user_id, limit, offset)

    async def get_chat_messages(self, chat_id: str, user_id: str, limit: int = 50, offset: int = 0):
        """Get chat messages"""
        return await self.repository.get_chat_messages(chat_id, user_id, limit, offset)

    async def archive_chat(self, chat_id: str, user_id: str) -> bool:
        """Archive chat"""
        return await self.repository.archive_chat(chat_id, user_id)
