# ================================================================
# JARVIS - Audio Manager v1.1 (Ported)
# ================================================================
# Central controller: state machine that wires
# wake detection -> recording -> STT -> orchestrator -> TTS
# Now with: beep sounds + continuous listening mode
# ================================================================

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import logging

# Set up logging with UTF-8 support for Windows
if sys.platform == "win32":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_audio.log", encoding="utf-8")
        ]
    )
    # Ensure UTF-8 encoding for console
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_audio.log", encoding="utf-8")
        ]
    )

logger = logging.getLogger(__name__)

from voice.wake_detector import WakeDetector, WakeConfig
from voice.speech_to_text import SpeechToText, STTConfig
from voice.text_to_speech import TextToSpeech, TTSConfig

# Windows beep support
if sys.platform == "win32":
    import winsound
    WINSOUND_AVAILABLE = True
else:
    WINSOUND_AVAILABLE = False


# ══ BEEP SOUNDS ═════════════════════════════════════════════════

class BeepType(Enum):
    """Different beep sounds for different events."""
    ACTIVATION = "activation"      # Wake detected - ready to listen
    SUCCESS = "success"            # Command completed successfully
    ERROR = "error"                # Something went wrong
    LISTENING = "listening"        # Start of continuous mode
    DEACTIVATE = "deactivate"      # Continuous mode off


async def play_beep(beep_type: BeepType) -> None:
    """Play a system beep sound (Windows only)."""
    if not WINSOUND_AVAILABLE:
        logger.debug(f"Beep skipped (not Windows): {beep_type.value}")
        return

    loop = asyncio.get_event_loop()

    try:
        if beep_type == BeepType.ACTIVATION:
            # Rising tone - "I'm listening"
            await loop.run_in_executor(None, lambda: winsound.Beep(800, 150))
            await loop.run_in_executor(None, lambda: winsound.Beep(1200, 150))
        elif beep_type == BeepType.SUCCESS:
            # Pleasant ding - "Done!"
            await loop.run_in_executor(None, lambda: winsound.Beep(1000, 200))
        elif beep_type == BeepType.ERROR:
            # Low buzz - "Oops"
            await loop.run_in_executor(None, lambda: winsound.Beep(300, 300))
        elif beep_type == BeepType.LISTENING:
            # Double beep - "Continuous mode on"
            await loop.run_in_executor(None, lambda: winsound.Beep(600, 100))
            await asyncio.sleep(0.05)
            await loop.run_in_executor(None, lambda: winsound.Beep(900, 100))
            await asyncio.sleep(0.05)
            await loop.run_in_executor(None, lambda: winsound.Beep(1200, 100))
        elif beep_type == BeepType.DEACTIVATE:
            # Falling tone - "Going idle"
            await loop.run_in_executor(None, lambda: winsound.Beep(1200, 100))
            await loop.run_in_executor(None, lambda: winsound.Beep(800, 100))
            await loop.run_in_executor(None, lambda: winsound.Beep(400, 150))
    except Exception as e:
        logger.debug(f"Beep failed: {e}")


# ══ STATES ═══════════════════════════════════════════════════════

class AudioState(Enum):
    IDLE = "idle"                        # Waiting for wake trigger
    LISTENING = "listening"              # Recording user's command
    PROCESSING = "processing"            # Transcribing + AI thinking
    SPEAKING = "speaking"                # TTS output
    PAUSED = "paused"                    # User said "ruko"
    CONTINUOUS = "continuous"            # Continuous listening mode (no wake needed)


# ══ CONFIG ═══════════════════════════════════════════════════════

@dataclass(frozen=True)
class AudioManagerConfig:
    """Immutable audio manager configuration."""
    activation_sound: bool = True        # play beep on wake
    beep_enabled: bool = True            # enable all beep sounds
    confirmation_phrases: tuple = (
        "Yes sir, I'm listening",
        "Ready sir",
        "Go ahead sir",
        "Listening",
    )
    error_phrase: str = "Sorry sir, I couldn't understand that. Please try again."
    processing_phrase: str = "Processing sir..."
    continuous_mode_timeout: float = 30.0  # seconds of silence before exiting continuous mode


# ══ AUDIO MANAGER ════════════════════════════════════════════════

class AudioManager:
    """
    Central audio controller with state machine.

    Flow:
        IDLE -> (clap/wake) -> LISTENING -> (silence) -> PROCESSING -> SPEAKING -> IDLE

    Usage:
        manager = AudioManager(on_command=handle_command)
        await manager.start()
    """

    def __init__(
        self,
        on_command: Optional[Callable] = None,
        config: Optional[AudioManagerConfig] = None,
        wake_config: Optional[WakeConfig] = None,
        stt_config: Optional[STTConfig] = None,
        tts_config: Optional[TTSConfig] = None,
    ):
        self._config = config or AudioManagerConfig()
        self._on_command = on_command
        self._state = AudioState.IDLE
        self._running = False
        self._command_count = 0
        self._start_time = time.time()

        # Sub-systems
        self._wake = WakeDetector(
            on_wake=self._on_wake_trigger,
            config=wake_config,
        )
        self._stt = SpeechToText(config=stt_config)
        self._tts = TextToSpeech(config=tts_config)

        # Confirmation phrase rotation
        self._phrase_idx = 0

        # Continuous mode state
        self._continuous_mode = False

    async def start(self) -> None:
        """Start the audio manager."""
        if self._running:
            return

        self._running = True
        self._state = AudioState.IDLE
        self._start_time = time.time()

        await self._wake.start()
        logger.info("Audio Manager started - state: IDLE")
        if self._config.beep_enabled:
            await play_beep(BeepType.LISTENING)

    async def stop(self) -> None:
        """Stop everything."""
        self._running = False
        await self._wake.stop()
        await self._tts.stop()
        self._state = AudioState.IDLE
        logger.info("Audio Manager stopped")

    async def _on_wake_trigger(self, method: str) -> None:
        """Called when wake trigger fires (clap or wake word)."""
        if self._state != AudioState.IDLE:
            logger.debug(f"Wake ignored - state is {self._state.value}")
            return

        logger.info(f"Wake trigger: {method}")

        # Stop wake detection while we handle command
        await self._wake.stop()

        # Confirm activation
        phrase = self._config.confirmation_phrases[
            self._phrase_idx % len(self._config.confirmation_phrases)
        ]
        self._phrase_idx += 1

        if self._config.beep_enabled:
            await play_beep(BeepType.ACTIVATION)

        self._state = AudioState.SPEAKING
        await self._tts.speak(phrase)

        # Listen for command
        self._state = AudioState.LISTENING
        text = await self._stt.listen_and_transcribe()

        if text:
            self._command_count += 1
            logger.info(f"Command #{self._command_count}: '{text}'")

            # Check for control commands
            text_lower = text.lower().strip()

            if any(w in text_lower for w in ("continuous mode on", "continuous on", "always listening", "lagataar suno")):
                self._continuous_mode = True
                self._state = AudioState.CONTINUOUS
                if self._config.beep_enabled:
                    await play_beep(BeepType.LISTENING)
                await self._tts.speak("Continuous mode on sir. Ab bina clap ke sun raha hoon.")
                await self._wake.start()
                return

            if any(w in text_lower for w in ("continuous mode off", "continuous off", "normal mode", "lagataar band")):
                self._continuous_mode = False
                self._state = AudioState.IDLE
                if self._config.beep_enabled:
                    await play_beep(BeepType.DEACTIVATE)
                await self._tts.speak("Continuous mode off sir.")
                await self._wake.start()
                return

            if any(w in text_lower for w in ("ruko", "pause", "wait")):
                self._state = AudioState.PAUSED
                await self._tts.speak("Paused sir. Clap twice to resume.")
                await self._wake.start()
                return

            if any(w in text_lower for w in ("band karo", "stop", "quit", "exit", "shutdown")):
                await self._tts.speak("Shutting down sir. Goodbye.")
                await self.stop()
                return

            # Process command
            self._state = AudioState.PROCESSING

            if self._on_command:
                try:
                    if asyncio.iscoroutinefunction(self._on_command):
                        response = await self._on_command(text)
                    else:
                        response = self._on_command(text)

                    # Speak response
                    if response:
                        self._state = AudioState.SPEAKING
                        await self._tts.speak(str(response))
                        if self._config.beep_enabled:
                            await play_beep(BeepType.SUCCESS)
                except Exception as e:
                    logger.error(f"Command handler error: {e}")
                    self._state = AudioState.SPEAKING
                    await self._tts.speak(f"Sorry sir, error occurred: {str(e)[:50]}")
                    if self._config.beep_enabled:
                        await play_beep(BeepType.ERROR)
            else:
                # No command handler - echo
                self._state = AudioState.SPEAKING
                await self._tts.speak(f"I heard: {text}")
        else:
            self._state = AudioState.SPEAKING
            await self._tts.speak(self._config.error_phrase)

        # Return to idle / continuous
        self._state = AudioState.IDLE
        await self._wake.start()

        if self._continuous_mode and self._running:
            asyncio.create_task(self._continuous_listen_loop())

    async def _continuous_listen_loop(self) -> None:
        """In continuous mode, keep listening without requiring wake trigger."""
        if not self._running or not self._continuous_mode:
            return
        if self._state not in (AudioState.IDLE, AudioState.CONTINUOUS):
            return

        self._state = AudioState.CONTINUOUS
        await self._wake.stop()

        try:
            text = await self._stt.listen_and_transcribe()
            if text:
                self._command_count += 1
                logger.info(f"[Continuous] Command #{self._command_count}: '{text}'")
                if self._on_command:
                    response = await self._on_command(text) if asyncio.iscoroutinefunction(self._on_command) else self._on_command(text)
                    if response:
                        self._state = AudioState.SPEAKING
                        await self._tts.speak(str(response))
                        if self._config.beep_enabled:
                            await play_beep(BeepType.SUCCESS)
        except Exception as e:
            logger.error(f"Continuous mode error: {e}")
            if self._config.beep_enabled:
                await play_beep(BeepType.ERROR)
        finally:
            self._state = AudioState.IDLE
            await self._wake.start()

    @property
    def state(self) -> AudioState:
        return self._state

    @property
    def stats(self) -> dict:
        return {
            "state": self._state.value,
            "commands_processed": self._command_count,
            "uptime_seconds": int(time.time() - self._start_time),
            "running": self._running,
        }


# ══ STANDALONE TEST ══════════════════════════════════════════════

async def _test():
    """Test audio manager standalone (echo mode)."""
    print("\n" + "=" * 50)
    print("  JARVIS Audio Manager - Echo Test")
    print("  Clap twice or say 'Hey JARVIS'")
    print("  Then speak a command - it will echo back")
    print("  Say 'band karo' to stop")
    print("=" * 50 + "\n")

    async def echo_handler(text: str) -> str:
        return f"You said: {text}"

    manager = AudioManager(on_command=echo_handler)
    await manager.start()

    try:
        while manager._running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await manager.stop()

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(_test())
