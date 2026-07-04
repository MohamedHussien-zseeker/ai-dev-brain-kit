"""CLI dispatcher for brain commands."""

import argparse
import sys
from pathlib import Path

from brain.config import load_config, config_dir, config_path
from brain.commands.init import initialize_brain
from brain.commands.capture import capture_note, capture_today
from brain.commands.doctor import doctor_offline
from brain.commands.context import build_context, copy_to_clipboard
from brain.commands.hook import install_hook, uninstall_hook, claude_stop
from brain.commands.consolidate import run_consolidate
from brain.commands.review import run_review, stats as review_stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="brain",
        description="AI Dev Brain — local memory system for solo developers",
    )
    parser.add_argument("--version", action="store_true", help="Show version and exit")

    sub = parser.add_subparsers(dest="command")

    # init
    init_p = sub.add_parser("init", help="Create vault and configuration")
    init_p.add_argument("--vault", type=str, default="",
                        help="Custom vault path")
    init_p.add_argument("--non-interactive", action="store_true",
                        help="Skip prompts")

    # note
    note_p = sub.add_parser("note", help="Capture a quick note")
    note_p.add_argument("text", type=str, nargs="*", help="Note text")

    # today
    today_p = sub.add_parser("today", help="Daily log entry")

    # version
    sub.add_parser("version", help="Show version")

    # doctor
    doc_p = sub.add_parser("doctor", help="Health check")
    doc_p.add_argument("--offline", action="store_true",
                       help="Run offline checks only")

    # context
    ctx_p = sub.add_parser("context", help="Build session context from vault")
    ctx_p.add_argument("--clipboard", action="store_true",
                       help="Copy context to clipboard")

    # hook
    hook_p = sub.add_parser("hook", help="Manage Claude Code stop hook")
    hook_sub = hook_p.add_subparsers(dest="hook_command")

    hook_install_p = hook_sub.add_parser("install", help="Install stop hook")
    hook_install_p.add_argument("--force", action="store_true",
                                help="Overwrite existing hook")
    hook_install_p.add_argument("--brain-path", type=str, default="brain",
                                help="Path to brain executable")

    hook_sub.add_parser("uninstall", help="Remove stop hook")

    hook_sub.add_parser("claude-stop", help="Process Claude stop event (internal)")

    # consolidate
    cons_p = sub.add_parser("consolidate", help="Stage inbox items into .brain-review/ for review")
    cons_p.add_argument("--dry-run", action="store_true",
                        help="Preview without writing proposals")
    cons_p.add_argument("--llm", action="store_true",
                        help="Use LLM for target suggestions (requires AI_BRAIN_KEY)")

    # review
    rev_p = sub.add_parser("review", help="Review staged proposals interactively")

    # review stats
    sub.add_parser("review-stats", help="Show review proposal counts")

    args = parser.parse_args(argv)

    if args.version:
        _print_version()
        return 0

    if args.command == "version" or args.command is None:
        _print_version()
        return 0

    if args.command == "init":
        vault_path = Path(args.vault).resolve() if args.vault else Path.cwd()
        initialize_brain(vault_path, non_interactive=args.non_interactive)
        print(f"Brain initialized at {vault_path}")
        print(f"Config: {config_path()}")
        return 0

    if args.command == "hook":
        return _handle_hook(args)

    if args.command == "context":
        cfg = load_config()
        text = build_context(cfg)
        if args.clipboard:
            copy_to_clipboard(text)
        print(text)
        return 0

    # All remaining commands need config
    cfg = load_config()
    vault = Path(cfg["vaultPath"])

    if args.command == "note":
        text = " ".join(args.text) if args.text else _read_stdin()
        if not text:
            print("Error: no text provided. Usage: brain note <text>", file=sys.stderr)
            return 1
        target = capture_note(cfg, text)
        print(f"Note saved → {target}")
        return 0

    if args.command == "today":
        target = capture_today(cfg)
        print(f"Daily log → {target}")
        return 0

    if args.command == "doctor":
        issues = doctor_offline()
        if issues:
            print("Health issues found:")
            for issue in issues:
                print(f"  {issue}")
            return 1
        else:
            print("All checks passed.")
            return 0

    if args.command == "consolidate":
        cfg = load_config()
        result = run_consolidate(cfg, dry_run=args.dry_run, use_llm=args.llm)
        print(f"Staged: {result['staged']}, Duplicates skipped: {result['duplicates']}")
        if result["errors"]:
            for e in result["errors"]:
                print(f"  Error: {e}", file=sys.stderr)
        return 0

    if args.command == "review":
        cfg = load_config()
        run_review(cfg)
        return 0

    if args.command == "review-stats":
        cfg = load_config()
        s = review_stats(cfg)
        print(f"Pending: {s['pending']}, Approved: {s['approved']}, Rejected: {s['rejected']}")
        return 0

    parser.print_help()
    return 0


def _handle_hook(args: argparse.Namespace) -> int:
    if args.hook_command == "install":
        install_hook(args.brain_path, force=args.force)
        return 0
    elif args.hook_command == "uninstall":
        uninstall_hook()
        return 0
    elif args.hook_command == "claude-stop":
        return claude_stop()
    else:
        print("Usage: brain hook {install|uninstall|claude-stop}", file=sys.stderr)
        return 1


def _print_version() -> None:
    print("AI Dev Brain v0.1.0")


def _read_stdin() -> str:
    import sys
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


if __name__ == "__main__":
    sys.exit(main())
