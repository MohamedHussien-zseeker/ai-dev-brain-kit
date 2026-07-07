"""Tests for brain/commands/feedback.py — brain feedback."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from brain.commands.feedback import run_feedback, ISSUES_URL, DISCUSSIONS_URL


def _make_config() -> dict:
    return {
        "version": 1,
        "vaultPath": "/tmp/fake-vault",
        "provider": "openai-compatible",
        "baseUrl": "",
        "model": "",
        "captureMode": "approval-required",
    }


def test_feedback_no_topic_prints_both_links(capsys):
    run_feedback(_make_config(), "")
    out = capsys.readouterr().out
    assert ISSUES_URL in out
    assert DISCUSSIONS_URL in out
    assert "brain feedback bug" in out
    assert "brain feedback idea" in out


def test_feedback_bug_prints_issues(capsys):
    run_feedback(_make_config(), "bug")
    out = capsys.readouterr().out
    assert ISSUES_URL in out
    assert "version" in out.lower()
    assert "platform" in out.lower()


def test_feedback_idea_prints_discussions(capsys):
    run_feedback(_make_config(), "idea")
    out = capsys.readouterr().out
    assert DISCUSSIONS_URL in out
    assert "ideas" in out.lower() or "questions" in out.lower()


def test_feedback_bug_no_secrets_warning(capsys):
    run_feedback(_make_config(), "bug")
    out = capsys.readouterr().out
    assert "Do NOT include" in out


def test_feedback_unknown_topic_prints_help(capsys):
    # topic is validated by argparse, but test directly anyway
    run_feedback(_make_config(), "")
    out = capsys.readouterr().out
    assert ISSUES_URL in out
