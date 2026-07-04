"""Tests for brain doctor --offline command."""

import json
import os
import tempfile
from pathlib import Path

from brain.commands.doctor import doctor_offline
from brain.config import BrainConfig, default_config


def _make_config(vault: Path) -> BrainConfig:
    cfg = default_config()
    cfg["vaultPath"] = str(vault)
    return cfg


def _write_config(data: dict, tmp: str) -> Path:
    config_dir = Path(tmp)
    config_path = config_dir / "config.json"
    os.environ["BRAIN_CONFIG_DIR"] = tmp
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data))
    return config_path


def test_doctor_passes_with_valid_setup():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        for sub in ("00-Inbox", "01-Daily", "02-Projects",
                    "03-Decisions", "04-Knowledge", "05-Prompts",
                    "_templates"):
            (vault / sub).mkdir()
        os.environ["AI_BRAIN_KEY"] = "test-key"
        _write_config(_make_config(vault), tmp)
        issues = doctor_offline()
        os.environ.pop("AI_BRAIN_KEY", None)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        assert len(issues) == 0, f"Expected no issues, got: {issues}"


def test_doctor_fails_without_config():
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        issues = doctor_offline()
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        assert any("config" in issue.lower() for issue in issues)


def test_doctor_fails_without_vault():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        _write_config(_make_config(vault), tmp)
        issues = doctor_offline()
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        assert any("vault" in issue.lower() for issue in issues)


def test_doctor_fails_missing_directories():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        vault.mkdir(parents=True)
        (vault / "00-Inbox").mkdir()  # Only one dir
        _write_config(_make_config(vault), tmp)
        issues = doctor_offline()
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        missing_dirs = [i for i in issues if "missing" in i.lower()]
        assert len(missing_dirs) > 0
