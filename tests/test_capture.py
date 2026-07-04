"""Tests for brain capture commands."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from brain.commands.capture import capture_note, capture_today
from brain.config import BrainConfig


def _make_config(vault: Path) -> BrainConfig:
    return BrainConfig(
        version=1,
        vaultPath=str(vault),
        provider="openai-compatible",
        baseUrl="",
        model="",
        captureMode="approval-required",
    )


def test_note_creates_file_in_inbox():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        (vault / "00-Inbox").mkdir()
        cfg = _make_config(vault)
        capture_note(cfg, "Fixed auth race condition")
        inbox = vault / "00-Inbox"
        files = list(inbox.glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "Fixed auth race condition" in content


def test_note_content_has_frontmatter():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        (vault / "00-Inbox").mkdir()
        cfg = _make_config(vault)
        capture_note(cfg, "Test note content")
        file = next((vault / "00-Inbox").glob("*.md"))
        content = file.read_text()
        assert content.startswith("---")
        assert "---" in content[3:]
        assert "type: note" in content


def test_note_filename_is_portable():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        (vault / "00-Inbox").mkdir()
        cfg = _make_config(vault)
        capture_note(cfg, "special chars: / \\ : * ? \" < > |")
        file = next((vault / "00-Inbox").glob("*.md"))
        # Should not contain illegal filename characters
        name = file.stem
        assert "/" not in name
        assert "\\" not in name


def test_today_creates_daily_log():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        (vault / "01-Daily").mkdir()
        cfg = _make_config(vault)

        # Simulate answering prompts
        with patch("builtins.input", side_effect=["auth refactor", "done and tested"]):
            capture_today(cfg)

        daily = vault / "01-Daily"
        files = list(daily.glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "## Focus" in content
        assert "auth refactor" in content
        assert "done and tested" in content


def test_today_appends_to_existing_daily():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        daily = vault / "01-Daily"
        daily.mkdir()
        cfg = _make_config(vault)

        with patch("builtins.input", side_effect=["first session", "in progress"]):
            capture_today(cfg)

        with patch("builtins.input", side_effect=["second session", "finished"]):
            capture_today(cfg)

        files = list(daily.glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text()
        assert "first session" in content
        assert "second session" in content


def test_today_no_input_still_creates_file():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        (vault / "01-Daily").mkdir()
        cfg = _make_config(vault)

        with patch("builtins.input", return_value=""):
            capture_today(cfg)

        daily = vault / "01-Daily"
        files = list(daily.glob("*.md"))
        assert len(files) == 1
