# ================================================================
# JARVIS - Voice Bridge v1.0 (Ported)
# ================================================================
# Connects the voice system to the existing JARVIS orchestrator
# Voice commands -> Orchestrator -> Response -> TTS
# ================================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional, Callable

import logging

# Set up logging with UTF-8 support for Windows
if sys.platform == "win32":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_bridge.log", encoding="utf-8")
        ]
    )
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_bridge.log", encoding="utf-8")
        ]
    )

logger = logging.getLogger(__name__)

import re
from voice.prompt_generator import PromptGenerator, detect_intent, IntentType

try:
    from voice.autonomy_runtime import AutonomyRuntime
    AUTONOMY_AVAILABLE = True
except ImportError:
    AUTONOMY_AVAILABLE = False
    logger.warning("AutonomyRuntime not available - running in basic mode")

# Complex goal pattern matching
_COMPLEX_GOAL_PATTERN = re.compile(r"(\band\b|\bthen\b|,|phir|uske baad|report|draft|save karo|schedule)", re.IGNORECASE)


# ══ VOICE BRIDGE ═════════════════════════════════════════════════

class VoiceBridge:
    """
    Bridge between voice system and JARVIS orchestrator.

    Takes transcribed text, routes it through intent detection,
    and either handles locally (open app, system control) or
    sends to JARVIS orchestrator for AI processing.

    Usage:
        bridge = VoiceBridge()
        response = await bridge.handle("calculator banao")
    """

    def __init__(self):
        self._prompt_gen: Optional[PromptGenerator] = None
        self._orchestrator = None
        self._llm_func = None
        self._autonomy: Optional[AutonomyRuntime] = None
        if AUTONOMY_AVAILABLE:
            self._autonomy = AutonomyRuntime()

    async def initialize(self) -> None:
        """Initialize bridge with orchestrator connection."""
        # Try to import JARVIS orchestrator
        try:
            # Add parent directory to path if not already there
            current_dir = Path(__file__).parent
            jarvis_path = str(current_dir.parent)
            if jarvis_path not in sys.path:
                sys.path.insert(0, jarvis_path)

            from core.local_llm_fallback import HybridLLMManager
            self._orchestrator = HybridLLMManager()
            self._llm_func = self._wrap_llm(self._orchestrator)
            logger.info("Voice Bridge: Connected to JARVIS Hybrid LLM manager")
        except ImportError as e:
            logger.warning(f"Voice Bridge: JARVIS LLM not available ({e})")
            logger.info("Voice Bridge: Running in standalone mode")

            # Try Groq directly as fallback
            try:
                from groq import AsyncGroq
                api_key = os.getenv("GROQ_API_KEY")
                if api_key:
                    # Clear proxy env vars that crash Groq SDK
                    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
                        os.environ.pop(k, None)
                    client = AsyncGroq(api_key=api_key)
                    self._llm_func = self._wrap_groq(client)
                    logger.info("Voice Bridge: Using Groq LLM directly")
            except ImportError:
                pass

        self._prompt_gen = PromptGenerator(
            llm_callable=self._llm_func,
        )

        if self._autonomy:
            await self._autonomy.start()

    async def handle(self, text: str) -> str:
        """Handle a voice command and return response text."""
        if not self._prompt_gen:
            await self.initialize()

        if self._looks_like_high_level_goal(text):
            return await self.execute_goal(text)

        return await self._prompt_gen.process(text)

    async def execute_goal(self, text: str, context: Optional[dict[str, Any]] = None) -> str:
        """Execute a high-level goal."""
        if self._autonomy:
            return await self._autonomy.execute_goal(text, context)
        logger.warning("AutonomyRuntime not available - cannot execute high-level goals")
        return f"Goal received: {text}. Use autonomy runtime for high-level goal execution."

    def get_runtime_status(self) -> dict[str, Any]:
        """Get runtime status."""
        if self._autonomy:
            return self._autonomy.get_status()
        return {"autonomy": False, "status": "unavailable"}

    @staticmethod
    def _looks_like_high_level_goal(text: str) -> bool:
        """Check if text looks like a high-level goal."""
        return bool(_COMPLEX_GOAL_PATTERN.search(text)) and len(text.split()) >= 4

    async def shutdown(self) -> None:
        """Shutdown the voice bridge."""
        if self._autonomy:
            await self._autonomy.stop()

    @staticmethod
    def _wrap_llm(llm_manager: Any) -> Callable[[str], str]:
        """Wrap JARVIS LLM manager into a simple async callable."""
        async def call_llm(prompt: str) -> str:
            # HybridLLMManager uses generate_response or similar
            if hasattr(llm_manager, 'generate_response'):
                result = await llm_manager.generate_response(prompt)
            else:
                # Fallback for other manager types
                result = await llm_manager.generate(
                    prompt=prompt,
                    task_type="general",
                )
            return result if isinstance(result, str) else str(result)
        return call_llm

    @staticmethod
    def _wrap_groq(client: Any) -> Callable[[str], str]:
        """Wrap Groq client into a simple async callable."""
        async def call_groq(prompt: str) -> str:
            response = await client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        return call_groq
