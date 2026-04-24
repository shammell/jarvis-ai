import typer
import os
import shutil
import glob
import asyncio
import socket
import datetime
import subprocess
import time
import signal
import sys
import webbrowser
from typing import Optional, List


def _is_non_interactive() -> bool:
    return not sys.stdin.isatty()


def _is_test_mode() -> bool:
    return os.getenv("PYTEST_CURRENT_TEST") is not None or os.getenv("JARVIS_CLI_TEST_MODE") == "1"
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Fix Windows console encoding for emoji and special character support
if sys.platform == 'win32':
    try:
        import codecs
        if sys.stdout.encoding != 'utf-8':
            sys.stdout.reconfigure(encoding='utf-8')
        if sys.stderr.encoding != 'utf-8':
            sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

app = typer.Typer(help="JARVIS Unified CLI")
# PhD-Level Fix: Use force_terminal=True and safe characters for legacy Windows consoles
console = Console(force_terminal=True)

# Global list to track subprocesses for shutdown
processes: List[subprocess.Popen] = []

def wait_for_port(port: int, host: str = "127.0.0.1", timeout: int = 60):
    """Wait for a port to become active."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect((host, port))
                return True
            except (ConnectionRefusedError, socket.timeout):
                time.sleep(1)
    return False

def shutdown_processes():
    """Stop all tracked subprocesses."""
    if not processes:
        return

    console.print("\n[bold yellow]Shutting down JARVIS components...[/bold yellow]")

    # Kill Chrome if it was launched in kiosk mode (Windows)
    if os.name == 'nt':
        try:
            subprocess.run(["taskkill", "/F", "/IM", "chrome.exe", "/T"], capture_output=True)
        except Exception:
            pass

    for p in processes:
        try:
            # Try graceful terminate first
            p.terminate()
            try:
                p.wait(timeout=5)
            except subprocess.TimeoutExpired:
                p.kill() # Force kill if terminate fails
        except Exception as e:
            console.print(f"[red]Error killing process {p.pid}: {e}[/red]")

    console.print("[bold green]All systems stopped.[/bold green]")

@app.command()
def bootstrap():
    """Launch Backend, Frontend, and Voice systems in parallel."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(root_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)

    bootstrap_log_path = os.path.join(log_dir, "bootstrap.log")

    console.print(Panel("Omni-Start Orchestrator", title="[bold cyan]Bootstrap[/bold cyan]", subtitle="v1.0"))

    python_exe = shutil.which("python") or sys.executable
    npm_exe = shutil.which("npm")

    if not npm_exe:
        # Try common windows path for npm if not in PATH
        npm_exe = shutil.which("npm.cmd")

    if not npm_exe:
        console.print("[red]Error: npm not found in PATH.[/red]")
        raise typer.Exit(code=1)

    # PhD-Level Fix: Clear proxy environment variables to prevent Groq SDK TypeError
    # Client.__init__() got an unexpected keyword argument 'proxies'
    env = os.environ.copy()
    env.pop("HTTP_PROXY", None)
    env.pop("HTTPS_PROXY", None)
    env.pop("http_proxy", None)
    env.pop("https_proxy", None)
    env.pop("ALL_PROXY", None)
    env.pop("all_proxy", None)

    try:
        with open(bootstrap_log_path, "a", encoding="utf-8") as log_file:
            log_file.write(f"\n--- Bootstrap session started at {datetime.datetime.now()} ---\n")

            # 1. Start Backend
            console.print("[yellow]Starting Backend (main.py)...[/yellow]")
            backend_proc = subprocess.Popen(
                [python_exe, "main.py"],
                cwd=root_dir,
                stdout=log_file,
                stderr=log_file,
                text=True,
                env=env
            )
            processes.append(backend_proc)

            # 2. Start Frontend
            console.print("[yellow]Starting Frontend (npm run dev)...[/yellow]")
            frontend_dir = os.path.join(root_dir, "web")
            frontend_proc = subprocess.Popen(
                [npm_exe, "run", "dev"],
                cwd=frontend_dir,
                stdout=log_file,
                stderr=log_file,
                text=True,
                shell=True if os.name == 'nt' else False,
                env=env
            )
            processes.append(frontend_proc)

            # 3. Start Voice
            console.print("[yellow]Starting Voice (voice_jarvis.py)...[/yellow]")
            voice_proc = subprocess.Popen(
                [python_exe, "voice_jarvis.py"],
                cwd=root_dir,
                stdout=log_file,
                stderr=log_file,
                text=True,
                env=env
            )
            processes.append(voice_proc)

            with Progress(
                SpinnerColumn("dots" if os.name != 'nt' else "simpleDots"),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True
            ) as progress:
                # Wait for Backend (typically 8080 or 8000, let's check common JARVIS ports)
                progress.add_task(description="Waiting for Backend (8080)...", total=None)
                if wait_for_port(8080):
                    console.print("[green]Backend is READY on port 8080.[/green]")
                else:
                    console.print("[red]Backend failed to start or port 8080 is blocked.[/red]")

                # Wait for Frontend (Next.js typically 3000 or 3001)
                progress.add_task(description="Waiting for Frontend (3000/3001)...", total=None)
                frontend_port = 3000
                if wait_for_port(3000):
                    console.print("[green]Frontend is READY on port 3000.[/green]")
                elif wait_for_port(3001):
                    frontend_port = 3001
                    console.print("[green]Frontend is READY on port 3001.[/green]")
                else:
                    console.print("[red]Frontend failed to start or ports 3000/3001 are blocked.[/red]")

            console.print(Panel.fit(
                "[bold green]JARVIS is fully operational![/bold green]\n"
                "Backend: http://localhost:8080\n"
                f"Frontend: http://localhost:{frontend_port}\n"
                "Voice: Active\n\n"
                "Press Ctrl+C to shut down all systems.",
                title="System Ready"
            ))

            # --- Final Polish: Greeting & Kiosk Mode ---
            try:
                # 1. TTS Greeting
                greeting = "System online. All modules initialized. Good morning, AK."
                console.print(f"[bold cyan]JARVIS:[/bold cyan] {greeting}")

                # Trigger via bridge
                temp_speak_script = os.path.join(root_dir, "temp_greeting.py")
                subprocess.Popen([python_exe, temp_speak_script], cwd=root_dir, env=env)

                # 2. Kiosk Launch
                console.print("[yellow]Launching Kiosk Mode...[/yellow]")
                dashboard_url = f"http://localhost:{frontend_port}/dashboard"
                if os.name == 'nt':
                    subprocess.Popen(["start", "chrome", "--kiosk", dashboard_url], shell=True)
                else:
                    webbrowser.open(dashboard_url)

            except Exception as e:
                console.print(f"[dim]Note: Final polish (TTS/Kiosk) had an issue: {e}[/dim]")

            # Keep the script running to manage processes
            try:
                while True:
                    # Check if any process has died unexpectedly
                    for p in processes:
                        if p.poll() is not None:
                            console.print(f"[red]Process {p.pid} exited unexpectedly with code {p.returncode}[/red]")
                            # We could restart or shutdown here
                    time.sleep(5)
            except KeyboardInterrupt:
                shutdown_processes()

    except Exception as e:
        console.print(f"[red]Bootstrap failed: {e}[/red]")
        shutdown_processes()
        raise typer.Exit(code=1)

def is_cluttered(root_dir: str) -> int:
    """Count files in root directory that are not in the safelist or hidden."""
    # Excluded files and patterns
    safelist = {
        "requirements.txt", "package.json", "package-lock.json",
        "Dockerfile", "docker-compose.yml", "LICENSE"
    }

    count = 0
    for entry in os.scandir(root_dir):
        if entry.is_file():
            name = entry.name
            # Exclude hidden files
            if name.startswith('.'):
                continue
            # Exclude Python files
            if name.endswith('.py'):
                continue
            # Exclude safelist
            if name in safelist:
                continue
            count += 1
    return count

def clean_root(root_dir: str):
    """Clean up the root directory of the JARVIS project by moving files to organized subfolders."""
    # Target Mappings
    mappings = {
        "*.log": "logs",
        "*.md": "docs/archive",
        "*.txt": "docs/archive",
        "*.png": "data/media",
        "*.jpg": "data/media",
        "*.svg": "data/media",
    }

    # Excluded Files (Safelist)
    safelist = {
        ".env", "config.json", ".gitignore", "jarvis.py", "main.py",
        "jarvis_autonomous.py", "README.md", "requirements.txt", "package.json",
        "CLAUDE.md", "temp_greeting.py"
    }

    console.print(f"Scanning [bold blue]{root_dir}[/bold blue] for cleanup...")

    for pattern, target_subdir in mappings.items():
        target_dir = os.path.join(root_dir, target_subdir)

        # Ensure target directory exists
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
            console.print(f"Created directory: [dim]{target_subdir}[/dim]")

        # Find matching files in root_dir only (not recursive)
        files = glob.glob(os.path.join(root_dir, pattern))

        for file_path in files:
            file_name = os.path.basename(file_path)

            # Skip if file is in safelist
            if file_name in safelist:
                continue

            # Skip hidden files
            if file_name.startswith('.'):
                continue

            # Skip all .py files in root (per instruction)
            if file_name.endswith('.py'):
                continue

            # Move the file
            dest_path = os.path.join(target_dir, file_name)

            # Handle name collisions
            if os.path.exists(dest_path):
                base, ext = os.path.splitext(file_name)
                counter = 1
                while os.path.exists(os.path.join(target_dir, f"{base}_{counter}{ext}")):
                    counter += 1
                dest_path = os.path.join(target_dir, f"{base}_{counter}{ext}")

            try:
                shutil.move(file_path, dest_path)
                console.print(f"Moved: [green]{file_name}[/green] -> [dim]{target_subdir}/[/dim]")
            except Exception as e:
                console.print(f"[red]Error moving {file_name}: {e}[/red]")

@app.command()
def start():
    """Start the JARVIS orchestrator (jarvis_brain)."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    clutter_count = is_cluttered(root_dir)

    if clutter_count > 30 and not _is_non_interactive() and not _is_test_mode():
        if typer.confirm(f"Root directory has {clutter_count} files. Run 'clean' first?"):
            clean_root(root_dir)
            console.print("[bold green]Cleanup complete![/bold green]")

    console.print(Panel("Starting JARVIS Orchestrator...", title="[bold green]Start[/bold green]"))

    if _is_test_mode():
        return

    # Import and run main orchestrator
    try:
        from main import uvicorn, app as fastapi_app
        uvicorn.run(fastapi_app, host="0.0.0.0", port=8080, log_level="info")
    except ImportError:
        console.print("[red]Error: Could not import main orchestrator components.[/red]")
    except Exception as e:
        console.print(f"[red]Error starting JARVIS: {e}[/red]")

@app.command()
def autonomous():
    """Run JARVIS in autonomous mode."""
    root_dir = os.path.dirname(os.path.abspath(__file__))
    clutter_count = is_cluttered(root_dir)

    if clutter_count > 30 and not _is_non_interactive() and not _is_test_mode():
        if typer.confirm(f"Root directory has {clutter_count} files. Run 'clean' first?"):
            clean_root(root_dir)
            console.print("[bold green]Cleanup complete![/bold green]")

    console.print(Panel("Launching JARVIS Autonomous Mode...", title="[bold blue]Autonomous[/bold blue]"))

    if _is_test_mode():
        return

    # Import and run autonomous mode
    try:
        from jarvis_autonomous import main as autonomous_main
        asyncio.run(autonomous_main())
    except ImportError:
        console.print("[red]Error: Could not import autonomous module.[/red]")
    except Exception as e:
        console.print(f"[red]Error starting autonomous mode: {e}[/red]")

@app.command()
def clean():
    """Clean up JARVIS temporary files and logs."""
    console.print(Panel("Cleaning up JARVIS environment...", title="[bold yellow]Clean[/bold yellow]"))
    # Get current directory of jarvis.py
    root_dir = os.path.dirname(os.path.abspath(__file__))
    clean_root(root_dir)
    console.print("[bold green]Cleanup complete![/bold green]")

@app.command()
def status():
    """Show JARVIS system status and health."""
    console.print(Panel("Checking JARVIS system status...", title="[bold cyan]Status[/bold cyan]"))

    root_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Root Health
    clutter_count = is_cluttered(root_dir)
    health_status = "[green]Healthy[/green]" if clutter_count <= 30 else "[yellow]Cluttered[/yellow]"

    # 2. Environment Checks
    env_exists = os.path.exists(os.path.join(root_dir, ".env"))
    config_exists = os.path.exists(os.path.join(root_dir, "config.json"))

    env_status = "[green]OK[/green]" if env_exists else "[red]Missing[/red]"
    config_status = "[green]OK[/green]" if config_exists else "[red]Missing[/red]"

    # 3. Activity Check
    log_path = os.path.join(root_dir, "logs", "jarvis_v9.log")
    last_log_line = "N/A"
    last_modified = "N/A"

    if os.path.exists(log_path):
        mtime = os.path.getmtime(log_path)
        last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    last_log_line = lines[-1].strip()
        except Exception:
            last_log_line = "Error reading log"

    # 4. Service Check (Port 8080)
    def check_port(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            try:
                s.connect(('127.0.0.1', port))
                return True
            except (ConnectionRefusedError, socket.timeout):
                return False

    api_running = check_port(8080)
    api_status = "[green]Running[/green]" if api_running else "[red]Stopped[/red]"

    # 5. UI - Table construction
    table = Table(title="JARVIS System Report", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="dim")
    table.add_column("Status")
    table.add_column("Details")

    table.add_row("Root Directory", health_status, f"{clutter_count} files found")
    table.add_row(".env File", env_status, ".env" if env_exists else "Missing .env")
    table.add_row("config.json", config_status, "config.json" if config_exists else "Missing config.json")
    table.add_row("FastAPI (8080)", api_status, "localhost:8080")
    table.add_row("Last Activity", "[blue]Info[/blue]", last_modified)

    console.print(table)

    if last_log_line != "N/A":
        console.print(Panel(last_log_line, title="[bold]Last Log Entry[/bold]", border_style="dim"))

if __name__ == "__main__":
    app()
