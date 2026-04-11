import typer
import os
import shutil
import glob
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="JARVIS Unified CLI")
console = Console()

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
    console.print(Panel("Starting JARVIS Orchestrator...", title="[bold green]Start[/bold green]"))
    # Implementation will be added later

@app.command()
def autonomous():
    """Run JARVIS in autonomous mode."""
    console.print(Panel("Launching JARVIS Autonomous Mode...", title="[bold blue]Autonomous[/bold blue]"))
    # Implementation will be added later

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
    # Implementation will be added later

if __name__ == "__main__":
    app()
