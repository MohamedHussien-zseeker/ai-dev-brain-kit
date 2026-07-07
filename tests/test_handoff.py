"""Tests for brain/commands/handoff.py — brain handoff."""

import os
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

from brain.commands.handoff import (
    _handoff_path,
    _parse_handoff,
    _set_field,
    _ensure_file,
    run_handoff,
    HEADERS,
)

# -- helpers ----------------------------------------------------------------


def _make_config() -> dict:
    return {
        "version": 1,
        "vaultPath": "/tmp/fake-vault",
        "provider": "openai-compatible",
        "baseUrl": "",
        "model": "",
        "captureMode": "approval-required",
    }


# -- _parse_handoff ---------------------------------------------------------


def _section_re(name):
    return re.compile(rf"^## {name}\s*$([\s\S]*?)(?=^## |\Z)", re.MULTILINE)


def test_parse_empty_sections():
    text = """# HANDOFF

## Now


## Done


## Next


## Watch


## Files

"""
    for h in HEADERS:
        m = _section_re(h).search(text)
        assert m is not None, f"Section {h} not found"
        assert m.group(1).strip() == "", f"Section {h} should be empty"


def test_parse_populated():
    text = """# HANDOFF — 2026-07-07

## Now
Fix login bug

## Done
- Added tests
- Fixed race condition

## Next
Deploy to staging

## Watch
None

## Files
- src/auth.py
- tests/test_auth.py
"""
    for h in HEADERS:
        m = _section_re(h).search(text)
        assert m is not None, f"Section {h} not found"
        assert m.group(1).strip(), f"Section {h} is empty"

    assert "Fix login bug" in _section_re("Now").search(text).group(1)
    assert "Deploy to staging" in _section_re("Next").search(text).group(1)


# -- integration tests via run_handoff --------------------------------------


def test_show_no_file(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            run_handoff(_make_config(), "show")
            captured = capsys.readouterr().out
            assert "No HANDOFF.md" in captured
        finally:
            os.chdir(orig)


def test_set_now_creates_file_and_shows():
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            run_handoff(_make_config(), "now", "Implement auth")
            assert (Path(tmp) / "HANDOFF.md").is_file()
            data = _parse_handoff(Path(tmp) / "HANDOFF.md")
            assert "Implement auth" in data["Now"]
        finally:
            os.chdir(orig)


def test_set_all_fields():
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            run_handoff(_make_config(), "now", "Fix bug")
            run_handoff(_make_config(), "done", "Root caused the issue")
            run_handoff(_make_config(), "next", "Write fix")
            run_handoff(_make_config(), "watch", "Edge case with empty input")
            run_handoff(_make_config(), "files", "src/handler.py")
            data = _parse_handoff(Path(tmp) / "HANDOFF.md")
            assert data["Now"] == "Fix bug"
            assert "Root caused" in data["Done"]
            assert data["Next"] == "Write fix"
            assert "Edge case" in data["Watch"]
            assert "src/handler.py" in data["Files"]
        finally:
            os.chdir(orig)


def test_done_appends():
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            run_handoff(_make_config(), "done", "First item")
            run_handoff(_make_config(), "done", "Second item")
            data = _parse_handoff(Path(tmp) / "HANDOFF.md")
            assert "First item" in data["Done"]
            assert "Second item" in data["Done"]
            lines = data["Done"].splitlines()
            assert len(lines) >= 2
        finally:
            os.chdir(orig)


def test_clear_removes_file():
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            run_handoff(_make_config(), "now", "Something")
            assert (Path(tmp) / "HANDOFF.md").is_file()
            run_handoff(_make_config(), "clear")
            assert not (Path(tmp) / "HANDOFF.md").is_file()
        finally:
            os.chdir(orig)


def test_set_now_overwrites():
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            run_handoff(_make_config(), "now", "First task")
            run_handoff(_make_config(), "now", "Second task")
            data = _parse_handoff(Path(tmp) / "HANDOFF.md")
            assert data["Now"] == "Second task"
            assert "First task" not in data["Now"]
        finally:
            os.chdir(orig)


def test_show_after_set(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            run_handoff(_make_config(), "now", "Current task")
            run_handoff(_make_config(), "show")
            captured = capsys.readouterr().out
            assert "Current task" in captured
        finally:
            os.chdir(orig)


def test_unknown_subcommand(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            import sys
            from io import StringIO

            err = StringIO()
            old_err = sys.stderr
            sys.stderr = err
            try:
                run_handoff(_make_config(), "bogus")
            except SystemExit:
                pass
            finally:
                sys.stderr = old_err
            assert "Unknown" in err.getvalue()
        finally:
            os.chdir(orig)


def test_no_text_required_subcommand(capsys):
    with tempfile.TemporaryDirectory() as tmp:
        orig = Path.cwd()
        os.chdir(tmp)
        try:
            import sys
            from io import StringIO

            err = StringIO()
            old_err = sys.stderr
            sys.stderr = err
            try:
                run_handoff(_make_config(), "now", "")
            except SystemExit:
                pass
            finally:
                sys.stderr = old_err
            assert "requires text" in err.getvalue()
        finally:
            os.chdir(orig)


def test_section_re_preserves_multiline_content():
    text = """# HANDOFF

## Now
line one
line two

## Done
- item 1

## Next
single

## Watch


## Files

"""
    m = _section_re("Now").search(text)
    assert m is not None
    content = m.group(1).strip()
    assert "line one" in content
    assert "line two" in content


def test_done_field_parses_multiple_entries():
    text = """# HANDOFF

## Now


## Done
- First completed item
- Second completed item
- Third completed item

## Next


## Watch


## Files

"""
    m = _section_re("Done").search(text)
    assert m is not None
    content = m.group(1).strip()
    assert "First completed item" in content
    assert "Second completed item" in content
    assert "Third completed item" in content
    assert content.count("-") == 3
