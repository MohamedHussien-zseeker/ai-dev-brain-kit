============================================================
AI Dev Brain Kit — Windows Pilot Delivery
v0.1.0 — July 2026
============================================================

Thank you for joining the AI Dev Brain Kit pilot!

This package contains everything you need to get started on
Windows 10/11 (x86_64).

WHAT'S INCLUDED:
  brain-windows-x86_64.exe   The Brain CLI binary (7.3 MB)
  QUICKSTART.md              Install & first workflow guide
  LICENSE                    Proprietary license terms

QUICK START:
  1. Create a directory (e.g. C:\tools\brain)
  2. Place brain-windows-x86_64.exe there and rename to brain.exe
  3. Add that directory to your PATH (User-level)
  4. Open a NEW PowerShell window
  5. Run:  brain init --vault "$env:USERPROFILE\brain-vault"
  6. Run:  brain doctor --offline
  7. Run:  brain note "Hello from Windows!"
  8. Run:  brain today

KNOWN LIMITATIONS:
  - "brain context --clipboard" uses Linux clipboard tools
    (clip.exe support not yet wired)
  - Binary cross-compiled (wine on Linux); native Windows
    build testing is planned
  - x86_64 only (no ARM64 support)

REPORTING ISSUES:
  Please report any issues to your setup engineer directly,
  including your Windows version and any error messages.

SHA-256: 1435b1148f6b1872efadeafe09277587f660f1fcc1a06fdb40710909d2021eaf
