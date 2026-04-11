import subprocess
import sys

def test_cli_help():
    """Verify the CLI responds to --help."""
    result = subprocess.run(
        [sys.executable, "C:/Users/AK/jarvis_project/jarvis.py", "--help"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "JARVIS Unified CLI" in result.stdout
    assert "start" in result.stdout
    assert "autonomous" in result.stdout
    assert "clean" in result.stdout
    assert "status" in result.stdout

def test_cli_commands():
    """Verify basic command stubs respond."""
    for command in ["start", "autonomous", "clean", "status"]:
        result = subprocess.run(
            [sys.executable, "C:/Users/AK/jarvis_project/jarvis.py", command],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert command.capitalize() in result.stdout
