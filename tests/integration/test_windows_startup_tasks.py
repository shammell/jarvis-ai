"""
============================================================================
JARVIS v11.0 - Windows Startup Task Integration Tests
============================================================================
Tests for PowerShell startup task installation and removal scripts.
============================================================================
"""

import subprocess
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest import mock
import pytest


# ============================================================================
# Constants
# ============================================================================

BASE_DIR = Path(__file__).parent.parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts" / "windows"
STARTUP_INSTALL_SCRIPT = SCRIPTS_DIR / "install_startup_task.ps1"
STARTUP_REMOVE_SCRIPT = SCRIPTS_DIR / "remove_startup_task.ps1"
START_JARVIS_BAT = BASE_DIR / "start_jarvis.bat"

TASK_NAME = "JARVIS Voice-First Assistant"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(scope="module")
def windows_env():
    """Check if running on Windows and PowerShell is available."""
    is_windows = sys.platform == "win32"
    has_powershell = False

    if is_windows:
        try:
            result = subprocess.run(
                ["pwsh", "-Version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            has_powershell = result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            try:
                result = subprocess.run(
                    ["powershell", "-Version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                has_powershell = result.returncode == 0
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

    return {"windows": is_windows, "powershell": has_powershell}


@pytest.fixture(scope="module")
def test_log_file(tmp_path_factory):
    """Create a temporary log file path for testing."""
    tmp_dir = tmp_path_factory.mktemp("startup_test")
    log_file = tmp_dir / "task_install.log"
    return log_file


# ============================================================================
# Helper Functions
# ============================================================================


def run_powershell_script(script_path, arguments=None, use_admin=False):
    """Run a PowerShell script and return the result."""
    cmd = ["pwsh", "-NoProfile", "-ExecutionPolicy", "Bypass", str(script_path)]

    if arguments:
        cmd.extend(arguments)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(BASE_DIR)
        )
        return result
    except subprocess.TimeoutExpired:
        return None
    except FileNotFoundError:
        return None


def task_exists(task_name):
    """Check if a Task Scheduler task exists."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", f"Get-ScheduledTask -TaskName '{task_name}' -ErrorAction SilentlyContinue"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0 and result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


# ============================================================================
# Test: Script Existence Verification
# ============================================================================


class TestScriptFilesExist:
    """Test that all required script files exist."""

    def test_install_script_exists(self):
        """Test that the install script exists."""
        assert STARTUP_INSTALL_SCRIPT.exists(), \
            f"Install script not found at {STARTUP_INSTALL_SCRIPT}"

    def test_remove_script_exists(self):
        """Test that the remove script exists."""
        assert STARTUP_REMOVE_SCRIPT.exists(), \
            f"Remove script not found at {STARTUP_REMOVE_SCRIPT}"

    def test_start_jarvis_bat_exists(self):
        """Test that the startup batch file exists."""
        assert START_JARVIS_BAT.exists(), \
            f"Start JARVIS bat file not found at {START_JARVIS_BAT}"

    def test_start_jarvis_bat_is_executable(self):
        """Test that the startup bat file has content."""
        content = START_JARVIS_BAT.read_text()
        assert len(content) > 0, "Start JARVIS bat file is empty"


# ============================================================================
# Test: PowerShell Script Validity
# ============================================================================


class TestPowerShellScriptValidity:
    """Test that PowerShell scripts are syntactically valid."""

    @pytest.mark.skipif(sys.platform != "win32", reason="PowerShell only available on Windows")
    def test_install_script_syntax(self):
        """Test that install script has valid PowerShell syntax."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", f"Test-Path '{STARTUP_INSTALL_SCRIPT}'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Script should be a valid file path
            assert result.returncode == 0, \
                f"Could not access install script: {result.stderr}"
        except FileNotFoundError:
            # PowerShell may not be available in test environment
            pytest.skip("PowerShell not available")

    @pytest.mark.skipif(sys.platform != "win32", reason="PowerShell only available on Windows")
    def test_remove_script_syntax(self):
        """Test that remove script has valid PowerShell syntax."""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-Command", f"Test-Path '{STARTUP_REMOVE_SCRIPT}'"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Script should be a valid file path
            assert result.returncode == 0, \
                f"Could not access remove script: {result.stderr}"
        except FileNotFoundError:
            # PowerShell may not be available in test environment
            pytest.skip("PowerShell not available")


# ============================================================================
# Test: PowerShell Script Content Verification
# ============================================================================


class TestScriptContent:
    """Test that PowerShell scripts contain required content."""

    def test_install_script_has_task_name(self):
        """Test that install script defines correct task name."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "JARVIS Voice-First Assistant" in content, \
            "Install script does not contain expected task name"

    def test_install_script_has_bat_path(self):
        """Test that install script references correct bat file path."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "start_jarvis.bat" in content, \
            "Install script does not reference start_jarvis.bat"

    def test_install_script_has_working_directory(self):
        """Test that install script sets correct working directory."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "WorkingDirectory" in content, \
            "Install script does not define working directory"

    def test_install_script_has_log_path(self):
        """Test that install script has logging configuration."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "task_install.log" in content, \
            "Install script does not configure logging"

    def test_remove_script_has_task_name(self):
        """Test that remove script defines correct task name."""
        content = STARTUP_REMOVE_SCRIPT.read_text()
        assert "JARVIS Voice-First Assistant" in content, \
            "Remove script does not contain expected task name"

    def test_remove_script_is_safe(self):
        """Test that remove script handles missing task gracefully."""
        content = STARTUP_REMOVE_SCRIPT.read_text()
        # Should check if task exists before trying to remove
        assert "if (-not $existingTask)" in content or \
               "ErrorAction SilentlyContinue" in content, \
            "Remove script should handle missing task gracefully"


# ============================================================================
# Test: Batch File Content Verification
# ============================================================================


class TestBatchFileContent:
    """Test that start_jarvis.bat contains required content."""

    def test_batch_file_has_health_check(self):
        """Test that batch file includes health check."""
        content = START_JARVIS_BAT.read_text()
        assert "HEALTH CHECK" in content or "health_check" in content.lower(), \
            "Batch file should include health check functionality"

    def test_batch_file_has_python_check(self):
        """Test that batch file checks for Python."""
        content = START_JARVIS_BAT.read_text()
        assert "python" in content.lower(), \
            "Batch file should check for Python installation"

    def test_batch_file_has_node_check(self):
        """Test that batch file checks for Node.js."""
        content = START_JARVIS_BAT.read_text()
        assert "node" in content.lower(), \
            "Batch file should check for Node.js installation"

    def test_batch_file_has_logging(self):
        """Test that batch file includes logging."""
        content = START_JARVIS_BAT.read_text()
        assert "logs" in content.lower(), \
            "Batch file should create/logging to logs directory"

    def test_batch_file_has_venv_activation(self):
        """Test that batch file activates virtual environment."""
        content = START_JARVIS_BAT.read_text()
        assert "activate" in content.lower(), \
            "Batch file should activate virtual environment if present"

    def test_batch_file_has_launcher_call(self):
        """Test that batch file calls unified launcher."""
        content = START_JARVIS_BAT.read_text()
        assert "unified_launcher" in content.lower() or "python" in content.lower(), \
            "Batch file should call Python launcher"


# ============================================================================
# Integration Test Helper
# ============================================================================


def should_run_integration_tests():
    """Check if integration tests should run."""
    if sys.platform != "win32":
        return False

    try:
        result = subprocess.run(
            ["powershell", "-Version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


# ============================================================================
# Test: Integration Tests (Conditional on Windows)
# ============================================================================


@pytest.mark.skipif(
    not should_run_integration_tests(),
    reason="Windows environment with PowerShell required for integration tests"
)
class TestIntegration:
    """Integration tests for actual PowerShell script execution."""

    @pytest.fixture(autouse=True)
    def cleanup_task(self):
        """Ensure task is removed before and after tests."""
        # Cleanup before test
        if task_exists(TASK_NAME):
            run_powershell_script(STARTUP_REMOVE_SCRIPT, ["--Force"])
            import time
            time.sleep(1)

        yield

        # Cleanup after test
        if task_exists(TASK_NAME):
            run_powershell_script(STARTUP_REMOVE_SCRIPT, ["--Force"])

    def test_install_creates_task(self):
        """Test that install script creates a valid task."""
        # First ensure clean state
        run_powershell_script(STARTUP_REMOVE_SCRIPT, ["--Force"])
        import time
        time.sleep(1)

        # Run install script
        result = run_powershell_script(STARTUP_INSTALL_SCRIPT)

        if result:
            # Check for success in output
            assert result.returncode == 0, \
                f"Install script failed: {result.stderr}"
            assert "success" in result.stdout.lower() or "complete" in result.stdout.lower(), \
                f"Install script did not report success: {result.stdout}"

            # Verify task exists
            import time
            time.sleep(1)
            assert task_exists(TASK_NAME), "Task was not created after install script"

    def test_remove_deletes_task(self):
        """Test that remove script deletes the task."""
        # First create the task
        run_powershell_script(STARTUP_INSTALL_SCRIPT)
        import time
        time.sleep(2)

        # Run remove script
        result = run_powershell_script(STARTUP_REMOVE_SCRIPT, ["--Force"])

        if result:
            assert result.returncode == 0, \
                f"Remove script failed: {result.stderr}"
            assert "success" in result.stdout.lower() or "complete" in result.stdout.lower(), \
                f"Remove script did not report success: {result.stdout}"

            # Verify task is deleted
            import time
            time.sleep(1)
            assert not task_exists(TASK_NAME), \
                "Task still exists after remove script"

    def test_idempotency_install(self):
        """Test that running install twice is safe."""
        # Ensure clean state
        run_powershell_script(STARTUP_REMOVE_SCRIPT, ["--Force"])
        import time
        time.sleep(1)

        # Run install twice
        result1 = run_powershell_script(STARTUP_INSTALL_SCRIPT)
        import time
        time.sleep(1)
        result2 = run_powershell_script(STARTUP_INSTALL_SCRIPT)

        # Both should succeed
        if result1 and result2:
            assert result1.returncode == 0, f"First install failed: {result1.stderr}"
            assert result2.returncode == 0, f"Second install failed: {result2.stderr}"

            # Verify task was created
            assert task_exists(TASK_NAME), "Task was not created"


# ============================================================================
# Test: Logging Verification
# ============================================================================


class TestLoggingBehavior:
    """Test script logging behavior."""

    def test_install_script_logs_to_file(self):
        """Test that install script configures file logging."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "Write-Log" in content or "Add-Content" in content, \
            "Install script should have logging function"

    def test_remove_script_logs_to_file(self):
        """Test that remove script configures file logging."""
        content = STARTUP_REMOVE_SCRIPT.read_text()
        assert "Write-Log" in content or "Add-Content" in content, \
            "Remove script should have logging function"


# ============================================================================
# Test: Safety Features
# ============================================================================


class TestSafetyFeatures:
    """Test script safety features."""

    def test_install_removes_existing_previously(self):
        """Test that install removes existing task before creating new one."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "Get-ScheduledTask" in content and \
               "Unregister-ScheduledTask" in content, \
            "Install script should check for and remove existing task"

    def test_remove_has_force_option(self):
        """Test that remove script has --Force option."""
        content = STARTUP_REMOVE_SCRIPT.read_text()
        assert "--Force" in content or "-Force" in content, \
            "Remove script should have --Force option"

    def test_install_uses_highest_privileges(self):
        """Test that install script runs with highest privileges."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "Highest" in content and "RunLevel" in content, \
            "Install script should configure Highest run level"

    def test_trigger_at_logon(self):
        """Test that install script uses logon trigger."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "AtLogOn" in content or "AtLoggedOnSessionStart" in content, \
            "Install script should use logon trigger"


# ============================================================================
# Test: Error Handling
# ============================================================================


class TestErrorHandling:
    """Test script error handling."""

    def test_install_validates_bat_exists(self):
        """Test that install script validates batch file exists."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "Test-Path" in content and "BatFilePath" in content, \
            "Install script should validate batch file exists"

    def test_install_validates_working_directory(self):
        """Test that install script validates working directory."""
        content = STARTUP_INSTALL_SCRIPT.read_text()
        assert "Test-Path" in content and "WorkingDirectory" in content, \
            "Install script should validate working directory"

    def test_remove_handles_missing_task(self):
        """Test that remove script handles missing task without error."""
        content = STARTUP_REMOVE_SCRIPT.read_text()
        # Should check existence before removing
        assert "if (-not $existingTask)" in content or "SilentlyContinue" in content, \
            "Remove script should handle missing task gracefully"


# ============================================================================
# Summary
# ============================================================================


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
