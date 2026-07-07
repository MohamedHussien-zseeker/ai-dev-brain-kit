"""brain feedback — direct links to GitHub Issues and Discussions."""

import sys
import webbrowser
from brain.config import BrainConfig

REPO = "MohamedHussien-zseeker/ai-dev-brain-kit"
ISSUES_URL = f"https://github.com/{REPO}/issues/new/choose"
DISCUSSIONS_URL = f"https://github.com/{REPO}/discussions"


def run_feedback(config: BrainConfig, topic: str = "") -> None:
    if topic == "bug":
        _open_or_print(ISSUES_URL)
        print(f"Bug report form opened: {ISSUES_URL}")
        print("Tip: include version, platform, reproduction steps, and expected vs actual behavior.")
        print("Do NOT include secrets or credentials.")
    elif topic == "idea":
        _open_or_print(DISCUSSIONS_URL)
        print(f"Discussions opened: {DISCUSSIONS_URL}")
        print("Share ideas, questions, or general feedback.")
    else:
        print("AI Dev Brain — Feedback & Support")
        print()
        print(f"  Report a bug:     {ISSUES_URL}")
        print(f"  Ideas & questions: {DISCUSSIONS_URL}")
        print()
        print("Quick commands:")
        print("  brain feedback bug    — open bug report form")
        print("  brain feedback idea   — open GitHub Discussions")
        print()
        print("Please do not include secrets or credentials in bug reports.")


def _open_or_print(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        pass
