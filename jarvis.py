import typer
import os
import shutil
import glob
import asyncio
import socket
import datetime
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(help="JARVIS Unified CLI")
console = Console()

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
        "CLAUDE.md"
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

    if clutter_count > 30:
        if typer.confirm(f"Root directory has {clutter_count} files. Run 'clean' first?"):
            clean_root(root_dir)
            console.print("[bold green]Cleanup complete![/bold green]")

    console.print(Panel("Starting JARVIS Orchestrator...", title="[bold green]Start[/bold green]"))

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

    if clutter_count > 30:
        if typer.confirm(f"Root directory has {clutter_count} files. Run 'clean' first?"):
            clean_root(root_dir)
            console.print("[bold green]Cleanup complete![/bold green]")

    console.print(Panel("Launching JARVIS Autonomous Mode...", title="[bold blue]Autonomous[/bold blue]"))

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
