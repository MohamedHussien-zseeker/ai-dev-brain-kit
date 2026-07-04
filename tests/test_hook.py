"""Tests for brain/commands/hook.py — Claude stop hook."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from brain.commands.hook import process_stop_event, install_hook, uninstall_hook


def _make_config(tmp: str) -> dict:
    vault = Path(tmp) / "Brain"
    for sub in ("00-Inbox", "01-Daily", "02-Projects", "03-Decisions", "04-Knowledge", "05-Prompts", "05-Logs", "_templates"):
        (vault / sub).mkdir(parents=True)
    return {
        "version": 1,
        "vaultPath": str(vault),
        "provider": "openai-compatible",
        "baseUrl": "",
        "model": "",
        "captureMode": "approval-required",
    }


def _valid_event() -> dict:
    return {
        "type": "stop",
        "session_id": "sess_abc123",
        "summary": "Fixed auth race condition",
        "key_decisions": ["Use mutex instead of channel"],
        "follow_up": ["Write tests for edge cases"],
        "project": "savesync",
    }


def test_process_valid_event_saves_log():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _make_config(tmp)
        event = _valid_event()
        target = process_stop_event(cfg, event)
        assert target.is_file()
        content = target.read_text()
        assert "Fixed auth race condition" in content
        assert "Use mutex instead of channel" in content
        assert "Write tests for edge cases" in content
        assert "savesync" in content


def test_process_event_does_not_store_full_transcript():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _make_config(tmp)
        event = _valid_event()
        # Simulate a full transcript field that should NOT be stored
        event["transcript"] = "this is the full conversation that should never be saved"
        event["messages"] = [{"role": "user", "content": "secret"}, {"role": "assistant", "content": "more secrets"}]
        target = process_stop_event(cfg, event)
        content = target.read_text()
        assert "full conversation" not in content
        assert "secret" not in content
        assert "more secrets" not in content
        # But the summary should still be there
        assert "Fixed auth race condition" in content


def test_process_malformed_events():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _make_config(tmp)
        result = process_stop_event(cfg, {"not": "valid"})
        assert result is None


def test_process_empty_event():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _make_config(tmp)
        result = process_stop_event(cfg, {})
        assert result is None


def test_duplicate_event_does_not_re_save():
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _make_config(tmp)
        event = _valid_event()
        target1 = process_stop_event(cfg, event)
        target2 = process_stop_event(cfg, event)
        assert target1 == target2  # Same path
        logs = list(Path(cfg["vaultPath"]).glob("05-Logs/*.md"))
        assert len(logs) == 1  # Only one file


def test_event_minimal_fields():
    """Only session_id is required; missing summary/follow_up is OK."""
    with tempfile.TemporaryDirectory() as tmp:
        cfg = _make_config(tmp)
        event = {"session_id": "sess_minimal"}
        target = process_stop_event(cfg, event)
        assert target.is_file()
        content = target.read_text()
        assert "sess_minimal" in content


def test_install_hook_creates_claude_config():
    with tempfile.TemporaryDirectory() as tmp:
        claude_dir = Path(tmp) / ".claude"
        claude_dir.mkdir(parents=True)
        claude_json = claude_dir / "claude.json"
        # Mock the home directory
        with patch("brain.commands.hook.CLAUDE_CONFIG_PATH", claude_json):
            result = install_hook("/path/to/brain")
            assert result is True
            assert claude_json.is_file()
            config = json.loads(claude_json.read_text())
            assert "stopHook" in config
            assert "/path/to/brain" in config["stopHook"]["command"]


def test_install_hook_merges_existing_config():
    with tempfile.TemporaryDirectory() as tmp:
        claude_dir = Path(tmp) / ".claude"
        claude_dir.mkdir(parents=True)
        claude_json = claude_dir / "claude.json"
        claude_json.write_text(json.dumps({"existingKey": "value"}))
        with patch("brain.commands.hook.CLAUDE_CONFIG_PATH", claude_json):
            install_hook("/path/to/brain")
            config = json.loads(claude_json.read_text())
            assert config["existingKey"] == "value"
            assert "stopHook" in config


def test_install_hook_does_not_overwrite_existing_hook():
    """If a stop hook already exists, warn and abort unless --force."""
    with tempfile.TemporaryDirectory() as tmp:
        claude_dir = Path(tmp) / ".claude"
        claude_dir.mkdir(parents=True)
        claude_json = claude_dir / "claude.json"
        claude_json.write_text(json.dumps({
            "existingKey": "value",
            "stopHook": {"command": "existing-hook"},
        }))
        with patch("brain.commands.hook.CLAUDE_CONFIG_PATH", claude_json):
            result = install_hook("/path/to/brain")
            assert result is False  # Aborted
            config = json.loads(claude_json.read_text())
            assert config["stopHook"]["command"] == "existing-hook"  # Unchanged


def test_uninstall_hook_removes_stop_hook():
    with tempfile.TemporaryDirectory() as tmp:
        claude_dir = Path(tmp) / ".claude"
        claude_dir.mkdir(parents=True)
        claude_json = claude_dir / "claude.json"
        claude_json.write_text(json.dumps({
            "existingKey": "value",
            "stopHook": {"command": "/path/to/brain"},
        }))
        with patch("brain.commands.hook.CLAUDE_CONFIG_PATH", claude_json):
            uninstall_hook()
            config = json.loads(claude_json.read_text())
            assert "stopHook" not in config
            assert config["existingKey"] == "value"  # Other keys preserved


def test_uninstall_hook_no_config():
    with tempfile.TemporaryDirectory() as tmp:
        claude_dir = Path(tmp) / ".claude"
        claude_json = claude_dir / "claude.json"
        with patch("brain.commands.hook.CLAUDE_CONFIG_PATH", claude_json):
            result = uninstall_hook()
            assert result is False  # Nothing to remove
