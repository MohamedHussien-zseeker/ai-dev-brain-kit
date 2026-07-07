"""brain handoff — per-project session handoff file.

Creates and manages a HANDOFF.md in the current working directory
with five fixed fields: Now, Done, Next, Watch, Files.
"""

import datetime
import re
import sys
from pathlib import Path

HEADERS = ["Now", "Done", "Next", "Watch", "Files"]

TEMPLATE = """# HANDOFF — {date}

## Now


## Done


## Next


## Watch


## Files

"""


def _handoff_path() -> Path:
    return Path.cwd() / "HANDOFF.md"


def _section_re(name: str) -> re.Pattern:
    return re.compile(
        rf"^## {name}\s*$([\s\S]*?)(?=^## |\Z)",
        re.MULTILINE,
    )


def _parse_handoff(path: Path) -> dict[str, str]:
    """Parse HANDOFF.md into a dict of {field: content}."""
    text = path.read_text()
    result = {}
    for h in HEADERS:
        m = _section_re(h).search(text)
        if m:
            content = m.group(1).strip()
            result[h] = content
        else:
            result[h] = ""
    return result


def _set_field(path: Path, field: str, value: str) -> None:
    """Set a single field's content, replacing existing value."""
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    start = None
    end = None
    for i, line in enumerate(lines):
        if re.match(rf"^## {field}\s*$", line):
            start = i
        elif start is not None and re.match(r"^## ", line):
            end = i
            break
    if end is None:
        end = len(lines)

    if start is None:
        print(f"Error: section '{field}' not found in HANDOFF.md", file=sys.stderr)
        sys.exit(1)

    stripped = value.strip()
    middle: list[str] = [lines[start]]  # keep header line
    if stripped:
        middle.append("\n")
        middle.append(stripped + "\n")
        middle.append("\n")
    else:
        middle.append("\n\n\n")
    updated = "".join(lines[: start + 1] + middle[1:] + lines[end:])
    path.write_text(updated)


def _show(config: object) -> None:
    path = _handoff_path()
    if not path.is_file():
        print("No HANDOFF.md in current directory.")
        print("→ Set a field with: brain handoff now <task>")
        return

    data = _parse_handoff(path)
    for h in HEADERS:
        content = data.get(h, "")
        print(f"## {h}")
        if content:
            print(content)
        else:
            print("_(empty)_")
        print()


def _now(config: object, text: str) -> None:
    path = _handoff_path()
    _ensure_file(path)
    _set_field(path, "Now", text)


def _done(config: object, text: str) -> None:
    path = _handoff_path()
    _ensure_file(path)
    data = _parse_handoff(path)
    current = data.get("Done", "")
    new_entry = f"- {text}"
    if current.strip():
        new_text = current.rstrip() + "\n" + new_entry
    else:
        new_text = new_entry
    _set_field(path, "Done", new_text)


def _next(config: object, text: str) -> None:
    path = _handoff_path()
    _ensure_file(path)
    _set_field(path, "Next", text)


def _watch(config: object, text: str) -> None:
    path = _handoff_path()
    _ensure_file(path)
    _set_field(path, "Watch", text)


def _files(config: object, text: str) -> None:
    path = _handoff_path()
    _ensure_file(path)
    _set_field(path, "Files", text)


def _clear(config: object) -> None:
    path = _handoff_path()
    if path.is_file():
        path.unlink()
    print("HANDOFF.md cleared.")


def _ensure_file(path: Path) -> None:
    if not path.is_file():
        date = datetime.date.today().isoformat()
        path.write_text(TEMPLATE.format(date=date))
        print(f"Created {path.name}")


COMMANDS = {
    "show": _show,
    "now": _now,
    "done": _done,
    "next": _next,
    "watch": _watch,
    "files": _files,
    "clear": _clear,
}


def run_handoff(config: object, subcommand: str, text: str = "") -> None:
    if subcommand not in COMMANDS:
        print(f"Unknown handoff subcommand: {subcommand}", file=sys.stderr)
        print("Usage: brain handoff {show|now|done|next|watch|files|clear} [text]", file=sys.stderr)
        sys.exit(1)

    fn = COMMANDS[subcommand]
    if subcommand == "show" or subcommand == "clear":
        fn(config)
    else:
        if not text:
            print(f"Error: 'brain handoff {subcommand}' requires text.", file=sys.stderr)
            sys.exit(1)
        fn(config, text)
