"""Tests for brain configuration."""

import json
import tempfile
from pathlib import Path

from brain.config import BrainConfig, load_config, config_path, default_config


def test_default_config_has_required_fields():
    cfg = default_config()
    assert "version" in cfg
    assert "vaultPath" in cfg
    assert "provider" in cfg
    assert "baseUrl" in cfg
    assert "captureMode" in cfg


def test_load_config_returns_default_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        cfg_path = Path(tmp) / "config.json"
        cfg = load_config(cfg_path)
        assert cfg["vaultPath"] == default_config()["vaultPath"]


def test_load_config_reads_existing():
    with tempfile.TemporaryDirectory() as tmp:
        cfg_path = Path(tmp) / "config.json"
        cfg_path.write_text(json.dumps({
            "version": 1,
            "vaultPath": "/tmp/test-brain",
            "provider": "openai-compatible",
            "baseUrl": "https://custom.api.com/v1",
            "model": "gpt-4",
            "captureMode": "approval-required",
        }))
        cfg = load_config(cfg_path)
        assert cfg["vaultPath"] == "/tmp/test-brain"
        assert cfg["baseUrl"] == "https://custom.api.com/v1"
        assert cfg["model"] == "gpt-4"
