# ================================================================
# JARVIS - Task Chain Executor v1.0 (Ported)
# ================================================================
# Multi-step command parsing and execution with:
#   - Complex command breakdown (Hinglish/Urdu/English)
#   - Goal persistence (SQLite)
#   - Error recovery with fallbacks
#   - Multi-step context maintenance
# ================================================================

from __future__ import annotations

import asyncio
import json
import os
import re
import sqlite3
import sys
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable

import logging

# Set up logging with UTF-8 support for Windows
if sys.platform == "win32":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("jarvis_task_chain.log", encoding="utf-8")
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
            logging.FileHandler("jarvis_task_chain.log", encoding="utf-8")
        ]
    )

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# TASK STATUS & TYPES
# ══════════════════════════════════════════════════════════════════

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    OPEN_APP = "open_app"
    CREATE_FILE = "create_file"
    SEND_EMAIL = "send_email"
    SCHEDULE = "schedule"
    SEARCH = "search"
    SYSTEM = "system"
    CODE = "code"
    GENERAL = "general"
    COMPOUND = "compound"  # Multiple tasks combined


# ══════════════════════════════════════════════════════════════════
# TASK DATACLASS
# ══════════════════════════════════════════════════════════════════

@dataclass
class Task:
    """Single executable task in a chain."""
    command: str
    task_type: TaskType = TaskType.GENERAL
    status: TaskStatus = TaskStatus.PENDING
    task_id: str = ""
    parent_chain_id: str = ""
    step_number: int = 0

    # Execution details
    result: str = ""
    error: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    retries: int = 0
    max_retries: int = 2

    # Context
    context: Dict[str, Any] = field(default_factory=dict)
    fallback_commands: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)  # task_ids

    def __post_init__(self):
        if not self.task_id:
            raw = f"{self.command[:30]}{time.time()}"
            self.task_id = hashlib.md5(raw.encode()).hexdigest()[:12]

    def duration_ms(self) -> int:
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time) * 1000)
        return 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "command": self.command,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "step_number": self.step_number,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms(),
            "retries": self.retries,
        }


@dataclass
class TaskChain:
    """A chain of related tasks from a complex command."""
    chain_id: str = ""
    original_command: str = ""
    tasks: List[Task] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0
    user_id: str = ""
    context: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.chain_id:
            raw = f"{self.original_command[:30]}{self.created_at}"
            self.chain_id = hashlib.md5(raw.encode()).hexdigest()[:12]

    def progress(self) -> str:
        completed = sum(1 for t in self.tasks if t.status == TaskStatus.COMPLETED)
        return f"{completed}/{len(self.tasks)}"

    def to_dict(self) -> dict:
        return {
            "chain_id": self.chain_id,
            "original_command": self.original_command,
            "status": self.status.value,
            "progress": self.progress(),
            "tasks": [t.to_dict() for t in self.tasks],
            "created_at": datetime.fromtimestamp(self.created_at).isoformat(),
        }


# ══════════════════════════════════════════════════════════════════
# COMMAND PATTERN DATABASE
# ══════════════════════════════════════════════════════════════════

# Multi-step command connectors (Hinglish/Urdu/English)
CHAIN_CONNECTORS = re.compile(
    r"\b(aur|phir|uske baad|then|and then|after that|بعد میں|پھر|اور|also|fir|toh|tab)\b",
    re.IGNORECASE | re.UNICODE
)

# Reference patterns for context ("usme", "woh", "that", etc.)
REFERENCE_PATTERNS = re.compile(
    r"\b(usme|usmein|uspe|isme|ismein|ispe|woh|wo|yeh|ye|that|this|it|isko|usko|اس میں|وہ|یہ)\b",
    re.IGNORECASE | re.UNICODE
)

# Recall patterns ("woh wala", "last wala", "pehle wala")
RECALL_PATTERNS = re.compile(
    r"\b(woh\s*wala|wo\s*wala|last\s*wala|pehle\s*wala|same\s*again|phirse|dobara|repeat|وہ والا|پہلے والا)\b",
    re.IGNORECASE | re.UNICODE
)

# Task type detection patterns
TASK_PATTERNS = {
    TaskType.OPEN_APP: re.compile(
        r"\b(open|kholo|khol|chalu|start|launch|run|kholna|کھولو|खोलो)\b",
        re.IGNORECASE | re.UNICODE
    ),
    TaskType.CREATE_FILE: re.compile(
        r"\b(create|banao|bana|make|likho|likh|new\s*(file|folder)|بناؤ|बनाओ)\b",
        re.IGNORECASE | re.UNICODE
    ),
    TaskType.SEND_EMAIL: re.compile(
        r"\b(email|mail|bhejo|send|forward|reply|ای میل|ईमेल)\b",
        re.IGNORECASE | re.UNICODE
    ),
    TaskType.SCHEDULE: re.compile(
        r"\b(schedule|meeting|calendar|remind|reminder|kal|tomorrow|parso|میٹنگ|کیلنڈر)\b",
        re.IGNORECASE | re.UNICODE
    ),
    TaskType.SEARCH: re.compile(
        r"\b(search|dhundho|find|google|lookup|تلاش|ढूंढो)\b",
        re.IGNORECASE | re.UNICODE
    ),
    TaskType.SYSTEM: re.compile(
        r"\b(screenshot|volume|brightness|wifi|bluetooth|shutdown|restart|lock|mute)\b",
        re.IGNORECASE | re.UNICODE
    ),
    TaskType.CODE: re.compile(
        r"\b(code|program|script|function|class|python|javascript|کوڈ|कोड)\b",
        re.IGNORECASE | re.UNICODE
    ),
}

# App fallbacks (primary -> alternatives)
APP_FALLBACKS: Dict[str, List[str]] = {
    "notepad": ["wordpad", "write", "notepad++", "vscode"],
    "chrome": ["msedge", "firefox", "browser"],
    "calculator": ["calc.exe", "python -c \"import tkinter\""],
    "word": ["wordpad", "write", "notepad"],
    "excel": ["calc", "google sheets"],
    "vscode": ["code", "notepad++", "sublime"],
    "terminal": ["cmd", "powershell", "wt"],
}


# ══════════════════════════════════════════════════════════════════
# GOAL PERSISTENCE (SQLite)
# ══════════════════════════════════════════════════════════════════

class GoalStore:
    """
    Persistent storage for incomplete tasks and goals.
    Enables resumption across sessions.
    """

    DB_PATH = Path("memory/voice_goals.db")

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_chains (
                chain_id TEXT PRIMARY KEY,
                original_command TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                tasks_json TEXT,
                context_json TEXT,
                user_id TEXT DEFAULT '',
                created_at REAL,
                updated_at REAL,
                completed_at REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS command_patterns (
                pattern_id TEXT PRIMARY KEY,
                command TEXT NOT NULL,
                parsed_tasks_json TEXT,
                success_count INTEGER DEFAULT 0,
                fail_count INTEGER DEFAULT 0,
                last_used REAL,
                shortcut TEXT DEFAULT ''
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversation_context (
                context_id TEXT PRIMARY KEY,
                user_id TEXT,
                last_command TEXT,
                last_result TEXT,
                last_task_type TEXT,
                last_object TEXT,
                context_json TEXT,
                timestamp REAL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chain_status ON task_chains(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chain_user ON task_chains(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pattern_shortcut ON command_patterns(shortcut)")
        conn.commit()
        conn.close()

    def save_chain(self, chain: TaskChain) -> None:
        """Save or update a task chain."""
        conn = sqlite3.connect(self.db_path)
        tasks_json = json.dumps([t.to_dict() for t in chain.tasks])
        context_json = json.dumps(chain.context)
        conn.execute("""
            INSERT OR REPLACE INTO task_chains
            (chain_id, original_command, status, tasks_json, context_json,
             user_id, created_at, updated_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chain.chain_id,
            chain.original_command,
            chain.status.value,
            tasks_json,
            context_json,
            chain.user_id,
            chain.created_at,
            time.time(),
            chain.completed_at,
        ))
        conn.commit()
        conn.close()

    def get_incomplete_chains(self, user_id: str = "") -> List[TaskChain]:
        """Get all incomplete task chains for a user."""
        conn = sqlite3.connect(self.db_path)
        query = """
            SELECT chain_id, original_command, status, tasks_json, context_json,
                   user_id, created_at, completed_at
            FROM task_chains
            WHERE status IN ('pending', 'in_progress')
        """
        params = []
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        query += " ORDER BY created_at DESC"

        rows = conn.execute(query, params).fetchall()
        conn.close()

        chains = []
        for row in rows:
            chain = TaskChain(
                chain_id=row[0],
                original_command=row[1],
                status=TaskStatus(row[2]),
                user_id=row[5],
                created_at=row[6],
                completed_at=row[7] or 0.0,
            )
            chain.context = json.loads(row[4] or '{}')
            # Reconstruct tasks from JSON
            tasks_data = json.loads(row[3] or '[]')
            for td in tasks_data:
                task = Task(
                    task_id=td.get('task_id', ''),
                    command=td.get('command', ''),
                    task_type=TaskType(td.get('task_type', 'general')),
                    status=TaskStatus(td.get('status', 'pending')),
                    step_number=td.get('step_number', 0),
                    result=td.get('result', ''),
                    error=td.get('error', ''),
                )
                chain.tasks.append(task)
            chains.append(chain)

        return chains

    def mark_chain_complete(self, chain_id: str) -> None:
        """Mark a chain as completed."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE task_chains
            SET status = 'completed', completed_at = ?, updated_at = ?
            WHERE chain_id = ?
        """, (time.time(), time.time(), chain_id))
        conn.commit()
        conn.close()

    def save_pattern(self, command: str, tasks: List[Task], shortcut: str = "") -> None:
        """Save a successful command pattern for learning."""
        pattern_id = hashlib.md5(command.lower().encode()).hexdigest()[:12]
        tasks_json = json.dumps([t.to_dict() for t in tasks])

        conn = sqlite3.connect(self.db_path)
        # Check if exists
        existing = conn.execute(
            "SELECT success_count FROM command_patterns WHERE pattern_id = ?",
            (pattern_id,)
        ).fetchone()

        if existing:
            conn.execute("""
                UPDATE command_patterns
                SET success_count = success_count + 1, last_used = ?, shortcut = COALESCE(?, shortcut)
                WHERE pattern_id = ?
            """, (time.time(), shortcut or None, pattern_id))
        else:
            conn.execute("""
                INSERT INTO command_patterns
                (pattern_id, command, parsed_tasks_json, success_count, last_used, shortcut)
                VALUES (?, ?, ?, 1, ?, ?)
            """, (pattern_id, command, tasks_json, time.time(), shortcut or ''))

        conn.commit()
        conn.close()

    def get_pattern(self, command: str) -> Optional[List[dict]]:
        """Get a learned pattern if it exists."""
        pattern_id = hashlib.md5(command.lower().encode()).hexdigest()[:12]

        conn = sqlite3.connect(self.db_path)
        row = conn.execute(
            "SELECT parsed_tasks_json FROM command_patterns WHERE pattern_id = ? AND success_count >= 2",
            (pattern_id,)
        ).fetchone()
        conn.close()

        if row:
            return json.loads(row[0])
        return None

    def get_shortcut(self, shortcut: str) -> Optional[str]:
        """Get the original command for a shortcut (e.g., 'woh wala')."""
        conn = sqlite3.connect(self.db_path)
        # Get most recent successful pattern with this shortcut
        row = conn.execute("""
            SELECT command FROM command_patterns
            WHERE shortcut = ? OR command LIKE ?
            ORDER BY last_used DESC LIMIT 1
        """, (shortcut, f"%{shortcut}%")).fetchone()
        conn.close()

        return row[0] if row else None

    def save_context(self, user_id: str, command: str, result: str,
                     task_type: str, last_object: str, context: dict) -> None:
        """Save conversation context for reference resolution."""
        context_id = hashlib.md5(user_id.encode()).hexdigest()[:12]

        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO conversation_context
            (context_id, user_id, last_command, last_result, last_task_type,
             last_object, context_json, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            context_id, user_id, command, result, task_type,
            last_object, json.dumps(context), time.time()
        ))
        conn.commit()
        conn.close()

    def get_context(self, user_id: str) -> Optional[dict]:
        """Get conversation context for a user."""
        context_id = hashlib.md5(user_id.encode()).hexdigest()[:12]

        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT last_command, last_result, last_task_type, last_object, context_json
            FROM conversation_context
            WHERE context_id = ? AND timestamp > ?
        """, (context_id, time.time() - 3600)).fetchone()  # 1 hour context window
        conn.close()

        if row:
            return {
                "last_command": row[0],
                "last_result": row[1],
                "last_task_type": row[2],
                "last_object": row[3],
                "context": json.loads(row[4] or '{}'),
            }
        return None


# ══════════════════════════════════════════════════════════════════
# TASK CHAIN EXECUTOR
# ══════════════════════════════════════════════════════════════════

class TaskChainExecutor:
    """
    Main executor for multi-step voice commands.

    Features:
    - Parse complex commands into task chains
    - Execute with status updates
    - Error recovery with fallbacks
    - Context maintenance
    - Goal persistence
    - Pattern learning

    Usage:
        executor = TaskChainExecutor(prompt_generator, llm_callable)
        result = await executor.process("Report banao, email karo, meeting schedule karo")
    """

    def __init__(
        self,
        prompt_generator=None,
        llm_callable: Optional[Callable] = None,
        user_id: str = "default",
    ):
        self.pg = prompt_generator
        self.llm = llm_callable
        self.user_id = user_id

        self.goal_store = GoalStore()
        self.current_chain: Optional[TaskChain] = None
        self.context: Dict[str, Any] = {}  # Current task context
        self.history: List[Dict[str, Any]] = []  # Recent commands

        # Load any existing context
        saved_ctx = self.goal_store.get_context(user_id)
        if saved_ctx:
            self.context = saved_ctx.get("context", {})
            self.context["last_object"] = saved_ctx.get("last_object", "")
            self.context["last_command"] = saved_ctx.get("last_command", "")

    # ══ MAIN ENTRY POINT ══════════════════════════════════════════

    async def process(self, text: str) -> str:
        """
        Process a voice command, detecting if it's complex/multi-part.
        Returns response text with status updates.
        """
        text = text.strip()
        if not text:
            return "Kya karna hai sir?"

        logger.info(f"TaskChain processing: '{text}'")

        # 1. Check for recall patterns ("woh wala karo")
        if RECALL_PATTERNS.search(text):
            return await self._handle_recall(text)

        # 2. Check for resume request ("kal wala complete karo")
        if self._is_resume_request(text):
            return await self._handle_resume(text)

        # 3. Check for reference ("usme yeh add karo")
        if REFERENCE_PATTERNS.search(text) and self.context.get("last_object"):
            text = self._resolve_reference(text)

        # 4. Check if complex command (has chain connectors)
        if self._is_complex_command(text):
            return await self._handle_complex_command(text)

        # 5. Check for learned pattern
        pattern = self.goal_store.get_pattern(text)
        if pattern:
            logger.info(f"Using learned pattern for: {text}")
            # Convert pattern to tasks and execute
            tasks = [Task(
                command=p.get('command', ''),
                task_type=TaskType(p.get('task_type', 'general')),
                step_number=i,
            ) for i, p in enumerate(pattern)]
            return await self._execute_chain(tasks, text)

        # 6. Single command - delegate to prompt_generator
        if self.pg:
            result = await self.pg.process(text)
            self._update_context(text, result)
            return result

        return f"Command received: {text}"

    # ══ COMMAND PARSING ═══════════════════════════════════════════

    def _is_complex_command(self, text: str) -> bool:
        """Check if command has multiple parts."""
        # Check for connectors
        if CHAIN_CONNECTORS.search(text):
            return True
        # Check for comma-separated commands
        if ',' in text and len(text.split(',')) > 1:
            parts = [p.strip() for p in text.split(',')]
            # Each part should have a verb
            verbs_found = sum(1 for p in parts if self._detect_task_type(p) != TaskType.GENERAL)
            return verbs_found >= 2
        return False

    def _is_resume_request(self, text: str) -> bool:
        """Check if user wants to resume incomplete task."""
        resume_patterns = [
            r"\b(resume|continue|jari|complete|khatam|finish|kal\s*ka|pehle\s*ka|جاری|مکمل)\b",
            r"woh\s*(jo|wala).*?(shuru|start|pending)",
            r"(incomplete|pending|adhura|ادھورا)\s*(task|kaam|کام)",
        ]
        for pattern in resume_patterns:
            if re.search(pattern, text, re.IGNORECASE | re.UNICODE):
                return True
        return False

    async def parse_complex_command(self, text: str) -> List[Task]:
        """
        Parse a complex command into individual tasks.
        Uses LLM if available for better understanding.
        """
        # Try LLM parsing first if available
        if self.llm:
            try:
                tasks = await self._llm_parse(text)
                if tasks:
                    return tasks
            except Exception as e:
                logger.warning(f"LLM parsing failed: {e}, falling back to rule-based")

        # Rule-based parsing fallback
        return self._rule_based_parse(text)

    async def _llm_parse(self, text: str) -> List[Task]:
        """Use LLM to parse complex command into steps."""
        from datetime import datetime

        prompt = f"""You are a task parser for a voice assistant. Break down this complex command into individual tasks.

Command: "{text}"

Rules:
1. Each task should be a single actionable command
2. Preserve the original language/words where possible
3. Identify task type: open_app, create_file, send_email, schedule, search, system, code, general
4. Return JSON array of tasks

Example input: "Notepad kholo aur ek letter likho phir email karo"
Example output:
[
  {{"command": "Notepad kholo", "type": "open_app"}},
  {{"command": "ek letter likho", "type": "create_file"}},
  {{"command": "email karo", "type": "send_email"}}
]

Return ONLY the JSON array, no other text."""

        response = await self.llm(prompt)

        # Parse JSON from response
        try:
            # Clean response
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            tasks_data = json.loads(response)
            tasks = []
            for i, td in enumerate(tasks_data):
                task_type = TaskType.GENERAL
                try:
                    task_type = TaskType(td.get('type', 'general'))
                except ValueError:
                    pass

                task = Task(
                    command=td.get('command', ''),
                    task_type=task_type,
                    step_number=i,
                )
                # Add fallbacks for apps
                if task_type == TaskType.OPEN_APP:
                    app_name = self._extract_app_name(td.get('command', ''))
                    if app_name and app_name.lower() in APP_FALLBACKS:
                        task.fallback_commands = APP_FALLBACKS[app_name.lower()]

                tasks.append(task)

            return tasks
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
            return []

    def _rule_based_parse(self, text: str) -> List[Task]:
        """Rule-based parsing for complex commands."""
        tasks = []

        # Split by connectors
        parts = CHAIN_CONNECTORS.split(text)
        parts = [p.strip() for p in parts if p.strip() and not CHAIN_CONNECTORS.match(p)]

        # If no connector-based split, try comma
        if len(parts) <= 1:
            parts = [p.strip() for p in text.split(',') if p.strip()]

        for i, part in enumerate(parts):
            task_type = self._detect_task_type(part)
            task = Task(
                command=part,
                task_type=task_type,
                step_number=i,
            )

            # Add fallbacks for apps
            if task_type == TaskType.OPEN_APP:
                app_name = self._extract_app_name(part)
                if app_name and app_name.lower() in APP_FALLBACKS:
                    task.fallback_commands = APP_FALLBACKS[app_name.lower()]

            tasks.append(task)

        return tasks

    def _detect_task_type(self, text: str) -> TaskType:
        """Detect task type from command text."""
        for task_type, pattern in TASK_PATTERNS.items():
            if pattern.search(text):
                return task_type
        return TaskType.GENERAL

    def _extract_app_name(self, text: str) -> str:
        """Extract application name from open command."""
        # Remove common verbs
        cleaned = re.sub(
            r"\b(open|kholo|khol|chalu|start|launch|run|please|jarvis|hey|sir)\b",
            "",
            text,
            flags=re.IGNORECASE
        ).strip()
        return cleaned

    # ══ EXECUTION ═════════════════════════════════════════════════

    async def _handle_complex_command(self, text: str) -> str:
        """Handle a multi-step command."""
        tasks = await self.parse_complex_command(text)

        if not tasks:
            return "Command samajh nahi aaya sir. Please repeat?"

        return await self._execute_chain(tasks, text)

    async def _execute_chain(self, tasks: List[Task], original_command: str) -> str:
        """Execute a chain of tasks with status updates."""
        # Create chain
        chain = TaskChain(
            original_command=original_command,
            tasks=tasks,
            user_id=self.user_id,
            status=TaskStatus.IN_PROGRESS,
        )
        self.current_chain = chain

        # Save to persistence
        self.goal_store.save_chain(chain)

        logger.info(f"Executing chain: {chain.chain_id} with {len(tasks)} tasks")

        results = []
        all_success = True

        for task in tasks:
            task.start_time = time.time()
            task.status = TaskStatus.IN_PROGRESS

            logger.info(f"Step {task.step_number + 1}/{len(tasks)}: {task.command}")

            try:
                result = await self._execute_with_recovery(task)
                task.result = result
                task.status = TaskStatus.COMPLETED
                task.end_time = time.time()

                results.append(f"Step {task.step_number + 1}: {result}")

                # Update context
                self._update_context_from_task(task)

            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                task.end_time = time.time()
                all_success = False

                results.append(f"Step {task.step_number + 1} failed: {str(e)[:50]}")
                logger.error(f"Task failed: {task.command} - {e}")

                # Continue to next task unless critical
                if not self._should_continue_on_failure(task):
                    break

            # Update chain in persistence
            self.goal_store.save_chain(chain)

        # Finalize chain
        chain.status = TaskStatus.COMPLETED if all_success else TaskStatus.FAILED
        chain.completed_at = time.time()
        self.goal_store.save_chain(chain)

        # Learn successful patterns
        if all_success:
            self.goal_store.save_pattern(original_command, tasks)
            self.history.append({
                "command": original_command,
                "tasks": len(tasks),
                "success": True,
                "timestamp": time.time(),
            })

        # Format response
        summary = f"Chain {chain.progress()} completed:\n" + "\n".join(results)
        return summary

    async def _execute_with_recovery(self, task: Task) -> str:
        """Execute a single task with fallback recovery."""
        last_error = None

        # Try main command
        for attempt in range(task.max_retries + 1):
            try:
                if self.pg:
                    return await self.pg.process(task.command)
                else:
                    return f"Executed: {task.command}"
            except Exception as e:
                last_error = e
                task.retries = attempt + 1
                logger.warning(f"Attempt {attempt + 1} failed for '{task.command}': {e}")
                await asyncio.sleep(0.5)

        # Try fallbacks
        for fallback in task.fallback_commands:
            logger.info(f"Trying fallback: {fallback}")
            try:
                fallback_task = Task(command=fallback, task_type=task.task_type)
                if self.pg:
                    result = await self.pg.process(fallback_task.command)
                    return f"{result} (using {fallback})"
            except Exception as e:
                logger.warning(f"Fallback '{fallback}' failed: {e}")
                continue

        # All attempts failed
        raise Exception(f"All attempts failed: {last_error}")

    def _should_continue_on_failure(self, task: Task) -> bool:
        """Determine if we should continue chain after a task failure."""
        # Critical tasks that should stop the chain
        critical_types = {TaskType.CREATE_FILE, TaskType.CODE}
        if task.task_type in critical_types:
            return False

        # Check if subsequent tasks depend on this one
        if task.depends_on:
            return False

        return True

    # ══ CONTEXT MANAGEMENT ════════════════════════════════════════

    def _resolve_reference(self, text: str) -> str:
        """Resolve reference words to actual objects."""
        last_object = self.context.get("last_object", "")
        if not last_object:
            return text

        # Replace reference with actual object
        resolved = REFERENCE_PATTERNS.sub(last_object, text)
        logger.info(f"Resolved reference: '{text}' -> '{resolved}'")
        return resolved

    def _update_context(self, command: str, result: str):
        """Update conversation context after command execution."""
        task_type = self._detect_task_type(command).value

        # Extract the object/target of the command
        last_object = self._extract_object(command)

        self.context["last_command"] = command
        self.context["last_result"] = result
        self.context["last_task_type"] = task_type
        if last_object:
            self.context["last_object"] = last_object

        # Save to persistence
        self.goal_store.save_context(
            user_id=self.user_id,
            command=command,
            result=result,
            task_type=task_type,
            last_object=last_object,
            context=self.context,
        )

    def _update_context_from_task(self, task: Task):
        """Update context from a completed task."""
        self._update_context(task.command, task.result)

        # Add to chain context
        if self.current_chain:
            self.current_chain.context[f"step_{task.step_number}"] = {
                "command": task.command,
                "result": task.result,
                "type": task.task_type.value,
            }

    def _extract_object(self, command: str) -> str:
        """Extract the main object/target from a command."""
        # Remove verbs and common words
        cleaned = re.sub(
            r"\b(open|kholo|create|banao|send|bhejo|search|dhundho|please|jarvis|sir|hey|"
            r"the|a|an|ek|yeh|woh|mujhe|mein|ko|ka|ki|ke|se|par|pe)\b",
            "",
            command,
            flags=re.IGNORECASE
        ).strip()

        # Return first meaningful word/phrase
        words = cleaned.split()
        if words:
            return " ".join(words[:3])  # Max 3 words
        return ""

    # ══ RECALL & RESUME ═══════════════════════════════════════════

    async def _handle_recall(self, text: str) -> str:
        """Handle recall patterns like 'woh wala karo'."""
        # Try to find the last successful complex command
        if self.history:
            last = self.history[-1]
            logger.info(f"Recalling last command: {last['command']}")
            return await self.process(last['command'])

        # Try from database
        shortcuts = ["woh wala", "last wala", "pehle wala"]
        for shortcut in shortcuts:
            if shortcut in text.lower():
                original = self.goal_store.get_shortcut(shortcut)
                if original:
                    logger.info(f"Recalling from DB: {original}")
                    return await self.process(original)

        return "Sir, pehle koi complex command nahi mila. Please repeat?"

    async def _handle_resume(self, text: str) -> str:
        """Resume incomplete tasks from previous session."""
        incomplete = self.goal_store.get_incomplete_chains(self.user_id)

        if not incomplete:
            return "Sir, koi pending task nahi hai."

        # Get most recent incomplete chain
        chain = incomplete[0]

        # Find first incomplete task
        remaining_tasks = [t for t in chain.tasks if t.status in (TaskStatus.PENDING, TaskStatus.FAILED)]

        if not remaining_tasks:
            self.goal_store.mark_chain_complete(chain.chain_id)
            return "Woh task toh complete ho gaya tha sir."

        logger.info(f"Resuming chain {chain.chain_id} with {len(remaining_tasks)} remaining tasks")

        # Resume execution
        return await self._execute_chain(remaining_tasks, f"Resume: {chain.original_command}")

    # ══ STATUS & DEBUGGING ════════════════════════════════════════

    def get_status(self) -> dict:
        """Get current executor status."""
        incomplete = self.goal_store.get_incomplete_chains(self.user_id)
        return {
            "current_chain": self.current_chain.to_dict() if self.current_chain else None,
            "incomplete_chains": len(incomplete),
            "history_length": len(self.history),
            "context": self.context,
        }

    def clear_context(self):
        """Clear current context (useful for testing)."""
        self.context = {}
        self.history = []
        self.current_chain = None


# ══════════════════════════════════════════════════════════════════
# INTEGRATION HELPER
# ══════════════════════════════════════════════════════════════════

def is_complex_command(text: str) -> bool:
    """
    Quick check if a command is complex (for routing).
    Use this in prompt_generator to decide whether to use TaskChainExecutor.
    """
    from datetime import datetime

    if CHAIN_CONNECTORS.search(text):
        return True
    if RECALL_PATTERNS.search(text):
        return True
    if ',' in text:
        parts = [p.strip() for p in text.split(',')]
        if len(parts) >= 2:
            # Check if parts look like separate commands
            verb_count = 0
            for p in parts:
                for pattern in TASK_PATTERNS.values():
                    if pattern.search(p):
                        verb_count += 1
                        break
            return verb_count >= 2
    return False


# ══════════════════════════════════════════════════════════════════
# EXPORTS
# ══════════════════════════════════════════════════════════════════

__all__ = [
    'TaskChainExecutor',
    'Task',
    'TaskChain',
    'TaskStatus',
    'TaskType',
    'GoalStore',
    'is_complex_command',
]
