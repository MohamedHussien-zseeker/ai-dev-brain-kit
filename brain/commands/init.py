"""brain init — create vault and configuration."""

import shutil
from pathlib import Path

from brain.config import BrainConfig, default_config, save_config, config_dir, config_path

TEMPLATE_VAULT = Path(__file__).resolve().parent.parent.parent / "template-vault"

VAULT_DIRS = [
    "00-Inbox",
    "01-Daily",
    "02-Projects",
    "03-Decisions",
    "04-Knowledge",
    "05-Prompts",
    "_templates",
]

TEMPLATE_NAMES = {
    "daily.md",
    "project.md",
    "decision.md",
    "prompt.md",
    "session.md",
}

INDEX_TEMPLATES: dict[str, str] = {
    "00-Inbox": "---\n# 00-Inbox\n\nQuick captures and raw notes.\n",
    "01-Daily": "---\n# 01-Daily\n\nDaily activity logs.\n",
    "02-Projects": "---\n# 02-Projects\n\nActive project notes.\n",
    "03-Decisions": "---\n# 03-Decisions\n\nDurable technical decisions.\n",
    "04-Knowledge": "---\n# 04-Knowledge\n\nReference knowledge pages.\n",
    "05-Prompts": "---\n# 05-Prompts\n\nReusable prompt templates.\n",
    "_templates": "---\n# Templates\n\nReusable note templates.\n",
}


def initialize_brain(vault_path: Path, non_interactive: bool = False) -> None:
    vault_path = vault_path.resolve()

    # Create vault directories
    for name in VAULT_DIRS:
        (vault_path / name).mkdir(parents=True, exist_ok=True)

    # Write _index.md for each directory (never overwrite)
    for name, content in INDEX_TEMPLATES.items():
        index_file = vault_path / name / "_index.md"
        if not index_file.is_file():
            index_file.write_text(content)

    # Copy template files from template-vault if available; otherwise create defaults
    tpl_dir = vault_path / "_templates"
    if TEMPLATE_VAULT.is_dir():
        src_tpl = TEMPLATE_VAULT / "_templates"
        if src_tpl.is_dir():
            for f in src_tpl.glob("*.md"):
                target = tpl_dir / f.name
                if not target.is_file():
                    shutil.copy2(f, target)

    # Ensure core templates exist (fallback defaults)
    _ensure_default_template(tpl_dir, "daily.md", _DEFAULT_DAILY_TPL)
    _ensure_default_template(tpl_dir, "project.md", _DEFAULT_PROJECT_TPL)
    _ensure_default_template(tpl_dir, "decision.md", _DEFAULT_DECISION_TPL)
    _ensure_default_template(tpl_dir, "prompt.md", _DEFAULT_PROMPT_TPL)
    _ensure_default_template(tpl_dir, "session.md", _DEFAULT_SESSION_TPL)

    # Write config
    cfg = default_config()
    cfg["vaultPath"] = str(vault_path)
    save_config(cfg)


def _ensure_default_template(tpl_dir: Path, name: str, content: str) -> None:
    target = tpl_dir / name
    if not target.is_file():
        target.write_text(content)


_DEFAULT_DAILY_TPL = """---
created: {date}
tags: [log, daily]
---

# {date}

## Focus

*What are you working on today?*

## Notes

*Capture decisions, blockers, and context.*

## End of Day

### Done
- [ ]

### Blockers

### Tomorrow
- [ ]
"""

_DEFAULT_PROJECT_TPL = """---
created: {date}
status: active
tags: [project]
---

# {title}

## Description

## Tech Stack

## Decisions

## Related
"""

_DEFAULT_DECISION_TPL = """---
created: {date}
status: active
tags: [decision]
---

# {title}

## Context

## Decision

## Consequences
"""

_DEFAULT_PROMPT_TPL = """---
created: {date}
tags: [prompt, template]
---

# {title}

## Context

## Prompt

```
{placeholder}
```

## Notes
"""

_DEFAULT_SESSION_TPL = """---
created: {date}
tags: [session]
---

# AI Session — {date}

## Summary

## Key Decisions

## Follow-up
"""
