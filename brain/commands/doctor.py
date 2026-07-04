"""brain doctor — health check."""

import os
import sys
from pathlib import Path

from brain.config import load_config, config_path, api_key

REQUIRED_VAULT_DIRS = [
    "00-Inbox",
    "01-Daily",
    "02-Projects",
    "03-Decisions",
    "04-Knowledge",
    "05-Prompts",
    "_templates",
]


def doctor_offline() -> list[str]:
    """Run offline health checks. Returns list of issues (empty = healthy)."""
    issues: list[str] = []

    # Check config
    if not config_path().is_file():
        issues.append(f"Config not found: {config_path()}")
        # Can't check further without config
        return issues

    cfg = load_config()

    # Check vault path
    vault = Path(cfg["vaultPath"])
    if not vault.is_dir():
        issues.append(f"Vault directory not found: {vault}")
        return issues

    # Check required subdirectories
    for name in REQUIRED_VAULT_DIRS:
        if not (vault / name).is_dir():
            issues.append(f"Missing vault directory: {name}")

    # Check config version
    if cfg.get("version") != 1:
        issues.append(f"Unknown config version: {cfg.get('version')}")

    # Check API key
    if not api_key():
        issues.append("AI_BRAIN_KEY environment variable not set (optional for offline use)")

    return issues
