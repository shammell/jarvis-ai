# ==========================================================
# JARVIS
# Features: Self-Healing DAG • Persistent Venv • Crash Recovery
# Robust JSON Parsing • Context Pinning • Safe Execution
# ==========================================================

import sys
import os

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    import codecs
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

import re, json, asyncio, logging, threading, time, uuid, subprocess, platform, signal, hashlib, ast
from datetime import datetime
from typing import Dict, Any, Optional, List
from core.registry import register_module
import aiofiles
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Optional imports with graceful fallbacks
try:
    import docker
except ImportError:
    docker = None
try:
    from groq import Groq
except ImportError:
    Groq = None
try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:
    chromadb = None

# ================= CONFIG =================
class CFG:
    MODEL = "llama-3.3-70b-versatile"
    TEMP = 0.1
    MAX_HEAL = 5
    MAX_CONCURRENT = 3
    GOAL_FILE = "GOAL.txt"
    VECTOR_PATH = "./vector_memory"
    EVENT_BUFFER = 500
    SHELL_TIMEOUT = 180
    DOCKER_IMAGE = "python:3.12-slim"
    FILE_HASH_HISTORY = "file_hashes.json"
    CONTEXT_MAX = 20000
    CHECKPOINT_FILE = "jarvis_state.json"

# ================= LOGGING =================
logging.basicConfig(level=logging.INFO, format="%(asctime)s ▶ %(message)s")

# ================= LIVE EVENT BUS =================
class EventBus:
    def __init__(self):
        self.events: List[str] = []
        self.lock = threading.Lock()

    def emit(self, msg: str):
        with self.lock:
            line = f"{datetime.now().strftime('%H:%M:%S')} | {msg}"
            self.events.append(line)
            if len(self.events) > CFG.EVENT_BUFFER:
                self.events.pop(0)
            print(line, flush=True)

    def stream(self):
        last = 0
        while True:
            time.sleep(0.4)
            with self.lock:
                if last < len(self.events):
                    for e in self.events[last:]:
                        yield f"data: {e}\n\n"
                    last = len(self.events)

EVENTS = EventBus()

# ================= VECTOR MEMORY =================
class Memory:
    def __init__(self):
        self.enabled = chromadb is not None
        if not self.enabled:
            EVENTS.emit("⚠ Vector memory disabled (chromadb not found)")
            return
        os.makedirs(CFG.VECTOR_PATH, exist_ok=True)
        self.client = chromadb.Client(chromadb.config.Settings(persist_directory=CFG.VECTOR_PATH))
        self.embed = embedding_functions.DefaultEmbeddingFunction()
        self.col = self.client.get_or_create_collection("jarvis", embedding_function=self.embed)

    def add(self, text: str, meta: Dict):
        if self.enabled:
            self.col.add(documents=[text], metadatas=[meta], ids=[str(uuid.uuid4())])

    def search(self, query: str, limit: int = 3):
        if not self.enabled:
            return []
        return self.col.query(query_texts=[query], n_results=limit)["documents"][0]

MEMORY = Memory()

# ================= FILE HASH TRACKING =================
class FileTracker:
    def __init__(self):
        self.hashes = {}
        if os.path.exists(CFG.FILE_HASH_HISTORY):
            try:
                with open(CFG.FILE_HASH_HISTORY, "r") as f:
                    self.hashes = json.load(f)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception("Failed to load file hash history: %s", e)
                self.hashes = {}

    def _compute_hash(self, path):
        try:
            with open(path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Failed to compute hash for %s: %s", path, e)
            return None

    def changed(self, path):
        old_h = self.hashes.get(path)
        new_h = self._compute_hash(path)
        if new_h:
            self.hashes[path] = new_h
            self._save()
        return old_h != new_h

    def _save(self):
        with open(CFG.FILE_HASH_HISTORY, "w") as f:
            json.dump(self.hashes, f, indent=2)

TRACKER = FileTracker()

# ================= EXECUTOR (VENV AWARE) =================
class Executor:
    async def shell(self, cmd: str) -> str:
        # 1. Security Check: Strict Allowlist
        from core.security_system import InputValidator
        allowed_cmds = ["git", "ls", "pip", "python", "mkdir", "cat", "rm", "mv", "cp", "echo", "pwd", "whoami", "uname", "hostname", "date", "uptime", "df", "free", "ps", "top"]
        validator = InputValidator()
        if not validator.validate_command(cmd, allowed_cmds):
            EVENTS.emit(f"🛡 BLOCKED ▶ {cmd}")
            return "⚠ Blocked: Command not in allowlist or contains unauthorized patterns."

        # 2. Venv Injection
        prefix = ""
        if os.path.exists("venv_temp"):
            if platform.system() == "Windows":
                prefix = "venv_temp\\Scripts\\"
            else:
                prefix = "venv_temp/bin/"

        # Ensure pip/python use the venv
        if cmd.startswith("pip ") or cmd.startswith("python "):
            full_cmd = f"{prefix}{cmd}"
        else:
            full_cmd = cmd # Normal system commands like git, ls

        EVENTS.emit(f"🖥 SHELL ▶ {full_cmd}")

        # 3. Execution
        kwargs = {}
        if platform.system() == "Windows":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            kwargs["preexec_fn"] = os.setsid

        try:
            # SECURITY MITIGATION: Switched to exec instead of shell
            import shlex
            cmd_args = shlex.split(full_cmd)
            # Fix: Ensure cmd_args is not empty before execution
            if not cmd_args:
                 return {"success": False, "error": "Empty command string"}

            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                **kwargs
            )
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=30.0
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return {"success": False, "error": "Command timed out after 30s"}
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.exception("Error in shell execution: %s", e)
            raise

        output = (stdout + stderr).decode(errors="ignore")

        # 4. Auto-Install Missing Modules
        m = re.search(r"No module named '([^']+)'", output)
        if m:
            pkg = m.group(1)
            EVENTS.emit(f"📦 AUTO-INSTALL ▶ {pkg}")
            await self.shell(f"pip install {pkg}")
            return await self.shell(cmd) # Retry original command
            
        return output

    async def write(self, path: str = None, content: str = "", **kwargs):
        # Agar AI 'file' bhej de 'path' ki jagah, toh usay handle karo
        final_path = path or kwargs.get('file')
        if not final_path:
            return "Error: No path or file provided."
            
        os.makedirs(os.path.dirname(final_path) or ".", exist_ok=True)
        async with aiofiles.open(final_path, "w", encoding="utf-8") as f:
            await f.write(content)
        EVENTS.emit(f"✍ FILE ▶ {final_path}")
        TRACKER.changed(final_path)
        return f"Successfully written to {final_path}"

    async def read(self, path: str) -> str:
        try:
            async with aiofiles.open(path, "r", encoding="utf-8") as f:
                return await f.read()
        except FileNotFoundError:
            return "Error: File not found."

    async def docker_run(self, code_path: str, requirements: list = []):
        from core.autonomy_guard import require_autonomy
        require_autonomy("docker_run")

        if docker is None:
            return "⚠ Docker SDK not installed"
        client = docker.from_env()
        abs_path = os.path.abspath(code_path)
        req_file = None
        cmds = []
        if requirements:
            req_file = abs_path + "_reqs.txt"
            with open(req_file, "w") as f:
                f.write("\n".join(requirements))
            cmds.append(f"pip install -r /workspace/{os.path.basename(req_file)}")
        cmds.append(f"python /workspace/{os.path.basename(code_path)}")
        full_cmd = " && ".join(cmds)

        try:
            container = client.containers.run(
                CFG.DOCKER_IMAGE,
                full_cmd,
                volumes={os.path.dirname(abs_path): {'bind': '/workspace', 'mode':'rw'}},
                detach=True,
                mem_limit="512m"
            )
            container.wait()
            logs = container.logs().decode()
            container.remove()
            if req_file and os.path.exists(req_file):
                os.remove(req_file)
            return logs
        except Exception as e:
            return f"Docker Error: {str(e)}"

EXEC = Executor()

# ================= CONTEXT PINNING =================
def append_ctx(ctx: str, new: str, max_len: int = CFG.CONTEXT_MAX) -> str:
    # Pin the first 1000 chars (Goal/System Prompt) so it never gets deleted
    header = ctx[:1000] if len(ctx) > 1000 else ctx
    body = ctx[1000:] + new
    
    if len(body) > max_len:
        body = body[-(max_len - len(header)):]
    return header + body

# ================= AST PARSER =================
def parse_python_file(path: str) -> Dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read())
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        return {"classes": classes, "functions": functions}
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Failed to parse Python file %s: %s", path, e)
        return {}

# ================= AI CORE (ROBUST) =================
class AI:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY")) if Groq else None

    def extract_json(self, text: str):
        # 1. Try finding ```json ... ``` block
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception("Failed to parse JSON from code block: %s", e)
                pass

        # 2. Try finding raw JSON structure { ... }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            try: return json.loads(match.group(1))
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.exception("Failed to parse JSON from raw structure: %s", e)
                pass

        return None

    async def call(self, system: str, user: str) -> Optional[Dict]:
        if not self.client: return None
        EVENTS.emit("🧠 AI THINKING")
        await asyncio.sleep(1.0) # Rate limit protection
        try:
            res = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=CFG.MODEL,
                temperature=0,
                messages=[
                    {"role":"system","content":system + "\nIMPORTANT: Return ONLY valid JSON. No markdown explanation."},
                    {"role":"user","content":user}
                ],
                response_format={"type": "json_object"}
            )
            txt = res.choices[0].message.content
            return self.extract_json(txt)
        except Exception as e:
            EVENTS.emit(f"❌ API ERROR: {str(e)}")
            return None

AI_CORE = AI()

# ================= AGENTS =================
class Agents:
    async def pm(self, ctx: str, goal: str):
        EVENTS.emit("📋 PM: Planning DAG milestones...")
        sys = "You are a Project Manager. Break the goal into milestones. Each milestone MUST have 'task' and 'depends_on' (list of previous task names)."
        user = ctx + f"\nGoal: {goal}\nJSON Format: {{\"milestones\": [ {{\"task\": \"T1\", \"depends_on\": [], \"details\": \"...\"}} ]}}"
        return await AI_CORE.call(sys, user)

    async def dev(self, ctx: str, task: str, error: str = ""):
        EVENTS.emit(f"👨‍💻 DEV: Working on '{task}'")
        sys = (
            "You are a Senior Engineer. Available tools: read, write, shell, docker. "
            "IMPORTANT: If you have already executed a command and got the result, DO NOT repeat it. "
            "If the task is done, return 'actions': [] immediately. "
            "Tool 'write' takes ONLY 'path' and 'content'. No 'file' arg."
        )
        msg = f"Task: {task}"
        if error: msg += f"\nLAST ERROR: {error}\nFix this error."
        return await AI_CORE.call(sys, ctx + "\n" + msg)

    async def qa(self, ctx: str, logs: str):
        EVENTS.emit("🧪 QA: Analyzing error...")
        return await AI_CORE.call(
            "You are a QA Engineer. Suggest a fix for the error.", 
            ctx + f"\nLOGS:\n{logs}\nJSON Format: {{\"actions\": [ ... fix actions ... ]}}"
        )

AGENTS = Agents()

# ================= MAIN JARVIS LOOP =================
@register_module(name="jarvis_core", metadata={"tier": "root"})
class Jarvis:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.loop = None
        self.fs_graph_file = "graph_map.json"
        self.workers = []

    def get_execution_order(self, milestones):
        # Simple dependency sorter
        ordered = []
        visited = set()
        def visit(m_name):
            if m_name in visited: return
            visited.add(m_name)
            # Find the milestone object
            m_obj = next((x for x in milestones if x['task'] == m_name), None)
            if m_obj and 'depends_on' in m_obj:
                for dep in m_obj['depends_on']:
                    visit(dep)
            ordered.append(m_name)
        
        for m in milestones:
            visit(m['task'])
        return ordered
    
    async def add_goal(self, goal: str):
        EVENTS.emit(f"🎯 NEW GOAL ▶ {goal}")
        MEMORY.add(goal, {"type": "goal"})
        await self.queue.put(goal)

        # Swarm Scaling: If queue is deep, spawn temporary worker
        if self.queue.qsize() > 2 and len(self.workers) < 10:
            EVENTS.emit(f"🐝 SWARM SCALING ▶ Spawning dynamic worker")
            worker_task = asyncio.create_task(self.worker())
            self.workers.append(worker_task)

    async def save_state(self, ctx: str, task_name: str, status: str):
        """Saves checkpoint to disk"""
        state = {
            "last_task": task_name,
            "status": status,
            "timestamp": str(datetime.now()),
            "partial_context": ctx[-3000:]
        }
        async with aiofiles.open(CFG.CHECKPOINT_FILE, "w") as f:
            await f.write(json.dumps(state, indent=2))

    async def worker(self):
        while True:
            goal = await self.queue.get()
            try:
                await self.run_goal(goal)
            except Exception as e:
                EVENTS.emit(f"💥 WORKER CRASH: {str(e)}")
            finally:
                self.queue.task_done()

    async def run_goal(self, goal: str):
        # 1. Initialize Context
        global_ctx = f"--- GOAL ---\n{goal}\n\n"
        past = MEMORY.search(goal)
        if past: global_ctx += f"MEMORY: {past}\n"

        # 2. Analyze Environment
        files = [f for f in os.listdir(".") if f.endswith(".py")]
        graph = {f: parse_python_file(f) for f in files}
        global_ctx += f"FILES: {json.dumps(graph)}\n"

        # 3. Plan
        plan = await AGENTS.pm(global_ctx, goal)
        if not plan or "milestones" not in plan:
            EVENTS.emit("❌ Planning Failed")
            return

        milestones = plan.get("milestones", [])
        
        # 4. Execute Milestones (Sequential)
        for m in milestones:
            task = m.get('task', 'Unknown')
            EVENTS.emit(f"🚩 MILESTONE START: {task}")
            
            heal = 0
            last_error = ""
            last_actions = None
            
            # Healing Loop
            while heal < CFG.MAX_HEAL:
                await self.save_state(global_ctx, task, f"Cycle {heal}")
                
                # Ask Dev
                dev_res = await AGENTS.dev(global_ctx, task, last_error)
                if not dev_res:
                    heal += 1; continue
                
                actions = dev_res.get("actions", [])
                
                # --- LOOP PROTECTION BLOCK (ADD THIS) ---
                if actions and actions == last_actions:
                    EVENTS.emit("⚠️ LOOP DETECTED: AI is repeating the same commands. Breaking milestone.")
                    break
                last_actions = actions 
                # ----------------------------------------
                
                # Completion Check
                if not actions:
                    EVENTS.emit(f"✅ Milestone '{task}' Complete")
                    break # Break Healing Loop, move to next Milestone
                
                # Action Execution Loop
                action_failed = False
                for action in actions:
                    tool = action.get("tool")
                    args = action.get("args", {})
                    output = ""
                    
                    try:
                        if tool == "shell": output = await EXEC.shell(**args)
                        elif tool == "write": await EXEC.write(**args); output = "Written."
                        elif tool == "read": output = await EXEC.read(**args)
                        elif tool == "docker": output = await EXEC.docker_run(**args)
                        
                        global_ctx = append_ctx(global_ctx, f"\n[Tool: {tool}] > {output[:500]}")
                        
                        # Soft Error Detection
                        if "error" in output.lower() or "traceback" in output.lower():
                            raise Exception(output[:200])

                    except Exception as e:
                        EVENTS.emit(f"⚠️ Tool Failed: {str(e)}")
                        last_error = str(e)
                        
                        # Call QA for specific fix
                        qa_res = await AGENTS.qa(global_ctx, last_error)
                        if qa_res and "actions" in qa_res:
                            # Prepend QA actions to next dev cycle context (or handle immediately)
                            global_ctx += f"\nQA SUGGESTION: {json.dumps(qa_res)}\n"
                        
                        action_failed = True
                        break # Break Action Loop
                
                if action_failed:
                    heal += 1 # Retry Healing Loop with error context
                else:
                    # All actions succeeded in this batch, check with Dev again in next loop
                    # OR if Dev is smart, it returns empty list next time.
                    last_error = "" 
                    # Don't break here, let loop restart. Dev will say "actions: []" if truly done.

            if heal >= CFG.MAX_HEAL:
                EVENTS.emit(f"🛑 Milestone '{task}' Failed after max retries.")
                break # Stop Plan execution

        EVENTS.emit("🏆 ALL TASKS PROCESSED.")
        await self.save_state(global_ctx, "COMPLETED", "Done")

CORE = Jarvis()

# ================= WATCHER HANDLER =================
class Watcher(FileSystemEventHandler):
    def __init__(self):
        self.last_run = 0

    def on_modified(self, event):
        if event.src_path.endswith(CFG.GOAL_FILE):
            now = time.time()
            if now - self.last_run > 2:  # 2 second ka gap
                self.last_run = now
                asyncio.run_coroutine_threadsafe(self.add_goal_from_file(), CORE.loop)

    async def add_goal_from_file(self):
        async with aiofiles.open(CFG.GOAL_FILE, mode='r') as f:
            c = (await f.read()).strip()
            if c: await CORE.add_goal(c)

# ================= FASTAPI & WATCHER =================
app = FastAPI()

@app.get("/")
def ui():
    return HTMLResponse("""
    <body style="background:black;color:#00ffcc;font-family:monospace;padding:20px">
    <h3>JARVIS V3.2 CONTROL</h3>
    <div id="log" style="white-space:pre-wrap;"></div>
    <script>
    const log=document.getElementById('log');
    const es=new EventSource('/events');
    es.onmessage=e=>{
        const div = document.createElement('div');
        div.textContent = e.data;
        log.appendChild(div);
        window.scrollTo(0, document.body.scrollHeight);
    };
    </script>
    </body>
    """)

@app.get("/events")
def events():
    return StreamingResponse(EVENTS.stream(), media_type="text/event-stream")

# ================= ENTRY POINT =================
if __name__ == "__main__":
    async def main():
        CORE.loop = asyncio.get_running_loop()
        
        # Cleanup locks
        if os.path.exists("LOCK"): os.remove("LOCK")
        
        # Workers
        for _ in range(CFG.MAX_CONCURRENT):
            worker_task = asyncio.create_task(CORE.worker())
            CORE.workers.append(worker_task)

        # Initialize Heartbeat Registry
        try:
            from core.registry import registry
            EVENTS.emit(f"💓 SYSTEM REGISTRY ACTIVE: {registry.get_registry_stats()['total_modules']} modules")
        except Exception as e:
            EVENTS.emit(f"⚠️ Registry Init Failed: {e}")

        # Watcher
        obs = Observer()
        handler = Watcher()
        obs.schedule(handler, ".", recursive=False)
        obs.start()

        # Initialize Autonomous Feedback Loop
        try:
            from core.self_monitor import SelfMonitor
            from core.self_evolving_architecture import SEAController
            from core.closed_feedback_loop import initialize_feedback

            monitor = SelfMonitor()
            sea = SEAController(CORE)
            f_loop = initialize_feedback(monitor, sea)
            CORE.loop.create_task(f_loop.start())
            EVENTS.emit("🧠 AUTONOMOUS FEEDBACK LOOP ACTIVE")
        except Exception as e:
            EVENTS.emit(f"⚠️ Feedback Loop Failed to Start: {e}")

        EVENTS.emit("🚀 JARVIS SYSTEM ONLINE")

        # Load Checkpoint/Goal
        if os.path.exists(CFG.GOAL_FILE):
             async with aiofiles.open(CFG.GOAL_FILE, mode='r') as f:
                c = (await f.read()).strip()
                if c: await CORE.add_goal(c)

        # Server
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="error")
        server = uvicorn.Server(config)
        await server.serve()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")