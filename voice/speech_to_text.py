# ================================================================
# JARVIS - Speech to Text v1.0 (Ported)
# ================================================================
# Primary: Groq Whisper API (fast, free tier)
# Fallback: Google Speech Recognition
# Supports: English + Urdu (multilingual)
# ================================================================

from __future__ import annotations

import asyncio
import io
import json
import os
import sys
import tempfile
import time
import wave
from dataclasses import dataclass
from typing import Optional

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
            logging.FileHandler("jarvis_stt.log", encoding="utf-8")
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
            logging.FileHandler("jarvis_stt.log", encoding="utf-8")
        ]
    )

logger = logging.getLogger(__name__)

try:
    from groq import AsyncGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False


# ══ CONFIG ═══════════════════════════════════════════════════════

@dataclass(frozen=True)
class STTConfig:
    """Immutable STT configuration."""
    sample_rate: int = 16000
    channels: int = 1
    max_record_seconds: float = 15.0     # max recording time
    silence_threshold: float = 0.015     # amplitude below = silence
    silence_duration: float = 1.5        # seconds of silence to stop
    min_record_seconds: float = 0.5      # minimum recording time
    groq_model: str = "whisper-large-v3"


# ══ SPEECH TO TEXT ═══════════════════════════════════════════════

class SpeechToText:
    """
    Records audio from microphone and transcribes to text.

    Usage:
        stt = SpeechToText()
        text = await stt.listen_and_transcribe()
        print(f"You said: {text}")
    """

    def __init__(self, config: Optional[STTConfig] = None):
        self._config = config or STTConfig()
        self._groq_client: Optional[AsyncGroq] = None

        if GROQ_AVAILABLE:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self._groq_client = AsyncGroq(api_key=api_key)
                logger.info("STT: Groq Whisper ready")
            else:
                logger.warning("STT: GROQ_API_KEY not set - using Google fallback")

    async def listen_and_transcribe(self) -> Optional[str]:
        """Record from mic until silence, then transcribe."""
        logger.info("Listening... (speak now)")

        audio_data = await self._record_until_silence()

        if audio_data is None or len(audio_data) < self._config.sample_rate * self._config.min_record_seconds:
            logger.debug("Recording too short, ignoring")
            return None

        logger.info("Transcribing...")
        start = time.time()

        # Try Groq first, then Google fallback
        text = None
        if self._groq_client:
            text = await self._transcribe_groq(audio_data)

        if text is None and SR_AVAILABLE:
            text = await self._transcribe_google(audio_data)

        if text:
            elapsed = time.time() - start
            logger.info(f"Transcribed in {elapsed:.1f}s: '{text}'")
        else:
            logger.warning("Could not transcribe audio")

        return text

    async def _record_until_silence(self) -> Optional[np.ndarray]:
        """Record audio until silence is detected or max time reached."""
        recorded_frames: list = []
        silence_start: Optional[float] = None
        start_time = time.time()
        is_recording = True

        def callback(indata: np.ndarray, frames: int, time_info, status):
            nonlocal silence_start, is_recording

            if not is_recording:
                return

            audio = indata[:, 0].copy()
            recorded_frames.append(audio)

            energy = float(np.mean(np.abs(audio)))
            elapsed = time.time() - start_time

            if energy < self._config.silence_threshold:
                if silence_start is None:
                    silence_start = time.time()
                elif (time.time() - silence_start > self._config.silence_duration
                      and elapsed > self._config.min_record_seconds):
                    is_recording = False
            else:
                silence_start = None

            if elapsed > self._config.max_record_seconds:
                is_recording = False

        stream = sd.InputStream(
            samplerate=self._config.sample_rate,
            channels=self._config.channels,
            blocksize=self._config.sample_rate // 10,  # 100ms blocks
            dtype="float32",
            callback=callback,
        )

        stream.start()

        while is_recording:
            await asyncio.sleep(0.1)

        stream.stop()
        stream.close()

        if not recorded_frames:
            return None

        return np.concatenate(recorded_frames)

    async def _transcribe_groq(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe using Groq Whisper API."""
        try:
            wav_bytes = self._audio_to_wav(audio)
            wav_buffer = io.BytesIO(wav_bytes)
            wav_buffer.name = "recording.wav"

            transcription = await self._groq_client.audio.transcriptions.create(
                file=wav_buffer,
                model=self._config.groq_model,
                response_format="text",
            )

            text = transcription.strip() if transcription else None

            # Filter out empty/noise transcriptions
            if text and len(text) > 1 and text.lower() not in ("", "you", "the", "a"):
                return text

            return None

        except Exception as e:
            logger.error(f"Groq STT error: {e}")
            return None

    async def _transcribe_google(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe using Google Speech Recognition (fallback)."""
        try:
            recognizer = sr.Recognizer()

            # Convert to AudioData
            int16_audio = (audio * 32767).astype(np.int16)
            audio_data = sr.AudioData(
                int16_audio.tobytes(),
                self._config.sample_rate,
                2,  # 16-bit = 2 bytes
            )

            # Run in thread (blocking API)
            loop = asyncio.get_event_loop()
            text = await loop.run_in_executor(
                None,
                lambda: recognizer.recognize_google(audio_data, language="ur-PK"),
            )

            return text.strip() if text else None

        except sr.UnknownValueError:
            logger.debug("Google STT: could not understand")
            return None
        except Exception as e:
            logger.error(f"Google STT error: {e}")
            return None

    def _audio_to_wav(self, audio: np.ndarray) -> bytes:
        """Convert float32 numpy audio to WAV bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self._config.sample_rate)
            int16 = (audio * 32767).astype(np.int16)
            wf.writeframes(int16.tobytes())
        return buf.getvalue()


# ══ STANDALONE TEST ══════════════════════════════════════════════

async def _test():
    """Test STT standalone."""
    print("\n" + "=" * 50)
    print("  JARVIS Speech-to-Text - Test Mode")
    print("  Speak after the prompt...")
    print("=" * 50 + "\n")

    stt = SpeechToText()

    for i in range(3):
        print(f"\n--- Test {i+1}/3 ---")
        text = await stt.listen_and_transcribe()
        if text:
            print(f"  You said: '{text}'")
        else:
            print(f"  Could not understand")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(_test())
