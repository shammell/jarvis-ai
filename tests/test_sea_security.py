import pytest
import asyncio
from core.sea_security_controller import sea_security_controller

def test_sea_security_controller():
    # Test low-risk modification
    result = sea_security_controller.validate_modification(
        "test_file.py",
        "def hello():\n    print('Hello world')"
    )
    assert result['allowed'] is True
    assert result['risk_score'] < 5

    # Test high-risk modification (forbidden call)
    result = sea_security_controller.validate_modification(
        "core/llm_provider.py",
        "import os\nos.system('rm -rf /')"
    )
    assert result['allowed'] is False
    assert "Forbidden call" in result['reason']

    # Test high-risk modification (core file)
    result = sea_security_controller.validate_modification(
        "jarvis_brain.py",
        "import subprocess\nsubprocess.run(['ls'])"
    )
    # core file + subprocess = high risk
    assert result['risk_score'] >= 8
    assert result['allowed'] is False
