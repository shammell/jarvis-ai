import subprocess
import sys
import os


def _cli_env():
    env = os.environ.copy()
    env["JARVIS_CLI_TEST_MODE"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env

def test_cli_help():
    """Verify the CLI responds to --help."""
    result = subprocess.run(
        [sys.executable, "C:/Users/AK/jarvis_project/jarvis.py", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=_cli_env()
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
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_cli_env()
        )
        assert result.returncode == 0
        assert command.capitalize() in result.stdout
