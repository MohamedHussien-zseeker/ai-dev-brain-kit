"""Tests for brain/commands/context.py — brain context."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from brain.commands.context import build_context


def _make_vault(tmp: str) -> Path:
    vault = Path(tmp) / "Brain"
    for sub in ("00-Inbox", "01-Daily", "02-Projects", "03-Decisions", "04-Knowledge", "05-Prompts", "_templates"):
        (vault / sub).mkdir(parents=True)
    return vault


def _make_config(tmp: str, vault: Path) -> dict:
    return {
        "version": 1,
        "vaultPath": str(vault),
        "provider": "openai-compatible",
        "baseUrl": "",
        "model": "",
        "captureMode": "approval-required",
    }


def test_context_contains_today():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        today_file = vault / "01-Daily" / "2026-07-04.md"
        today_file.write_text("# Today\n\nWorking on auth\n")
        cfg = _make_config(tmp, vault)
        result = build_context(cfg)
        assert "2026-07-04" in result
        assert "Working on auth" in result


def test_context_contains_recent_inbox():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        inbox_file = vault / "00-Inbox" / "20260703-fix-auth.md"
        inbox_file.write_text("Fix auth race condition\n")
        cfg = _make_config(tmp, vault)
        result = build_context(cfg)
        assert "fix-auth" in result
        assert "Fix auth race condition" in result


def test_context_contains_decision_files():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        (vault / "03-Decisions" / "use-sqlite.md").write_text("Decided to use SQLite\n")
        cfg = _make_config(tmp, vault)
        result = build_context(cfg)
        assert "use-sqlite" in result


def test_context_includes_source_paths():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        (vault / "01-Daily" / "2026-07-04.md").write_text("work\n")
        (vault / "00-Inbox" / "note.md").write_text("note\n")
        cfg = _make_config(tmp, vault)
        result = build_context(cfg)
        assert "01-Daily/2026-07-04.md" in result
        assert "00-Inbox/note.md" in result


def test_context_local_only_no_llm():
    """build_context should work without calling any LLM."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        (vault / "01-Daily" / "2026-07-04.md").write_text("work\n")
        cfg = _make_config(tmp, vault)
        result = build_context(cfg)
        assert "work" in result


def test_context_works_with_empty_vault():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        result = build_context(cfg)
        assert "# AI Dev Brain Context" in result
        assert "No recent daily entries" in result


def test_context_clipboard_flag_calls_xclip():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        (vault / "01-Daily" / "2026-07-04.md").write_text("work\n")
        cfg = _make_config(tmp, vault)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            from brain.commands.context import copy_to_clipboard
            copy_to_clipboard("test context")
            mock_run.assert_called_once()


def test_context_clipboard_fallback_when_no_tool():
    """Should print instructions when no clipboard tool found."""
    from brain.commands.context import copy_to_clipboard
    with patch("subprocess.run", side_effect=FileNotFoundError):
        result = copy_to_clipboard("test context")
        assert result is False


def test_context_clipboard_windows_fallback():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [FileNotFoundError, MagicMock(returncode=0)]
        from brain.commands.context import copy_to_clipboard
        with patch("sys.platform", "win32"):
            copy_to_clipboard("test context")
            assert mock_run.call_count == 2


def test_context_respects_recent_only():
    """Only files from the last 7 days should appear in daily context."""
    import datetime
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        old = vault / "01-Daily" / "2026-06-01.md"
        old.write_text("ancient history")
        today = vault / "01-Daily" / "2026-07-04.md"
        today.write_text("current work")
        cfg = _make_config(tmp, vault)
        with patch("brain.commands.context._today_str", return_value="2026-07-04"):
            result = build_context(cfg)
        assert "current work" in result
        assert "ancient history" not in result
