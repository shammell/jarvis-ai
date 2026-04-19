# ================================================================
# JARVIS - Task Chain (Simple Version)
# ================================================================
# Simple multi-step command executor with retry/fallback
# Ported from Desktop jarvis for basic task chaining
# ================================================================

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional


@dataclass
class TaskStep:
    """Simple task step with retry tracking."""
    raw: str
    attempts: int = 0


class TaskChainExecutor:
    """Simple multi-step command executor with retry/fallback."""

    def __init__(self, executor: Callable[[str], Awaitable[str]], max_retries: int = 1):
        self._executor = executor
        self._max_retries = max_retries

    def parse(self, text: str) -> list[TaskStep]:
        """Parse command text into task steps."""
        parts = [p.strip() for p in re.split(r"\bthen\b|\band\b|,|phir|uske baad", text, flags=re.IGNORECASE) if p.strip()]
        return [TaskStep(raw=p) for p in parts]

    async def execute_chain(self, text: str) -> str:
        """Execute a chain of tasks."""
        steps = self.parse(text)
        if len(steps) <= 1:
            return await self._executor(text)

        outputs: list[str] = []
        for index, step in enumerate(steps, start=1):
            last_error: Optional[str] = None
            while step.attempts <= self._max_retries:
                try:
                    step.attempts += 1
                    result = await self._executor(step.raw)
                    outputs.append(f"Step {index}: {result}")
                    last_error = None
                    break
                except Exception as e:  # pragma: no cover - defensive runtime path
                    last_error = str(e)
            if last_error:
                outputs.append(f"Step {index} failed: {last_error[:80]}")
                break
        return " | ".join(outputs)
