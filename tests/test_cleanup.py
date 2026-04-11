import os
import shutil
import tempfile
import pytest
from jarvis import clean_root

def test_clean_root():
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create some files to move
        files_to_move = [
            "test.log",
            "notes.md",
            "todo.txt",
            "image.png",
            "photo.jpg",
            "icon.svg",
        ]

        for f in files_to_move:
            with open(os.path.join(tmp_dir, f), "w") as fp:
                fp.write("content")

        # Create files to keep (safelist)
        files_to_keep = [
            "jarvis.py",
            "main.py",
            ".env",
            "README.md",
            "requirements.txt"
        ]

        for f in files_to_keep:
            with open(os.path.join(tmp_dir, f), "w") as fp:
                fp.write("content")

        # Create a .py file that is NOT in safelist but should be skipped anyway
        with open(os.path.join(tmp_dir, "other_script.py"), "w") as fp:
            fp.write("content")

        # Run clean_root
        clean_root(tmp_dir)

        # Verify moves
        assert os.path.exists(os.path.join(tmp_dir, "logs", "test.log"))
        assert os.path.exists(os.path.join(tmp_dir, "docs/archive", "notes.md"))
        assert os.path.exists(os.path.join(tmp_dir, "docs/archive", "todo.txt"))
        assert os.path.exists(os.path.join(tmp_dir, "data/media", "image.png"))
        assert os.path.exists(os.path.join(tmp_dir, "data/media", "photo.jpg"))
        assert os.path.exists(os.path.join(tmp_dir, "data/media", "icon.svg"))

        # Verify kept files
        for f in files_to_keep:
            assert os.path.exists(os.path.join(tmp_dir, f))

        # Verify other .py file is kept
        assert os.path.exists(os.path.join(tmp_dir, "other_script.py"))

        # Verify old files are gone
        for f in files_to_move:
            assert not os.path.exists(os.path.join(tmp_dir, f))
