"""Tests for brain/commands/consolidate.py — brain consolidate."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from brain.commands.consolidate import (
    run_consolidate,
    _content_hash,
    _slugify,
    _parse_frontmatter,
    _extract_title,
    _suggest_target_heuristic,
    _load_proposals,
    _find_duplicate,
    _proposals_dir,
    _approved_dir,
    _rejected_dir,
    _ensure_dirs,
    approve_proposal,
    reject_proposal,
    REVIEW_DIR,
)


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


def test_consolidate_empty_vault_no_crash():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg)
        assert result["staged"] == 0
        assert result["duplicates"] == 0
        assert result["errors"] == []


def test_consolidate_stages_inbox_note():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "fix-auth.md", "# Fix Auth\n\nDecided to use JWT tokens\n")
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg)
        assert result["staged"] == 1
        assert result["duplicates"] == 0
        # Verify proposal file was created
        props = list((vault / REVIEW_DIR / "proposals").glob("*.json"))
        assert len(props) == 1
        prop = json.loads(props[0].read_text())
        assert prop["source_path"] == "00-Inbox/fix-auth.md"
        assert prop["status"] == "pending"
        assert prop["checksum"] == _content_hash("# Fix Auth\n\nDecided to use JWT tokens\n")


def test_consolidate_duplicate_prevention():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "note.md", "Same content here")
        cfg = _make_config(tmp, vault)
        # First run
        r1 = run_consolidate(cfg)
        assert r1["staged"] == 1
        # Second run with same content
        r2 = run_consolidate(cfg)
        assert r2["staged"] == 0
        assert r2["duplicates"] == 1


def test_consolidate_duplicate_different_content():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        cfg = _make_config(tmp, vault)
        _write_inbox(vault, "first.md", "First note")
        r1 = run_consolidate(cfg)
        assert r1["staged"] == 1
        _write_inbox(vault, "second.md", "Second note with different content")
        r2 = run_consolidate(cfg)
        assert r2["staged"] == 1  # new content gets staged
        assert r2["duplicates"] == 1  # first.md is already staged


def test_consolidate_respects_dry_run():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "note.md", "Dry run test")
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg, dry_run=True)
        assert result["staged"] == 1
        assert result["proposals"][0]["status"] == "pending"
        # No files should be written
        prop_dir = vault / REVIEW_DIR / "proposals"
        assert not prop_dir.is_dir() or len(list(prop_dir.glob("*.json"))) == 0


def test_consolidate_heuristic_decision_tag():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        content = "---\ntags: [decision]\n---\n\nDecided to use Postgres\n"
        _write_inbox(vault, "db-choice.md", content)
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg)
        assert result["staged"] == 1
        assert result["proposals"][0]["suggested_target"] == "03-Decisions"


def test_consolidate_heuristic_knowledge_tag():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        content = "---\ntags: [reference]\n---\n\nHow to deploy with Docker\n"
        _write_inbox(vault, "docker-guide.md", content)
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg)
        assert result["staged"] == 1
        assert result["proposals"][0]["suggested_target"] == "04-Knowledge"


def test_consolidate_heuristic_fallback():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "random.md", "Just some random thoughts")
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg)
        assert result["staged"] == 1
        # Low-confidence fallback
        assert result["proposals"][0]["confidence"] <= 0.4


def test_consolidate_skips_underscore_files():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "_index.md", "Index file")
        _write_inbox(vault, "real-note.md", "Real content")
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg)
        assert result["staged"] == 1


def test_consolidate_unreadable_file():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        note = _write_inbox(vault, "broken.md", "content")
        note.chmod(0o000)
        cfg = _make_config(tmp, vault)
        try:
            result = run_consolidate(cfg)
            assert result["errors"] != []
        finally:
            note.chmod(0o644)


def test_consolidate_missing_inbox():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "EmptyBrain"
        vault.mkdir(parents=True)
        cfg = _make_config(tmp, vault)
        result = run_consolidate(cfg)
        assert result["staged"] == 0
        assert result["errors"] == []


def test_content_hash_consistency():
    h1 = _content_hash("hello world")
    h2 = _content_hash("hello world")
    h3 = _content_hash("hello world!")
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 16


def test_slugify():
    assert _slugify("Hello World") == "hello-world"
    assert _slugify("  Spaces! ") == "spaces"
    assert _slugify("") == ""
    assert _slugify("ALLCAPS") == "allcaps"


def test_parse_frontmatter_with_tags():
    content = "---\ntags: [decision, auth]\ntitle: Auth Decision\n---\n\nBody text"
    fm, body = _parse_frontmatter(content)
    assert fm is not None
    assert "decision" in fm["tags"]
    assert "auth" in fm["tags"]
    assert fm["title"] == "Auth Decision"
    assert body == "Body text"


def test_parse_frontmatter_no_frontmatter():
    content = "# Just a heading\n\nBody text"
    fm, body = _parse_frontmatter(content)
    assert fm is None
    assert "heading" in body


def test_parse_frontmatter_malformed():
    content = "---\nno colon here\n---\n\nBody"
    fm, body = _parse_frontmatter(content)
    assert fm is not None
    assert body == "Body"


def test_extract_title_from_frontmatter():
    fm = {"title": "My Title"}
    content = "# Wrong Title\n\nbody"
    assert _extract_title(content, fm) == "My Title"


def test_extract_title_from_heading():
    assert _extract_title("# Real Title\n\nbody", {}) == "Real Title"


def test_extract_title_fallback():
    assert _extract_title("just text", None) == "just text"


def test_suggest_target_decision_keyword():
    target, _, conf = _suggest_target_heuristic("We decided to use Redis", None)
    assert target == "03-Decisions"
    assert conf >= 0.5


def test_suggest_target_project_keyword():
    target, _, conf = _suggest_target_heuristic("This project uses FastAPI", None)
    assert target == "02-Projects"
    assert conf >= 0.4


def test_suggest_target_guide_keyword():
    target, _, conf = _suggest_target_heuristic("How to set up monitoring", None)
    assert target == "04-Knowledge"
    assert conf >= 0.4


def test_provider_failure_falls_back():
    """When LLM provider fails, consolidate should fall back to heuristic."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "note.md", "# Decision\n\nWe chose X over Y")
        cfg = _make_config(tmp, vault)
        cfg["baseUrl"] = "http://localhost:1"  # non-routable
        cfg["model"] = "gpt-4o"
        with patch.dict(os.environ, {"AI_BRAIN_KEY": "test-key"}):
            result = run_consolidate(cfg, use_llm=True)
        assert result["staged"] == 1
        # Should have fallen back since provider will fail
        assert result["proposals"][0]["suggested_target"] in (
            "03-Decisions", "04-Knowledge"
        )


def test_provider_failure_empty_key():
    """When no API key, use_llm should silently fall back to heuristic."""
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "note.md", "Some content")
        cfg = _make_config(tmp, vault)
        with patch.dict(os.environ, {}, clear=True):
            result = run_consolidate(cfg, use_llm=True)
        assert result["staged"] == 1
        assert result["errors"] == []


def test_approve_proposal_creates_target_file():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "note.md", "# Test\n\nbody")
        cfg = _make_config(tmp, vault)
        run_consolidate(cfg)
        props = list(_proposals_dir(vault).glob("*.json"))
        assert len(props) == 1
        proposal = json.loads(props[0].read_text())
        target = approve_proposal(vault, proposal)
        assert target is not None
        assert target.is_file()
        assert target.read_text() == "# Test\n\nbody"
        # Proposal moved to approved
        assert len(list(_approved_dir(vault).glob("*.json"))) == 1
        assert len(list(_proposals_dir(vault).glob("*.json"))) == 0


def test_approve_proposal_preserves_existing_file():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        _write_inbox(vault, "note.md", "# Test\n\nbody")
        cfg = _make_config(tmp, vault)
        run_consolidate(cfg)
        props = list(_proposals_dir(vault).glob("*.json"))
        proposal = json.loads(props[0].read_text())
        # Create existing file at target
        target_dir = vault / proposal["suggested_target"]
        target_dir.mkdir(parents=True, exist_ok=True)
        existing = target_dir / proposal["suggested_name"]
        existing.write_text("existing content")
        target = approve_proposal(vault, proposal)
        assert target is not None
        assert target.name != existing.name  # Different name
        assert existing.read_text() == "existing content"


def test_reject_proposal_leaves_source_untouched():
    with tempfile.TemporaryDirectory() as tmp:
        vault = _make_vault(tmp)
        src = _write_inbox(vault, "note.md", "# Original content")
        cfg = _make_config(tmp, vault)
        run_consolidate(cfg)
        props = list(_proposals_dir(vault).glob("*.json"))
        proposal = json.loads(props[0].read_text())
        reject_proposal(vault, proposal, reason="Not relevant")
        # Source untouched
        assert src.read_text() == "# Original content"
        # Proposal moved to rejected
        assert len(list(_rejected_dir(vault).glob("*.json"))) == 1
        assert len(list(_proposals_dir(vault).glob("*.json"))) == 0
        # No files created in target
        rejected_prop = json.loads(
            list(_rejected_dir(vault).glob("*.json"))[0].read_text()
        )
        assert rejected_prop["status"] == "rejected"
        assert rejected_prop["reject_reason"] == "Not relevant"


def test_find_duplicate_matches_checksum():
    proposals = [
        {"id": "1", "checksum": "abc123", "status": "pending"},
        {"id": "2", "checksum": "def456", "status": "pending"},
    ]
    assert _find_duplicate(proposals, "abc123") is not None
    assert _find_duplicate(proposals, "xyz789") is None


def test_ensure_dirs_creates_review_structure():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Vault"
        vault.mkdir()
        _ensure_dirs(vault)
        assert (vault / REVIEW_DIR / "proposals").is_dir()
        assert (vault / REVIEW_DIR / "approved").is_dir()
        assert (vault / REVIEW_DIR / "rejected").is_dir()
        # Idempotent
        _ensure_dirs(vault)
        assert (vault / REVIEW_DIR / "proposals").is_dir()
