"""Tests for brain init command."""

import json
import os
import tempfile
from pathlib import Path

from brain.commands.init import initialize_brain


def vault_dirs(vault_root: Path) -> set[str]:
    """Return set of relative directory paths in vault."""
    return {
        str(p.relative_to(vault_root))
        for p in vault_root.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    }


def test_init_creates_vault_structure():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        initialize_brain(vault)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        dirs = vault_dirs(vault)
        for expected in ("00-Inbox", "01-Daily", "02-Projects",
                         "03-Decisions", "04-Knowledge", "05-Prompts",
                         "_templates"):
            assert expected in dirs, f"Missing directory: {expected}"


def test_init_creates_config():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        initialize_brain(vault)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        config_file = Path(tmp) / "config.json"
        assert config_file.is_file()
        cfg = json.loads(config_file.read_text())
        assert cfg["version"] == 1
        assert cfg["vaultPath"] == str(vault)


def test_init_is_idempotent():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        initialize_brain(vault)
        dirs_before = vault_dirs(vault)
        initialize_brain(vault)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        dirs_after = vault_dirs(vault)
        assert dirs_before == dirs_after


def test_init_does_not_overwrite_existing_note():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        vault.mkdir(parents=True)
        existing = vault / "00-Inbox" / "my-note.md"
        existing.parent.mkdir()
        existing.write_text("user content")
        initialize_brain(vault)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        assert existing.read_text() == "user content"


def test_init_custom_path():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Custom" / "Brain"
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        initialize_brain(vault)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        config_file = Path(tmp) / "config.json"
        cfg = json.loads(config_file.read_text())
        assert cfg["vaultPath"] == str(vault)


def test_init_creates_templates():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        initialize_brain(vault)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        daily_tpl = vault / "_templates" / "daily.md"
        assert daily_tpl.is_file()
        content = daily_tpl.read_text()
        assert "## Focus" in content
        assert "## Notes" in content


def test_init_creates_index_files():
    with tempfile.TemporaryDirectory() as tmp:
        vault = Path(tmp) / "Brain"
        os.environ["BRAIN_CONFIG_DIR"] = tmp
        initialize_brain(vault)
        os.environ.pop("BRAIN_CONFIG_DIR", None)
        for sub in ("00-Inbox", "01-Daily", "02-Projects"):
            index = vault / sub / "_index.md"
            assert index.is_file(), f"Missing _index.md in {sub}"
