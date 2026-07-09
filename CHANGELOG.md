# Changelog

## v0.2.1 — 2026-07-07

### Changed
- First closed-source release (Nuitka-compiled binary)
- Windows binary rebuilt with PyInstaller (Nuitka Windows cross-compilation in development)
- Public repository now distributes binaries only
- Added `brain feedback` command for Issues/Discussions links

### Platforms
- Linux x86_64 (Nuitka)
- Windows x86_64 (PyInstaller)

---

## v0.2.0 — 2026-07-07

### Added
- `brain handoff` command — per-project session handoff with 5 fields
  - `show`, `now`, `done`, `next`, `watch`, `files`, `clear`
- `brain feedback` command — links to GitHub Issues and Discussions

### Changed
- Nuitka-based build pipeline

---

## v0.1.0 — 2026-07-04

### Added
- Initial public release (open source)
- Commands: `init`, `note`, `today`, `context`, `doctor`, `hook`, `consolidate`, `review`, `review-stats`
- Obsidian vault integration
- Claude Code stop hook
- PyInstaller-based builds
- 115 tests
