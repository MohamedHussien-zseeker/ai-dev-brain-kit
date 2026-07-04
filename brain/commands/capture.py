"""brain capture — note and today commands."""

import re
from datetime import datetime, timezone
from pathlib import Path

from brain.config import BrainConfig


def capture_note(config: BrainConfig, text: str) -> Path:
    vault = Path(config["vaultPath"])
    inbox = vault / "00-Inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%d-%H%M%S")
    # Sanitize text for filename
    slug = _slugify(text)[:40]
    filename = f"{timestamp}-{slug}.md" if slug else f"{timestamp}.md"
    target = inbox / filename

    content = f"""---
created: {now.strftime('%Y-%m-%dT%H:%M:%SZ')}
type: note
---

{text}
"""
    target.write_text(content)
    return target


def capture_today(config: BrainConfig) -> Path:
    vault = Path(config["vaultPath"])
    daily_dir = vault / "01-Daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    filename = f"{date_str}.md"
    target = daily_dir / filename

    if target.is_file():
        existing = target.read_text()
        focus = _prompt_input("What did you work on? (append to today's log)")
        notes = _prompt_input("Key decisions or notes?")
        if focus or notes:
            appendix = f"\n\n## Later Update ({now.strftime('%H:%M')})\n"
            if focus:
                appendix += f"\n**Focus:** {focus}\n"
            if notes:
                appendix += f"\n{notes}\n"
            target.write_text(existing.rstrip() + appendix)
    else:
        focus = _prompt_input("What are you working on today?")
        notes = _prompt_input("Initial thoughts or notes?")
        content = f"""---
created: {date_str}
tags: [log, daily]
---

# {date_str}

## Focus

{focus or ''}

## Notes

{notes or ''}

## End of Day
"""
        target.write_text(content)

    return target


def _prompt_input(prompt: str) -> str:
    """Read a line of input from the user. Override for testing."""
    return input(f"{prompt} ").strip()


def _slugify(text: str) -> str:
    text = text.lower().strip()[:60]
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")
