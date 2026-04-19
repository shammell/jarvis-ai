"""Voice-first JARVIS runtime entrypoint.

Boots VoiceBridge + AudioManager and keeps the hands-free loop alive.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Optional

from voice.voice_bridge import VoiceBridge
from voice.audio_manager import AudioManager

logger = logging.getLogger(__name__)


class VoiceJarvisRuntime:
    def __init__(self):
        self.bridge: Optional[VoiceBridge] = None
        self.audio: Optional[AudioManager] = None
        self.running = False

    async def start(self) -> None:
        if self.running:
            return

        self.bridge = VoiceBridge()
        await self.bridge.initialize()

        async def on_command(text: str) -> str:
            if not self.bridge:
                return "Voice bridge unavailable"
            return await self.bridge.handle(text)

        self.audio = AudioManager(on_command=on_command)
        await self.audio.start()
        self.running = True
        logger.info("VoiceJarvisRuntime started")

    async def stop(self) -> None:
        if not self.running:
            return
        if self.audio:
            await self.audio.stop()
        if self.bridge:
            await self.bridge.shutdown()
        self.running = False
        logger.info("VoiceJarvisRuntime stopped")

    async def run_forever(self) -> None:
        await self.start()
        try:
            while self.running:
                await asyncio.sleep(1)
        finally:
            await self.stop()


async def main() -> None:
    runtime = VoiceJarvisRuntime()
    await runtime.run_forever()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
