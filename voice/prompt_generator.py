# ================================================================
# JARVIS - Prompt Generator v1.0 (Ported)
# ================================================================
# Takes user voice commands and generates smart prompts
# for code generation, app actions, and system control
# ================================================================

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import logging

# Set up logging with UTF-8 support for Windows
if sys.platform == "win32":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_prompt.log", encoding="utf-8")
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
            logging.FileHandler("jarvis_prompt.log", encoding="utf-8")
        ]
    )

logger = logging.getLogger(__name__)

# Import desktop-specific modules if available (optional dependencies)
try:
    from voice.computer_controller import ComputerController
    COMPUTER_CONTROLLER_AVAILABLE = True
except ImportError:
    COMPUTER_CONTROLLER_AVAILABLE = False
    logger.warning("ComputerController not available - some features disabled")

try:
    from voice.screen_analyzer import ScreenAnalyzer
    SCREEN_ANALYZER_AVAILABLE = True
except ImportError:
    SCREEN_ANALYZER_AVAILABLE = False
    logger.warning("ScreenAnalyzer not available - some features disabled")

try:
    from voice.task_chain_executor import TaskChainExecutor
    TASK_CHAIN_AVAILABLE = True
except ImportError:
    TASK_CHAIN_AVAILABLE = False
    logger.warning("TaskChainExecutor not available - complex commands disabled")

_COMPLEX_CHAIN_PATTERN = re.compile(r"\b(and|then|phir|uske\s+baad)\b|,")


# ══ INTENT TYPES ═════════════════════════════════════════════════

class IntentType:
    OPEN_APP = "open_app"
    CREATE_CODE = "create_code"
    SYSTEM_CONTROL = "system_control"
    WEB_SEARCH = "web_search"
    TYPE_TEXT = "type_text"           # Type text command
    # Vision intents
    SCREEN_ANALYZE = "screen_analyze"
    IMAGE_ANALYZE = "image_analyze"
    DOCUMENT_READ = "document_read"
    GENERAL_QUERY = "general_query"


# ══ INTENT DETECTION ═════════════════════════════════════════════

# Keyword patterns for intent detection
_OPEN_PATTERNS = re.compile(
    r"\b(open|kholo|kholu|holo|chalu karo|start|launch|run|kholna|kholdo)\b",
    re.IGNORECASE,
)

# Script-based keywords (Urdu/Hindi) that regex \b misses
_OPEN_KEYWORDS_NATIVE = (
    "کھولو", "کھول", "खोलो", "खोल", "खोलना", "खोलो", "ओपन"
)

# App names that imply open intent
_APP_HINTS = (
    "نوٹ پیڈ", "نوٹ پیٹ", "نوٹپیڈ",  # Urdu notepad
    "नोटपैड", "नोट पैड", "नोटपेड", "नोटपेट",  # Hindi notepad
    "notepad", "note pad",  # English notepad
    "calculator", "calc", "کیلکولیٹر", "कैलकुलेटर",  # Calculator
    "chrome", "کروم", "क्रोम", "browser",  # Chrome
    "word", "excel", "powerpoint", "vscode", "code"  # Common apps
)

_CODE_PATTERNS = re.compile(
    r"\b(bana|banao|create|make|build|write|code|likhh?o|program)\b",
    re.IGNORECASE,
)

_SEARCH_PATTERNS = re.compile(
    r"\b(search|google|find|dhundho|dekho|look up)\b",
    re.IGNORECASE,
)

_SYSTEM_PATTERNS = re.compile(
    r"\b(screenshot|volume|brightness|wifi|bluetooth|shutdown|restart|lock|mute|unmute|"
    r"minimize|chhota|chota|maximize|bara|bada|close|band|switch|snap|window|"
    r"sleep|soja|desktop|task.?view|action.?center|folder|file|url|website)\b",
    re.IGNORECASE,
)

# Window management patterns (Urdu/Hindi + English)
_WINDOW_PATTERNS = re.compile(
    r"\b(minimize|maximize|close|switch|snap|window|band.?karo|chhota.?karo|bara.?karo|"
    r"choti.?karo|badi.?karo|hatao|switch.?karo|badle|left|right|بند|چھوٹا|بڑا)\b",
    re.IGNORECASE,
)

# File operation patterns
_FILE_PATTERNS = re.compile(
    r"\b(folder|file|banao|bana|create|Desktop|Documents|Downloads|make)\b",
    re.IGNORECASE,
)

# NEW: Type text patterns (Urdu/Hindi/English)
_TYPE_PATTERNS = re.compile(
    r"\b(likho|likhe|likh|type\s*karo|yeh\s*likho|write\s+this|type\s+this)\b",
    re.IGNORECASE,
)

# Script-based type keywords (Urdu/Hindi)
_TYPE_KEYWORDS_NATIVE = (
    "لکھو", "لکھ", "لکھیں",  # Urdu
    "लिखो", "लिख", "लिखें", "टाइप",  # Hindi
)

# ══ VISION PATTERNS ═════════════════════════════════════════════

# Screen analysis patterns
_SCREEN_PATTERNS = re.compile(
    r"\b(screen\s*pe\s*kya|screen\s*dekho|screen\s*analyze|analyze\s*screen|"
    r"kya\s*dikh\s*raha|what('?s)?\s*on\s*screen|describe\s*screen|"
    r"screen\s*padho|screen\s*dikhao|error\s*dekho|screen\s*check)\b",
    re.IGNORECASE,
)

# Native script screen keywords (Urdu/Hindi)
_SCREEN_KEYWORDS_NATIVE = (
    "سکرین دیکھو", "سکرین پر کیا", "اسکرین",  # Urdu
    "स्क्रीन देखो", "स्क्रीन पर क्या", "स्क्रीन",  # Hindi
)

# Image analysis patterns
_IMAGE_PATTERNS = re.compile(
    r"\b(image\s*analyze|analyze\s*image|photo\s*analyze|yeh\s*photo|"
    r"is\s*image|this\s*image|picture\s*dekho|tasveer|"
    r"analyze\s*this|what('?s)?\s*in\s*this|describe\s*this)\b",
    re.IGNORECASE,
)

# Document reading patterns
_DOCUMENT_PATTERNS = re.compile(
    r"\b(pdf\s*padho|read\s*pdf|document\s*padho|read\s*document|"
    r"word\s*padho|docx\s*padho|yeh\s*file|this\s*file|"
    r"summarize\s*pdf|pdf\s*summarize|document\s*summarize)\b",
    re.IGNORECASE,
)

# File path pattern (to extract paths from commands)
_FILE_PATH_PATTERN = re.compile(
    r'([A-Za-z]:\\[^\s"]+|[A-Za-z]:/[^\s"]+|~/[^\s"]+|/[^\s"]+\.\w+)',
    re.IGNORECASE,
)


def detect_intent(text: str) -> str:
    """Detect user's intent from transcribed text."""
    text_lower = text.lower()

    # ── Vision intents (check first for clarity) ──
    # Screen analysis
    if _SCREEN_PATTERNS.search(text_lower):
        return IntentType.SCREEN_ANALYZE
    if any(k in text for k in _SCREEN_KEYWORDS_NATIVE):
        return IntentType.SCREEN_ANALYZE

    # Document reading (PDF/Word)
    if _DOCUMENT_PATTERNS.search(text_lower):
        return IntentType.DOCUMENT_READ

    # Image analysis
    if _IMAGE_PATTERNS.search(text_lower):
        return IntentType.IMAGE_ANALYZE

    # ── System control ──
    if _SYSTEM_PATTERNS.search(text_lower):
        return IntentType.SYSTEM_CONTROL

    # NEW: Check for type text intent BEFORE open app (likho can be confused)
    if _TYPE_PATTERNS.search(text_lower):
        return IntentType.TYPE_TEXT

    # Native-script type intent (Urdu/Hindi)
    if any(k in text_lower for k in _TYPE_KEYWORDS_NATIVE) or any(k in text for k in _TYPE_KEYWORDS_NATIVE):
        return IntentType.TYPE_TEXT

    if _OPEN_PATTERNS.search(text_lower):
        return IntentType.OPEN_APP

    # Native-script open intent (Urdu/Hindi)
    if any(k in text_lower for k in _OPEN_KEYWORDS_NATIVE):
        return IntentType.OPEN_APP

    # App name mentioned = likely open intent (notepad, calculator, chrome, etc.)
    if any(a in text_lower for a in _APP_HINTS) or any(a in text for a in _APP_HINTS):
        return IntentType.OPEN_APP

    if _CODE_PATTERNS.search(text_lower):
        return IntentType.CREATE_CODE

    if _SEARCH_PATTERNS.search(text_lower):
        return IntentType.WEB_SEARCH

    return IntentType.GENERAL_QUERY


# ══ PROMPT GENERATOR ═════════════════════════════════════════════

class PromptGenerator:
    """
    Generates smart prompts and executes actions based on voice commands.

    Usage:
        gen = PromptGenerator(llm_callable=my_llm_function)
        response = await gen.process("calculator banao Python mein")
    """

    def __init__(
        self,
        llm_callable=None,
        output_dir: Optional[str] = None,
    ):
        self._llm = llm_callable
        self._ctrl = ComputerController() if COMPUTER_CONTROLLER_AVAILABLE else None
        self._screen = ScreenAnalyzer() if SCREEN_ANALYZER_AVAILABLE else None
        self._task_chain = TaskChainExecutor(self._process_single_step) if TASK_CHAIN_AVAILABLE else None
        self._output_dir = output_dir or os.path.join(
            os.path.expanduser("~"), "jarvis_output"
        )
        Path(self._output_dir).mkdir(parents=True, exist_ok=True)

    async def process(self, text: str) -> str:
        """Process a voice command and return response text."""
        if _COMPLEX_CHAIN_PATTERN.search(text) and TASK_CHAIN_AVAILABLE and len(text.split()) >= 5:
            logger.info(f"Complex task-chain detected | Command: '{text}'")
            return await self._task_chain.execute_chain(text)
        return await self._process_single_step(text)

    async def _process_single_step(self, text: str) -> str:
        intent = detect_intent(text)
        logger.info(f"Intent: {intent} | Command: '{text}'")

        handlers = {
            IntentType.OPEN_APP: self._handle_open_app,
            IntentType.CREATE_CODE: self._handle_create_code,
            IntentType.SYSTEM_CONTROL: self._handle_system_control,
            IntentType.WEB_SEARCH: self._handle_web_search,
            IntentType.TYPE_TEXT: self._handle_type_text,
            IntentType.SCREEN_ANALYZE: self._handle_screen_analyze,
            IntentType.IMAGE_ANALYZE: self._handle_image_analyze,
            IntentType.DOCUMENT_READ: self._handle_document_read,
            IntentType.GENERAL_QUERY: self._handle_general_query,
        }

        handler = handlers.get(intent, self._handle_general_query)
        return await handler(text)

    async def _handle_open_app(self, text: str) -> str:
        """Open an application."""
        if not self._ctrl:
            return "System control not available - cannot open apps"

        # Extract app name from command
        app_name = re.sub(
            r"\b(open|kholo|chalu karo|start|launch|run|please|jarvis|hey)\b",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        text_lower = text.lower()

        # Native-script normalization (multiple spelling variations)
        # Notepad variations
        notepad_patterns = (
            "نوٹ پیڈ", "نوٹ پیٹ", "نوٹپیڈ",  # Urdu
            "नोटपैड", "नोट पैड", "नोटपेड", "नोटपेट", "नोट पेड",  # Hindi
            "notepad", "note pad"  # English
        )
        if any(x in text_lower for x in notepad_patterns) or any(x in text for x in notepad_patterns):
            app_name = "notepad"
        # Calculator variations
        elif any(x in text_lower for x in ("calculator", "calc", "کیلکولیٹر", "कैलकुलेटर", "कैल्कुलेटर")):
            app_name = "calculator"
        # Chrome variations
        elif any(x in text_lower for x in ("کروم", "chrome", "क्रोम", "ब्राउज़र")):
            app_name = "chrome"

        if not app_name:
            return "Which app should I open sir?"

        success = await self._ctrl.open_app(app_name)
        if success:
            return f"{app_name} open kar diya sir"
        else:
            return f"Sorry sir, {app_name} open nahi ho saka"

    async def _handle_type_text(self, text: str) -> str:
        """
        Handle type text commands.

        Examples:
            - "Hello World likho" -> types "Hello World"
            - "type karo my name is JARVIS" -> types "my name is JARVIS"
            - "yeh likho good morning" -> types "good morning"
        """
        if not self._ctrl:
            return "System control not available - cannot type text"

        # Extract text after the type command
        # Remove command keywords from the text
        text_to_type = text

        # Patterns to remove (command keywords)
        remove_patterns = [
            r"\b(likho|likhe|likh)\b",
            r"\b(type\s*karo|type\s*kar)\b",
            r"\b(yeh\s*likho|ye\s*likho)\b",
            r"\b(write\s*this|type\s*this)\b",
            r"\b(please|jarvis|hey)\b",
            # Urdu/Hindi script keywords
            r"(لکھو|لکھ|لکھیں)",
            r"(लिखो|लिख|लिखें|टाइप)",
        ]

        for pattern in remove_patterns:
            text_to_type = re.sub(pattern, "", text_to_type, flags=re.IGNORECASE)

        text_to_type = text_to_type.strip()

        if not text_to_type:
            return "Kya likhna hai sir? Please text bolo."

        logger.info(f"Typing: '{text_to_type}'")

        try:
            # Use clipboard method for Unicode support
            await self._ctrl.type_text_unicode(text_to_type)
            return f"Likh diya sir: {text_to_type[:30]}{'...' if len(text_to_type) > 30 else ''}"
        except Exception as e:
            logger.error(f"Type text error: {e}")
            return f"Sorry sir, type nahi ho saka: {str(e)[:30]}"

    async def _handle_create_code(self, text: str) -> str:
        """Generate code and open in VS Code."""
        if not self._llm:
            return "Code generation requires LLM connection sir. LLM not available."

        # Generate code prompt
        prompt = (
            f"User wants to create code. Their request: '{text}'\n\n"
            f"Generate ONLY the complete, working Python code. "
            f"No explanations, no markdown, just pure code. "
            f"Include proper error handling and a main block."
        )

        try:
            code = await self._llm(prompt)

            if not code:
                return "Sorry sir, code generate nahi ho saka"

            # Clean code (remove markdown fences if any)
            code = self._clean_code(code)

            # Save to file
            filename = self._generate_filename(text)
            filepath = os.path.join(self._output_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(code)

            logger.info(f"Code saved: {filepath}")

            # Try to open VS Code with the file
            import subprocess

            try:
                # Try 'code' command first (VS Code in PATH)
                subprocess.Popen(
                    ["code", filepath],
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                logger.info(f"Opened {filepath} in VS Code")
            except Exception as e:
                logger.warning(f"VS Code not found via 'code' command: {e}")
                # Fallback: try notepad
                if self._ctrl:
                    await self._ctrl.open_app("notepad")
                    await asyncio.sleep(1.5)
                    # Type the code
                    await self._ctrl.type_text_unicode(code)

            return f"Code ready hai sir. File saved at {filepath} and opened in editor."

        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return f"Sorry sir, error: {str(e)[:50]}"

    async def _handle_system_control(self, text: str) -> str:
        """Handle system control commands."""
        if not self._ctrl:
            return "System control not available - cannot execute system commands"

        text_lower = text.lower()

        if "screenshot" in text_lower:
            path = await self._ctrl.screenshot()
            return f"Screenshot le liya sir, saved at {path}" if path else "Screenshot fail ho gaya sir"

        # Window management
        if any(w in text_lower for w in ("minimize", "chhota", "chota")):
            ok = await self._ctrl.minimize_window()
            return "Window minimize kar di sir" if ok else "Window minimize nahi ho saki sir"
        if any(w in text_lower for w in ("maximize", "bara", "bada")):
            ok = await self._ctrl.maximize_window()
            return "Window maximize kar di sir" if ok else "Window maximize nahi ho saki sir"
        if any(w in text_lower for w in ("close window", "window band", "alt f4")):
            ok = await self._ctrl.close_window()
            return "Window close kar di sir" if ok else "Window close nahi ho saki sir"
        if any(w in text_lower for w in ("switch", "alt tab")):
            ok = await self._ctrl.switch_window()
            return "Window switch kar di sir" if ok else "Window switch nahi ho saki sir"

        # URLs and web
        if "google" in text_lower and "search" in text_lower:
            query = re.sub(r"\b(google|search|karo|please|jarvis|hey)\b", "", text, flags=re.IGNORECASE).strip()
            if query:
                ok = await self._ctrl.search_google(query)
                return f"Google search kar diya sir: {query}" if ok else "Google search nahi ho saka sir"

        # Folder operations
        if "folder" in text_lower and any(w in text_lower for w in ("banao", "create", "make")):
            name = "New Folder"
            m = re.search(r"folder\s+(?:named\s+)?([a-zA-Z0-9_\- ]+)", text, flags=re.IGNORECASE)
            if m:
                name = m.group(1).strip()
            ok = await self._ctrl.create_folder("desktop", name)
            return f"Folder bana diya sir: {name}" if ok else "Folder nahi ban saka sir"

        # Volume controls
        if "volume" in text_lower:
            m = re.search(r"(\d{1,3})", text_lower)
            if m:
                level = int(m.group(1))
                ok = await self._ctrl.set_volume(level)
                return f"Volume {level}% kar diya sir" if ok else "Volume set nahi ho saka sir"
            if any(w in text_lower for w in ("up", "increase", "barhao")):
                await self._ctrl.hotkey("volumeup")
                await self._ctrl.hotkey("volumeup")
                await self._ctrl.hotkey("volumeup")
                return "Volume increase kar diya sir"
            elif any(w in text_lower for w in ("down", "decrease", "kam")):
                await self._ctrl.hotkey("volumedown")
                await self._ctrl.hotkey("volumedown")
                await self._ctrl.hotkey("volumedown")
                return "Volume decrease kar diya sir"
            elif any(w in text_lower for w in ("mute",)):
                ok = await self._ctrl.mute_unmute()
                return "Volume mute toggle kar diya sir" if ok else "Mute nahi ho saka sir"

        if "brightness" in text_lower:
            m = re.search(r"(\d{1,3})", text_lower)
            if m:
                level = int(m.group(1))
                ok = await self._ctrl.set_brightness(level)
                return f"Brightness {level}% set kar di sir" if ok else "Brightness set nahi ho saki sir"

        if "lock" in text_lower:
            ok = await self._ctrl.lock_screen()
            return "Screen lock kar diya sir" if ok else "Screen lock nahi ho saka sir"

        if "sleep" in text_lower:
            ok = await self._ctrl.sleep_pc()
            return "PC sleep mode mein daal diya sir" if ok else "Sleep command fail ho gaya sir"

        return f"System command samajh nahi aaya sir: {text}"

    async def _handle_web_search(self, text: str) -> str:
        """Open browser and search."""
        if not self._ctrl:
            return "System control not available - cannot search Google"

        query = re.sub(
            r"\b(search|google|find|dhundho|dekho|look up|for|on|please|jarvis|hey)\b",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()

        if not query:
            return "Kya search karoon sir?"

        ok = await self._ctrl.search_google(query)
        return f"Searching for '{query}' sir" if ok else f"Search nahi ho saka sir: {query}"

    async def _handle_screen_analyze(self, text: str) -> str:
        """Analyze current screen content."""
        if not self._screen:
            return "Screen analysis not available"

        prompt = re.sub(
            r"\b(screen\s*pe\s*kya|screen\s*dekho|screen\s*analyze|analyze\s*screen|what('?s)?\s*on\s*screen|describe\s*screen|please|jarvis|hey)\b",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        return await self._screen.analyze_screen(prompt=prompt)

    async def _handle_image_analyze(self, text: str) -> str:
        """Analyze provided image path."""
        if not self._screen:
            return "Image analysis not available"

        m = _FILE_PATH_PATTERN.search(text)
        if not m:
            return "Image path do sir. Example: C:/Users/AK/Desktop/test.png"
        image_path = m.group(1)
        return await self._screen.analyze_image(image_path=image_path)

    async def _handle_document_read(self, text: str) -> str:
        """Read and summarize PDF/Word/Text documents."""
        if not self._screen:
            return "Document reading not available"

        m = _FILE_PATH_PATTERN.search(text)
        if not m:
            return "Document path do sir. Example: C:/Users/AK/Desktop/file.pdf"
        doc_path = m.group(1)
        instruction = re.sub(re.escape(doc_path), "", text, flags=re.IGNORECASE).strip()
        return await self._screen.read_document(file_path=doc_path, instruction=instruction)

    async def _handle_general_query(self, text: str) -> str:
        """Handle general queries via LLM."""
        if not self._llm:
            return f"I heard: {text}. But LLM is not connected sir."

        try:
            prompt = (
                f"You are JARVIS, a helpful AI assistant. "
                f"Respond concisely in 1-2 sentences. "
                f"If the user speaks in Urdu/Roman Urdu, reply in the same style. "
                f"User: {text}"
            )
            response = await self._llm(prompt)
            return response or "Sorry sir, response generate nahi ho saka"
        except Exception as e:
            return f"Error sir: {str(e)[:50]}"

    @staticmethod
    def _clean_code(code: str) -> str:
        """Remove markdown code fences from LLM output."""
        code = code.strip()
        if code.startswith("```python"):
            code = code[len("```python"):].strip()
        elif code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
        return code

    @staticmethod
    def _generate_filename(text: str) -> str:
        """Generate a filename from the command text."""
        # Extract meaningful words
        words = re.findall(r"[a-zA-Z]+", text.lower())
        # Remove common words
        skip = {"a", "the", "me", "mujhe", "ek", "banao", "bana", "create",
                "make", "python", "mein", "in", "please", "jarvis"}
        meaningful = [w for w in words if w not in skip][:3]

        if meaningful:
            return "_".join(meaningful) + ".py"
        return f"jarvis_code_{int(time.time())}.py"
