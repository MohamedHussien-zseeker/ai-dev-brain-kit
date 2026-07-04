"""Tests for brain/commands/review.py — brain review."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from brain.commands.consolidate import (
    run_consolidate,
    _proposals_dir,
    _approved_dir,
    _rejected_dir,
    approve_proposal,
    reject_proposal,
    REVIEW_DIR,
)
from brain.commands.review import run_review, stats as review_stats, _prompt_action


def _make_vault(tmp: str) -> Path:
    vault = Path(tmp) / "Brain"
    (vault / "00-Inbox").mkdir(parents=True)
    for sub in ("01-Daily", "02-Projects", "03-Decisions", "04-Knowledge", "05-Prompts"):
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


def _write_inbox(vault: Path, name: str, content: str) -> Path:
    target = vault / "00-Inbox" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return target


def _stage_one(vault: Path, cfg: dict, content: str = "# Note\n\nbody") -> dict:
    _write_inbox(vault, "note.md", content)
    return run_consolidate(cfg)


def test_review_no_pending_proposals():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        result = run_review(cfg)
        assert result["approved"] == 0
        assert result["rejected"] == 0
        assert result["skipped"] == 0


def test_review_approve_proposal():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _stage_one(vault, cfg)
        with patch("builtins.input", side_effect=["a"]):
            result = run_review(cfg)
        assert result["approved"] == 1
        assert result["rejected"] == 0
        assert result["skipped"] == 0
        assert len(list(_proposals_dir(vault).glob("*.json"))) == 0
        assert len(list(_approved_dir(vault).glob("*.json"))) == 1


def test_review_reject_proposal():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _stage_one(vault, cfg)
        with patch("builtins.input", side_effect=["r", "not useful"]):
            result = run_review(cfg)
        assert result["approved"] == 0
        assert result["rejected"] == 1
        assert result["skipped"] == 0
        assert len(list(_rejected_dir(vault).glob("*.json"))) == 1


def test_review_skip_proposal():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _stage_one(vault, cfg)
        with patch("builtins.input", side_effect=["s"]):
            result = run_review(cfg)
        assert result["approved"] == 0
        assert result["rejected"] == 0
        assert result["skipped"] == 1
        # Proposal stays in pending
        assert len(list(_proposals_dir(vault).glob("*.json"))) == 1


def test_review_quit_early():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _stage_one(vault, cfg)
        with patch("builtins.input", side_effect=["q"]):
            result = run_review(cfg)
        assert result["approved"] == 0
        assert result["rejected"] == 0
        assert result["skipped"] == 0


def test_review_view_content_then_approve():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _stage_one(vault, cfg, "# Important\n\nDetailed content here")
        with patch("builtins.input", side_effect=["c", "a"]):
            result = run_review(cfg)
        assert result["approved"] == 1


def test_review_multiple_proposals():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _write_inbox(vault, "a.md", "# A\n\nFirst")
        _write_inbox(vault, "b.md", "# B\n\nSecond")
        _write_inbox(vault, "c.md", "# C\n\nThird")
        run_consolidate(cfg)
        with patch("builtins.input", side_effect=["a", "r", "", "s"]):
            result = run_review(cfg)
        assert result["approved"] == 1
        assert result["rejected"] == 1
        assert result["skipped"] == 1


def test_review_approve_creates_target_file():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _stage_one(vault, cfg, "# Decision\n\nUse Postgres\n")
        with patch("builtins.input", side_effect=["a"]):
            run_review(cfg)
        # Check target file exists
        dec_dir = vault / "03-Decisions"
        md_files = list(dec_dir.glob("*.md"))
        assert len(md_files) >= 1
        content = md_files[0].read_text()
        assert "Use Postgres" in content


def test_review_reject_leaves_source_untouched():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        src = _write_inbox(vault, "note.md", "# Original source content")
        run_consolidate(cfg)
        with patch("builtins.input", side_effect=["r", ""]):
            run_review(cfg)
        assert src.read_text() == "# Original source content"


def test_review_stats():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        s = review_stats(cfg)
        assert s["pending"] == 0
        assert s["approved"] == 0
        assert s["rejected"] == 0
        _stage_one(vault, cfg)
        s = review_stats(cfg)
        assert s["pending"] == 1
        assert s["approved"] == 0
        assert s["rejected"] == 0


def test_review_prompt_action_valid():
    with patch("builtins.input", return_value="a"):
        assert _prompt_action() == "approve"
    with patch("builtins.input", return_value="r"):
        assert _prompt_action() == "reject"
    with patch("builtins.input", return_value="s"):
        assert _prompt_action() == "skip"
    with patch("builtins.input", return_value="c"):
        assert _prompt_action() == "content"
    with patch("builtins.input", return_value="q"):
        assert _prompt_action() == "quit"


def test_review_prompt_action_long_forms():
    with patch("builtins.input", return_value="approve"):
        assert _prompt_action() == "approve"
    with patch("builtins.input", return_value="quit"):
        assert _prompt_action() == "quit"


def test_review_prompt_action_invalid_then_valid():
    with patch("builtins.input", side_effect=["x", "a"]):
        assert _prompt_action() == "approve"


def test_review_prompt_action_eof():
    with patch("builtins.input", side_effect=EOFError):
        assert _prompt_action() == "quit"


def test_review_prompt_action_keyboard_interrupt():
    with patch("builtins.input", side_effect=KeyboardInterrupt):
        assert _prompt_action() == "quit"
