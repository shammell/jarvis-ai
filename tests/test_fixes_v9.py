import pytest
import asyncio
from jarvis_brain import Executor
from core.security_system import InputValidator

@pytest.mark.asyncio
async def test_shell_allowlist():
    executor = Executor()

    # Test allowed command
    result = await executor.shell("ls")
    assert "⚠ Blocked" not in str(result)

    # Test disallowed command
    result = await executor.shell("rm -rf /")
    assert "⚠ Blocked" in str(result)

    # Test unauthorized pattern
    result = await executor.shell("ls; cat /etc/passwd")
    assert "⚠ Blocked" in str(result)

@pytest.mark.asyncio
async def test_subprocess_exec_fix():
    executor = Executor()
    # If the bug was present, this would likely raise a ValueError or TypeError
    # depending on the asyncio version and platform
    result = await executor.shell("echo 'test'")
    assert "test" in result.strip().lower()
