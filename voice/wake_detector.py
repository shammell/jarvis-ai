# ================================================================
# JARVIS - Wake Detector v1.0 (Ported)
# ================================================================
# Double-clap detection + "Hey JARVIS" wake word
# Uses sounddevice for mic capture, numpy for signal analysis
# Groq Whisper for wake word transcription
# ================================================================

from __future__ import annotations

import asyncio
import io
import json
import os
import struct
import sys
import time
import wave
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import logging

# Set up logging with UTF-8 support for Windows
if sys.platform == "win32":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_wake.log", encoding="utf-8")
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
            logging.FileHandler("jarvis_wake.log", encoding="utf-8")
        ]
    )

logger = logging.getLogger(__name__)

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not installed - wake word detection disabled")


# ══ CONFIG ═══════════════════════════════════════════════════════

@dataclass(frozen=True)
class WakeConfig:
    """Immutable wake detection configuration."""
    # Audio settings
    sample_rate: int = 16000
    channels: int = 1
    block_size: int = 1024        # samples per callback (~64ms at 16kHz)

    # Clap detection
    clap_threshold: float = 0.4   # amplitude threshold (0.0-1.0)
    clap_min_duration: float = 0.01   # min clap length (seconds)
    clap_max_duration: float = 0.15   # max clap length (seconds)
    double_clap_window: float = 1.0   # max time between 2 claps
    clap_cooldown: float = 2.0        # cooldown after wake trigger

    # Wake word detection
    wake_word_enabled: bool = True
    wake_words: tuple = ("jarvis", "hey jarvis", "hey jarves", "jarves")
    speech_energy_threshold: float = 0.02  # min energy to try transcription
    wake_word_buffer_seconds: float = 3.0  # rolling buffer size
    wake_word_check_interval: float = 2.0  # how often to check buffer

    # Groq API
    groq_model: str = "whisper-large-v3"


# ══ WAKE DETECTOR ════════════════════════════════════════════════

class WakeDetector:
    """
    Detects wake triggers:
    1. Double-clap (amplitude spike analysis)
    2. Wake word "Hey JARVIS" (Groq Whisper transcription)

    Usage:
        detector = WakeDetector(on_wake=my_callback)
        await detector.start()
        # ... later
        await detector.stop()
    """

    def __init__(
        self,
        on_wake: Optional[Callable] = None,
        config: Optional[WakeConfig] = None,
    ):
        self._config = config or WakeConfig()
        self._on_wake = on_wake
        self._running = False
        self._stream: Optional[sd.InputStream] = None
        # Capture main event loop for cross-thread callback scheduling
        self.loop = asyncio.get_running_loop()

        # Clap state
        self._clap_times: deque = deque(maxlen=5)
        self._in_spike = False
        self._spike_start: float = 0.0
        self._last_wake_time: float = 0.0

        # Wake word state
        self._audio_buffer: deque = deque(
            maxlen=int(self._config.sample_rate * self._config.wake_word_buffer_seconds)
        )
        self._last_wake_word_check: float = 0.0
        self._groq_client: Optional[AsyncGroq] = None

        if GROQ_AVAILABLE and self._config.wake_word_enabled:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                # Clear proxy env vars that crash Groq SDK
                for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
                    os.environ.pop(k, None)
                self._groq_client = AsyncGroq(api_key=api_key)
                logger.info("Wake word detection enabled (Groq Whisper)")
            else:
                logger.warning("GROQ_API_KEY not set - wake word detection disabled")

    async def start(self) -> None:
        """Start listening for wake triggers."""
        if self._running:
            return

        self._running = True
        logger.info(
            "Wake detector started - listening for claps"
            + (" and 'Hey JARVIS'" if self._groq_client else "")
        )

        # Start audio stream
        self._stream = sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            blocksize=self._config.block_size,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()

        # Start wake word checker loop if enabled
        if self._groq_client:
            asyncio.create_task(self._wake_word_loop())

    async def stop(self) -> None:
        """Stop listening."""
        self._running = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        logger.info("Wake detector stopped")

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Called by sounddevice for each audio block."""
        if status:
            logger.debug(f"Audio status: {status}")

        audio = indata[:, 0]  # mono

        # Add to wake word buffer
        self._audio_buffer.extend(audio.tolist())

        # Check for claps
        self._detect_clap(audio)

    def _detect_clap(self, audio: np.ndarray) -> None:
        """Detect double-clap pattern in audio block."""
        now = time.time()

        # Cooldown check
        if now - self._last_wake_time < self._config.clap_cooldown:
            return

        peak = float(np.max(np.abs(audio)))

        if peak > self._config.clap_threshold:
            if not self._in_spike:
                self._in_spike = True
                self._spike_start = now
        else:
            if self._in_spike:
                spike_duration = now - self._spike_start
                self._in_spike = False

                # Check if spike duration matches a clap
                if (self._config.clap_min_duration
                        <= spike_duration
                        <= self._config.clap_max_duration):
                    self._clap_times.append(now)
                    logger.debug(f"Clap detected (duration={spike_duration:.3f}s)")

                    # Check for double clap
                    if len(self._clap_times) >= 2:
                        gap = self._clap_times[-1] - self._clap_times[-2]
                        if gap <= self._config.double_clap_window:
                            self._trigger_wake("double_clap")

    def _trigger_wake(self, method: str) -> None:
        """Fire wake event."""
        now = time.time()
        if now - self._last_wake_time < self._config.clap_cooldown:
            return

        self._last_wake_time = now
        self._clap_times.clear()
        logger.info(f"WAKE DETECTED via {method}")

        if self._on_wake:
            # Callback may be invoked from sounddevice thread (no event loop there)
            if asyncio.iscoroutinefunction(self._on_wake):
                asyncio.run_coroutine_threadsafe(self._on_wake(method), self.loop)
            else:
                self.loop.call_soon_threadsafe(self._on_wake, method)

        # Re-arm spike state so next clap sequence is clean
        self._in_spike = False
        self._spike_start = 0.0

    async def _wake_word_loop(self) -> None:
        """Periodically check audio buffer for wake word."""
        while self._running:
            await asyncio.sleep(self._config.wake_word_check_interval)

            if not self._running:
                break

            # Check if there's enough audio energy to bother transcribing
            if len(self._audio_buffer) < self._config.sample_rate:
                continue

            audio_array = np.array(list(self._audio_buffer), dtype=np.float32)
            energy = float(np.mean(np.abs(audio_array)))

            if energy < self._config.speech_energy_threshold:
                continue

            # Transcribe buffer
            try:
                text = await self._transcribe_buffer(audio_array)
                if text:
                    text_lower = text.lower().strip()
                    for wake_word in self._config.wake_words:
                        if wake_word in text_lower:
                            self._audio_buffer.clear()
                            self._trigger_wake(f"wake_word:'{wake_word}'")
                            break
            except Exception as e:
                logger.debug(f"Wake word check failed: {e}")

    async def _transcribe_buffer(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe audio buffer using Groq Whisper."""
        if not self._groq_client:
            return None

        # Convert float32 audio to WAV bytes
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(self._config.sample_rate)
            # Convert float32 [-1,1] to int16
            int16_audio = (audio * 32767).astype(np.int16)
            wf.writeframes(int16_audio.tobytes())

        wav_buffer.seek(0)
        wav_buffer.name = "wake_check.wav"

        transcription = await self._groq_client.audio.transcriptions.create(
            file=wav_buffer,
            model=self._config.groq_model,
            language="en",
            response_format="text",
        )

        return transcription.strip() if transcription else None

    @property
    def is_running(self) -> bool:
        return self._running


# ══ STANDALONE TEST ══════════════════════════════════════════════

async def _test():
    """Test wake detection standalone."""
    print("\n" + "=" * 50)
    print("  JARVIS Wake Detector - Test Mode")
    print("  Clap twice or say 'Hey JARVIS'")
    print("  Press Ctrl+C to stop")
    print("=" * 50 + "\n")

    async def on_wake(method: str):
        print(f"\n  WAKE DETECTED! Method: {method}\n")

    detector = WakeDetector(on_wake=on_wake)
    await detector.start()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await detector.stop()
        print("\nStopped.")


if __name__ == "__main__":
    asyncio.run(_test())
