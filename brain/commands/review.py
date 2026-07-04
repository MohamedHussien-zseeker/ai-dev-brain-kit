"""brain review — terminal-based interactive review of .brain-review/ proposals.

Invariants:
- No durable-note changes before explicit approval.
- Rejected proposals leave source notes untouched.
- Approved proposals copy content to target directory (never move).
"""

import json
import sys
from pathlib import Path
from typing import Optional

from brain.config import BrainConfig
from brain.commands.consolidate import (
    load_pending_proposals,
    approve_proposal,
    reject_proposal,
    _proposals_dir,
    _approved_dir,
    _rejected_dir,
    _review_dir,
)


def _show_proposal(
    proposal: dict, index: int, total: int
) -> None:
    print(
        f"\n{'='*60}\n"
        f"  Proposal {index}/{total}: {proposal['id']}\n"
        f"{'='*60}"
    )
    print(f"  Source:     {proposal['source_path']}")
    print(f"  Title:      {proposal.get('title', '')}")
    print(f"  Target:     {proposal['suggested_target']}/{proposal['suggested_name']}")
    print(f"  Confidence: {proposal['confidence']:.0%}")
    if proposal.get("rationale"):
        print(f"  Rationale:  {proposal['rationale']}")
    print()
    lines = proposal["content"].strip().splitlines()
    print("  ── Content preview ──")
    for line in lines[:10]:
        if line.strip():
            print(f"  {line[:76]}")
    if len(lines) > 10:
        print(f"  ... ({len(lines)} lines, {len(proposal['content'])} chars)")
    print()


def _show_full_content(proposal: dict) -> None:
    print("\n  ── Full content ──")
    print(proposal["content"])
    print("  ── End ──\n")


def _prompt_action() -> str:
    while True:
        try:
            inp = input(
                "  Actions: [a]pprove  [r]eject  [s]kip  [c]ontent  [q]uit\n"
                "  Choice: "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "quit"
        if inp in ("a", "approve"):
            return "approve"
        if inp in ("r", "reject"):
            return "reject"
        if inp in ("s", "skip"):
            return "skip"
        if inp in ("c", "content"):
            return "content"
        if inp in ("q", "quit"):
            return "quit"
        print("  Invalid choice. Enter a, r, s, c, or q.")


def run_review(config: BrainConfig) -> dict:
    vault = Path(config["vaultPath"])
    pending = load_pending_proposals(vault)
    result: dict = {
        "approved": 0,
        "rejected": 0,
        "skipped": 0,
    }
    if not pending:
        print("\n  No pending proposals to review.")
        print(
            "  Run `brain consolidate` first to stage items.\n"
        )
        return result
    print(
        f"\n{'='*60}\n"
        f"  Brain Review — {len(pending)} pending proposal(s)\n"
        f"{'='*60}\n"
    )
    i = 0
    while i < len(pending):
        proposal = pending[i]
        _show_proposal(proposal, i + 1, len(pending))
        action = _prompt_action()
        if action == "approve":
            target = approve_proposal(vault, proposal)
            if target:
                print(f"  ✓ Approved → {target.relative_to(vault)}\n")
            else:
                print(f"  ✓ Approved\n")
            result["approved"] += 1
            i += 1
        elif action == "reject":
            try:
                reason = input("  Reason (optional): ").strip()
            except (EOFError, KeyboardInterrupt):
                reason = ""
            reject_proposal(vault, proposal, reason)
            print(f"  ✗ Rejected. Source untouched.\n")
            result["rejected"] += 1
            i += 1
        elif action == "skip":
            print(f"  → Skipped.\n")
            result["skipped"] += 1
            i += 1
        elif action == "content":
            _show_full_content(proposal)
        elif action == "quit":
            print("  Review session ended.\n")
            break
    print(
        f"{'='*60}\n"
        f"  Review complete: {result['approved']} approved, "
        f"{result['rejected']} rejected, {result['skipped']} skipped\n"
        f"{'='*60}\n"
    )
    return result


def stats(config: BrainConfig) -> dict:
    vault = Path(config["vaultPath"])
    pending = len(load_pending_proposals(vault))
    approved = len(list(_approved_dir(vault).glob("*.json")))
    rejected = len(list(_rejected_dir(vault).glob("*.json")))
    return {
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
    }
