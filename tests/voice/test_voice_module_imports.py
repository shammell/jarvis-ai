"""Smoke tests for migrated voice modules.

These tests validate that migrated modules in jarvis_project.voice import cleanly
without runtime execution side effects.
"""

import importlib
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


MODULES = [
    "voice.audio_manager",
    "voice.wake_detector",
    "voice.speech_to_text",
    "voice.text_to_speech",
    "voice.voice_bridge",
    "voice.prompt_generator",
    "voice.task_chain",
    "voice.task_chain_executor",
]


def test_voice_modules_import_cleanly():
    imported = []
    for module_name in MODULES:
        module = importlib.import_module(module_name)
        assert module is not None
        imported.append(module_name)

    assert len(imported) == len(MODULES)
