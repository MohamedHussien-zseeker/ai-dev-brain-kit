"""Configuration management for brain CLI."""

import json
import os
from pathlib import Path
from typing import TypedDict, Optional


def config_dir() -> Path:
    return Path(os.environ.get("BRAIN_CONFIG_DIR", Path.home() / ".brain"))


def config_path() -> Path:
    return config_dir() / "config.json"


def default_vault_path() -> str:
    return os.environ.get("BRAIN_VAULT_PATH", str(Path.home() / "AI-Dev-Brain"))


class BrainConfig(TypedDict, total=False):
    version: int
    vaultPath: str
    provider: str
    baseUrl: str
    model: str
    captureMode: str


def default_config() -> BrainConfig:
    return {
        "version": 1,
        "vaultPath": default_vault_path(),
        "provider": "openai-compatible",
        "baseUrl": "",
        "model": "",
        "captureMode": "approval-required",
    }


def load_config(path: Optional[Path] = None) -> BrainConfig:
    path = path or config_path()
    if path.is_file():
        data = json.loads(path.read_text())
        cfg = default_config()
        cfg.update(data)
        return cfg
    return default_config()


def save_config(cfg: BrainConfig, path: Optional[Path] = None) -> Path:
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2) + "\n")
    return path


def api_key() -> str:
    return os.environ.get("AI_BRAIN_KEY", "")
