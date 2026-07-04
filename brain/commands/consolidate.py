"""brain consolidate — stage inbox items into .brain-review/ for review.

Invariants:
- No automatic consolidation (manual invocation only).
- No durable-note changes before approval (staging writes only to
  .brain-review/).
- Rejected or failed proposals leave source notes untouched.
- Duplicate prevention via content checksums.
"""

import hashlib
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from brain.config import BrainConfig, api_key as get_api_key
from brain.provider import LLMProvider

REVIEW_DIR = ".brain-review"
PROPOSALS_DIR = "proposals"
APPROVED_DIR = "approved"
REJECTED_DIR = "rejected"

TARGET_HINTS: dict[str, str] = {
    "decision": "03-Decisions",
    "decisions": "03-Decisions",
    "project": "02-Projects",
    "projects": "02-Projects",
    "knowledge": "04-Knowledge",
    "reference": "04-Knowledge",
    "prompt": "05-Prompts",
    "prompts": "05-Prompts",
    "log": "01-Daily",
    "daily": "01-Daily",
}


def _review_dir(vault: Path) -> Path:
    return vault / REVIEW_DIR


def _proposals_dir(vault: Path) -> Path:
    return _review_dir(vault) / PROPOSALS_DIR


def _approved_dir(vault: Path) -> Path:
    return _review_dir(vault) / APPROVED_DIR


def _rejected_dir(vault: Path) -> Path:
    return _review_dir(vault) / REJECTED_DIR


def _ensure_dirs(vault: Path) -> None:
    _proposals_dir(vault).mkdir(parents=True, exist_ok=True)
    _approved_dir(vault).mkdir(parents=True, exist_ok=True)
    _rejected_dir(vault).mkdir(parents=True, exist_ok=True)


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def _slugify(text: str) -> str:
    text = text.lower().strip()[:60]
    text = re.sub(r"[^a-z0-9-]", "-", text)
    text = re.sub(r"-+", "-", text)
    return text.strip("-")


def _load_proposals(prop_dir: Path) -> list[dict]:
    proposals: list[dict] = []
    if not prop_dir.is_dir():
        return proposals
    for f in sorted(prop_dir.glob("*.json")):
        try:
            proposals.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError):
            continue
    return proposals


def _find_duplicate(
    proposals: list[dict], checksum: str
) -> Optional[dict]:
    for p in proposals:
        if p.get("checksum") == checksum:
            return p
    return None


def _parse_frontmatter(content: str) -> tuple[Optional[dict], str]:
    if not content.startswith("---"):
        return None, content.strip()
    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content.strip()
    raw = parts[1].strip()
    body = parts[2].strip()
    fm: dict[str, Any] = {}
    for line in raw.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1]
            vals = []
            for v in inner.split(","):
                v = v.strip().strip('"').strip("'")
                if v:
                    vals.append(v)
            val = vals
        elif (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]
        fm[key] = val
    return fm, body


def _extract_title(content: str, frontmatter: Optional[dict]) -> str:
    if frontmatter and isinstance(frontmatter, dict):
        raw = frontmatter.get("title")
        if raw and isinstance(raw, str) and raw.strip():
            return raw.strip()
    body = content
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            body = parts[2]
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("# ") and not line.startswith("##"):
            return line[2:].strip()
    lines = [l.strip() for l in body.strip().splitlines() if l.strip()]
    if lines:
        return lines[0][:60]
    return "Untitled"


def _suggest_target_heuristic(
    content: str, frontmatter: Optional[dict]
) -> tuple[str, str, float]:
    if frontmatter:
        tags = frontmatter.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        if isinstance(tags, list):
            for tag in tags:
                tag_lower = tag.lower().strip()
                if tag_lower in TARGET_HINTS:
                    return TARGET_HINTS[tag_lower], "", 0.7

    body_lower = content.lower()
    if any(kw in body_lower for kw in ["decided", "decision", "we chose"]):
        return "03-Decisions", "", 0.6
    if any(kw in body_lower for kw in ["project", "repository", "repo", "architecture"]):
        return "02-Projects", "", 0.5
    if any(kw in body_lower for kw in ["how to", "guide", "reference", "tutorial"]):
        return "04-Knowledge", "", 0.5
    if any(kw in body_lower for kw in ["prompt", "template for"]):
        return "05-Prompts", "", 0.5
    return "04-Knowledge", "", 0.3


def _suggest_target_llm(
    provider: LLMProvider, content: str
) -> tuple[str, str, float]:
    system = (
        "You are a brain consolidation assistant. Given a vault note, suggest:\n"
        "1. The best target directory: 02-Projects, 03-Decisions, 04-Knowledge, "
        "05-Prompts, or 00-Inbox (stay)\n"
        "2. A suggested filename in snake_case.md\n"
        "3. A brief rationale\n\n"
        "Respond ONLY with JSON: "
        '{"target": "...", "filename": "...", "rationale": "...", "confidence": 0.0-1.0}'
    )
    response = provider.complete(
        system=system,
        messages=[
            {
                "role": "user",
                "content": f"Analyze this note for consolidation:\n\n{content[:2000]}",
            }
        ],
        timeout=30,
    )
    try:
        data = json.loads(response)
        target = str(data.get("target", "04-Knowledge"))
        filename = str(data.get("filename", ""))
        confidence = float(data.get("confidence", 0.3))
        return target, filename, min(confidence, 1.0)
    except (json.JSONDecodeError, ValueError, TypeError):
        return "04-Knowledge", "", 0.3


def run_consolidate(
    config: BrainConfig, dry_run: bool = False, use_llm: bool = False
) -> dict:
    vault = Path(config["vaultPath"])
    inbox = vault / "00-Inbox"
    result: dict = {
        "staged": 0,
        "duplicates": 0,
        "errors": [],
        "proposals": [],
    }
    if not inbox.is_dir():
        return result
    _ensure_dirs(vault)
    existing = _load_proposals(_proposals_dir(vault))
    existing_checksums = {
        p.get("checksum") for p in existing if p.get("checksum")
    }
    provider: Optional[LLMProvider] = None
    if use_llm:
        key = get_api_key()
        if key:
            base = config.get("baseUrl", "") or ""
            model = config.get("model", "") or ""
            provider = LLMProvider(
                api_key=key,
                base_url=base or "https://api.openai.com/v1",
                model=model or "gpt-4o",
            )
    md_files = sorted(
        f for f in inbox.glob("*.md") if not f.name.startswith("_")
    )
    for f in md_files:
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            result["errors"].append(f"Cannot read {f.name}: {e}")
            continue
        checksum = _content_hash(content)
        dup = _find_duplicate(existing, checksum)
        if dup:
            result["duplicates"] += 1
            continue
        frontmatter, body = _parse_frontmatter(content)
        if provider:
            target, suggested_name, confidence = _suggest_target_llm(
                provider, content
            )
        else:
            target, suggested_name, confidence = _suggest_target_heuristic(
                content, frontmatter
            )
        title = _extract_title(content, frontmatter)
        name = suggested_name or _slugify(title)
        now = datetime.now(timezone.utc)
        suffix = secrets.token_hex(4)
        proposal_id = (
            f"cons-{now.strftime('%Y%m%d-%H%M%S')}-{name[:16]}-{suffix}"
        )
        proposal = {
            "id": proposal_id,
            "source_path": str(f.relative_to(vault)),
            "content": content,
            "frontmatter": frontmatter,
            "title": title,
            "suggested_target": target,
            "suggested_name": f"{name}.md",
            "confidence": round(confidence, 2),
            "rationale": "",
            "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": "pending",
            "checksum": checksum,
        }
        result["proposals"].append(proposal)
        if not dry_run:
            prop_file = _proposals_dir(vault) / f"{proposal_id}.json"
            prop_file.write_text(json.dumps(proposal, indent=2) + "\n")
        result["staged"] += 1
    return result


def load_pending_proposals(vault: Path) -> list[dict]:
    all_props = _load_proposals(_proposals_dir(vault))
    return [p for p in all_props if p.get("status") == "pending"]


def approve_proposal(vault: Path, proposal: dict) -> Optional[Path]:
    target_dir = vault / proposal["suggested_target"]
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / proposal["suggested_name"]
    if target_path.is_file():
        stem = target_path.stem
        suffix = target_path.suffix
        target_path = target_dir / f"{stem}-{_slugify(proposal['id'])}{suffix}"
    target_path.write_text(proposal["content"])
    proposal["status"] = "approved"
    proposal["approved_at"] = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    _move_proposal(vault, proposal, PROPOSALS_DIR, APPROVED_DIR)
    return target_path


def reject_proposal(vault: Path, proposal: dict, reason: str = "") -> None:
    proposal["status"] = "rejected"
    proposal["rejected_at"] = (
        datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    proposal["reject_reason"] = reason
    _move_proposal(vault, proposal, PROPOSALS_DIR, REJECTED_DIR)


def _move_proposal(
    vault: Path, proposal: dict, src_sub: str, dst_sub: str
) -> None:
    src_dir = _review_dir(vault) / src_sub
    dst_dir = _review_dir(vault) / dst_sub
    dst_dir.mkdir(parents=True, exist_ok=True)
    src_file = src_dir / f"{proposal['id']}.json"
    dst_file = dst_dir / f"{proposal['id']}.json"
    if src_file.is_file():
        src_file.write_text(json.dumps(proposal, indent=2) + "\n")
        src_file.rename(dst_file)
    else:
        dst_file.write_text(json.dumps(proposal, indent=2) + "\n")
