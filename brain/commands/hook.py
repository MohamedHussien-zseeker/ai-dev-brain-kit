"""brain hook — Claude Code stop hook and CLI hook management."""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from brain.config import BrainConfig, load_config, config_path

HOME = Path.home()
CLAUDE_CONFIG_PATH = HOME / ".claude" / "claude.json"

EXCLUDED_FIELDS = {"transcript", "messages", "conversation", "raw_output"}


def process_stop_event(config: BrainConfig, event: dict) -> Optional[Path]:
    session_id = event.get("session_id")
    if not session_id:
        return None

    vault = Path(config["vaultPath"])
    logs_dir = vault / "05-Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{session_id}.md"
    target = logs_dir / filename
    if target.is_file():
        return target

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = []
    lines.append("---")
    lines.append(f"created: {now}")
    lines.append(f"session_id: {session_id}")
    if event.get("project"):
        lines.append(f"project: {event['project']}")
    lines.append("tags: [session, auto-captured]")
    lines.append("---")
    lines.append("")
    lines.append(f"# AI Session — {session_id}")
    lines.append("")

    summary = event.get("summary", "")
    if summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(summary)
        lines.append("")

    decisions = event.get("key_decisions", [])
    if decisions:
        lines.append("## Key Decisions")
        lines.append("")
        for d in decisions:
            lines.append(f"- {d}")
        lines.append("")

    follow_up = event.get("follow_up", [])
    if follow_up:
        lines.append("## Follow-up")
        lines.append("")
        for f in follow_up:
            lines.append(f"- [ ] {f}")
        lines.append("")

    target.write_text("\n".join(lines) + "\n")
    return target


def install_hook(brain_path: str, force: bool = False) -> bool:
    claude_json = CLAUDE_CONFIG_PATH
    config = {}
    if claude_json.is_file():
        try:
            config = json.loads(claude_json.read_text())
        except json.JSONDecodeError:
            pass

    if "stopHook" in config and not force:
        print("A Claude stop hook is already configured.", file=sys.stderr)
        print("Use --force to overwrite, or `brain hook uninstall` first.", file=sys.stderr)
        return False

    config["stopHook"] = {
        "command": f"{brain_path} hook claude-stop",
        "timeout": 5000,
    }

    claude_json.parent.mkdir(parents=True, exist_ok=True)
    claude_json.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Claude stop hook installed → {claude_json}")
    return True


def uninstall_hook() -> bool:
    claude_json = CLAUDE_CONFIG_PATH
    if not claude_json.is_file():
        print("No Claude config found.", file=sys.stderr)
        return False

    try:
        config = json.loads(claude_json.read_text())
    except json.JSONDecodeError:
        print("Invalid Claude config, skipping.", file=sys.stderr)
        return False

    if "stopHook" not in config:
        print("No stop hook configured.", file=sys.stderr)
        return False

    del config["stopHook"]
    claude_json.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Stop hook removed from {claude_json}")
    return True


def claude_stop() -> int:
    raw = sys.stdin.read().strip()
    if not raw:
        print("No input received from Claude hook (stdin was empty)", file=sys.stderr)
        return 1

    try:
        event = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Failed to parse Claude hook event: {e}", file=sys.stderr)
        return 1

    for field in EXCLUDED_FIELDS:
        event.pop(field, None)

    cfg = load_config()
    target = process_stop_event(cfg, event)
    if target:
        print(f"Session saved → {target}")
        return 0

    print("No session_id in event; nothing saved.", file=sys.stderr)
    return 1
