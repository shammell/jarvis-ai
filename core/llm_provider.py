import os
import threading
import logging
import asyncio
from typing import List, Dict, Any, Optional
from core.llm_exceptions import LLMClientUnavailableError
from core.resilience_patterns import retry_policy, circuit_breaker

logger = logging.getLogger(__name__)

class LLMProvider:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.client = None
        self.fallback_manager = None
        self._init_client()

    def _init_client(self):
        # Initialize HybridLLMManager for automatic fallback
        try:
            from core.local_llm_fallback import HybridLLMManager
            self.fallback_manager = HybridLLMManager()
            self.client = self.fallback_manager.groq_client
            logger.info("✅ LLMProvider initialized with HybridLLMManager")
        except (ImportError, Exception) as e:
            logger.warning(f"⚠️ HybridLLMManager initialization failed: {e}. Falling back to basic Groq.")
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                try:
                    from groq import Groq
                    self.client = Groq(api_key=api_key)
                except ImportError:
                    self.client = None
            else:
                self.client = None

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    @retry_policy(max_attempts=3)
    @circuit_breaker(name="llm_provider", failure_threshold=5, recovery_timeout=60)
    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        model: str = "llama-3.3-70b-versatile",
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text with automatic fallback and resilience"""
        if self.fallback_manager:
            # HybridLLMManager handles its own Groq -> Local fallback
            return await asyncio.to_thread(
                self.fallback_manager.generate,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                **kwargs
            )

        if not self.client:
            raise LLMClientUnavailableError("LLM client not initialized")

        # Fallback to basic Groq call if HybridLLMManager is unavailable
        response = await asyncio.to_thread(
            self.client.chat.completions.create,
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        return {
            "text": response.choices[0].message.content,
            "source": "groq",
            "model": model
        }

    def get_client(self):
        if not self.client:
            raise LLMClientUnavailableError(
                "LLM client not initialized. Set GROQ_API_KEY in .env"
            )
        return self.client
