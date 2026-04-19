# ================================================================
# JARVIS - Text to Speech v1.0 (Ported)
# ================================================================
# Primary: edge-tts (Microsoft voices - free, natural)
# Fallback: pyttsx3 (offline)
# Auto-detect: Urdu text - Urdu voice, English - English voice
# ================================================================

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Optional

import logging

# Set up logging with UTF-8 support for Windows
if sys.platform == "win32":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_tts.log", encoding="utf-8")
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
            logging.FileHandler("jarvis_tts.log", encoding="utf-8")
        ]
    )

logger = logging.getLogger(__name__)

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


# ══ CONFIG ═══════════════════════════════════════════════════════

@dataclass(frozen=True)
class TTSConfig:
    """Immutable TTS configuration."""
    english_voice: str = "en-US-GuyNeural"
    urdu_voice: str = "ur-PK-AsadNeural"
    hindi_voice: str = "hi-IN-MadhurNeural"
    english_rate: str = "+10%"
    urdu_rate: str = "+0%"
    hindi_rate: str = "+0%"
    volume: str = "+0%"
    temp_dir: str = ""


# ══ LANGUAGE DETECTION ═══════════════════════════════════════════

_URDU_PATTERN = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")
_HINDI_PATTERN = re.compile(r"[\u0900-\u097F]")


def detect_language(text: str) -> str:
    """Detect if text is primarily Urdu, Hindi, or English."""
    urdu_chars = len(_URDU_PATTERN.findall(text))
    hindi_chars = len(_HINDI_PATTERN.findall(text))
    total_alpha = sum(1 for c in text if c.isalpha())

    if total_alpha == 0:
        return "en"

    urdu_ratio = urdu_chars / total_alpha
    hindi_ratio = hindi_chars / total_alpha

    if urdu_ratio > 0.25:
        return "ur"
    if hindi_ratio > 0.25:
        return "hi"
    return "en"


# ══ TEXT TO SPEECH ═══════════════════════════════════════════════

class TextToSpeech:
    """Converts text to speech with auto language detection."""

    def __init__(self, config: Optional[TTSConfig] = None):
        self._config = config or TTSConfig()
        self._speaking = False

        if PYTTSX3_AVAILABLE:
            logger.info("TTS: pyttsx3 ready (offline voice)")
        elif EDGE_TTS_AVAILABLE:
            logger.info("TTS: edge-tts ready (English + Urdu voices)")
        else:
            logger.error("TTS: No TTS engine available!")

    async def speak(self, text: str) -> None:
        """Speak text aloud with auto language detection."""
        if not text or not text.strip():
            return

        lang = detect_language(text)
        logger.info(f"Speaking ({lang}): '{text[:60]}...'")

        if PYTTSX3_AVAILABLE:
            await self._speak_pyttsx3(text)
        elif EDGE_TTS_AVAILABLE:
            await self._speak_edge_tts(text, lang)
        else:
            logger.error("No TTS engine - cannot speak")

    async def _speak_edge_tts(self, text: str, lang: str) -> None:
        """Speak using edge-tts (Microsoft voices)."""
        temp_path = None
        try:
            if lang == "ur":
                voice = self._config.urdu_voice
                rate = self._config.urdu_rate
            elif lang == "hi":
                voice = self._config.hindi_voice
                rate = self._config.hindi_rate
            else:
                voice = self._config.english_voice
                rate = self._config.english_rate

            temp_dir = self._config.temp_dir or tempfile.gettempdir()
            temp_path = os.path.join(temp_dir, f"jarvis_tts_{int(time.time() * 1000)}.mp3")

            communicate = edge_tts.Communicate(
                text=text,
                voice=voice,
                rate=rate,
                volume=self._config.volume,
            )
            await communicate.save(temp_path)

            if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                raise RuntimeError("edge-tts produced empty audio file")

            self._speaking = True
            played = await self._play_audio(temp_path)
            self._speaking = False
            if not played:
                raise RuntimeError("audio playback failed")
        except Exception as e:
            logger.error(f"edge-tts error: {e}")
            if PYTTSX3_AVAILABLE:
                await self._speak_pyttsx3(text)
        finally:
            if temp_path:
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

    async def _speak_pyttsx3(self, text: str) -> None:
        """Speak using pyttsx3 (offline fallback)."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._pyttsx3_sync, text)
        except Exception as e:
            logger.error(f"pyttsx3 error: {e}")

    def _pyttsx3_sync(self, text: str) -> None:
        """Synchronous pyttsx3 speech with Windows COM init."""
        engine = None
        pythoncom_module = None
        com_initialized = False
        try:
            if os.name == "nt":
                try:
                    import pythoncom as pythoncom_module  # type: ignore
                    pythoncom_module.CoInitialize()
                    com_initialized = True
                except Exception:
                    pythoncom_module = None

            engine = pyttsx3.init()
            engine.setProperty("rate", 180)
            engine.setProperty("volume", 0.9)

            voices = engine.getProperty("voices")
            for voice in voices:
                if "male" in voice.name.lower() or "david" in voice.name.lower():
                    engine.setProperty("voice", voice.id)
                    break

            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"pyttsx3 sync error: {e}")
        finally:
            if engine:
                try:
                    engine.stop()
                except Exception:
                    pass
            if com_initialized and pythoncom_module:
                try:
                    pythoncom_module.CoUninitialize()
                except Exception:
                    pass

    async def _play_audio(self, filepath: str) -> bool:
        """Play an audio file using system player. Returns True on success."""
        try:
            if os.name == "nt":
                cmd = (
                    f'powershell -NoProfile -Command "'
                    f"Add-Type -AssemblyName PresentationCore; "
                    f"$ErrorActionPreference='Stop'; "
                    f"$p = New-Object System.Windows.Media.MediaPlayer; "
                    f"$p.Open([Uri]'{filepath}'); "
                    f"Start-Sleep -Milliseconds 300; "
                    f"if (-not $p.NaturalDuration.HasTimeSpan) {{ throw 'No audio duration' }}; "
                    f"$p.Play(); "
                    f"while ($p.Position -lt $p.NaturalDuration.TimeSpan) {{ Start-Sleep -Milliseconds 120 }}; "
                    f"$p.Stop(); $p.Close();"
                    f'"'
                )
                process = await asyncio.create_subprocess_shell(
                    cmd,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                code = await process.wait()
                return code == 0
            else:
                process = await asyncio.create_subprocess_exec(
                    "ffplay", "-nodisp", "-autoexit", filepath,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                code = await process.wait()
                return code == 0
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
            return False

    @property
    def is_speaking(self) -> bool:
        return self._speaking

    async def stop(self) -> None:
        """Stop any current speech."""
        self._speaking = False


async def _test():
    tts = TextToSpeech()
    await tts.speak("Hello sir, I am JARVIS.")


if __name__ == "__main__":
    asyncio.run(_test())
