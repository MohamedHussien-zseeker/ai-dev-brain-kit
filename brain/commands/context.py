"""brain context — build session context from vault."""

import datetime
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional

from brain.config import BrainConfig

RECENT_DAYS = 7
MAX_INBOX_ITEMS = 10


def _today_str() -> str:
    return datetime.date.today().isoformat()


def build_context(config: BrainConfig) -> str:
    vault = Path(config["vaultPath"])
    lines: list[str] = []
    lines.append("# AI Dev Brain Context")
    lines.append("")

    # Daily logs — last 7 days
    lines.append("## Recent Daily Logs")
    lines.append("")
    daily_dir = vault / "01-Daily"
    today = _today_str()
    found_daily = False
    if daily_dir.is_dir():
        for i in range(RECENT_DAYS):
            date = (
                datetime.date.fromisoformat(today) - datetime.timedelta(days=i)
            ).isoformat()
            daily_file = daily_dir / f"{date}.md"
            if daily_file.is_file():
                rel = daily_file.relative_to(vault)
                lines.append(f"### {date} (`{rel}`)")
                content = daily_file.read_text().strip()
                # Show first 20 lines
                excerpt_lines = content.splitlines()[:20]
                for line in excerpt_lines:
                    if line.strip():
                        lines.append(f"> {line}")
                lines.append("")
                found_daily = True

    if not found_daily:
        lines.append("_No recent daily entries._")
        lines.append("")

    # Inbox — most recent files
    lines.append("## Recent Inbox Items")
    lines.append("")
    inbox_dir = vault / "00-Inbox"
    if inbox_dir.is_dir():
        md_files = sorted(inbox_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in md_files[:MAX_INBOX_ITEMS]:
            rel = f.relative_to(vault)
            lines.append(f"- `{rel}`")
            excerpt = f.read_text().strip().splitlines()
            first_line = excerpt[0].strip() if excerpt else ""
            if first_line and not first_line.startswith("---"):
                lines.append(f"  _{first_line}_")
            elif len(excerpt) > 3:
                for line in excerpt[3:]:
                    stripped = line.strip()
                    if stripped:
                        lines.append(f"  _{stripped}_")
                        break
        if not md_files:
            lines.append("_Inbox is empty._")
    lines.append("")

    # Decision files
    lines.append("## Recent Decisions")
    lines.append("")
    dec_dir = vault / "03-Decisions"
    if dec_dir.is_dir():
        dec_files = sorted(dec_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
        for f in dec_files[:5]:
            rel = f.relative_to(vault)
            lines.append(f"- `{rel}`")
        if not dec_files:
            lines.append("_No decision records yet._")
    lines.append("")

    return "\n".join(lines)


def copy_to_clipboard(text: str) -> bool:
    if platform.system() == "Windows":
        try:
            subprocess.run(
                ["powershell", "-Command", f"Set-Clipboard -Value '{text}'"],
                check=True,
                timeout=5,
            )
            return True
        except (FileNotFoundError, subprocess.SubprocessError):
            pass
    else:
        for tool in ["xclip", "xsel", "wl-copy"]:
            try:
                if tool == "xclip":
                    subprocess.run(
                        [tool, "-selection", "clipboard"],
                        input=text.encode("utf-8"),
                        check=True,
                        timeout=5,
                    )
                elif tool == "xsel":
                    subprocess.run(
                        [tool, "--clipboard", "--input"],
                        input=text.encode("utf-8"),
                        check=True,
                        timeout=5,
                    )
                elif tool == "wl-copy":
                    subprocess.run(
                        [tool],
                        input=text.encode("utf-8"),
                        check=True,
                        timeout=5,
                    )
                return True
            except (FileNotFoundError, subprocess.SubprocessError):
                continue

    print("No clipboard tool found (install xclip, xsel, or wl-copy)", file=sys.stderr)
    print("--- context output ---", file=sys.stderr)
    print(text, file=sys.stderr)
    return False
