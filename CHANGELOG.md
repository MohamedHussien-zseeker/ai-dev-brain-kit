# Changelog

## v0.2.0 — 2026-07-07

### Added
- `brain handoff` command — per-project session handoff with 5 fields
  - `show`, `now`, `done`, `next`, `watch`, `files`, `clear`
- `brain feedback` command — links to GitHub Issues and Discussions
- Nuitka-based build pipeline (replaces PyInstaller)

### Changed
- Zero external dependencies (Python stdlib only)
- 127 tests passing

### Platforms
- Linux x86_64
- Windows x86_64

---

## v0.1.0 — 2026-07-04

### Added
- Initial release
- Commands: `init`, `note`, `today`, `context`, `doctor`, `hook`, `consolidate`, `review`, `review-stats`
- Obsidian vault integration
- Claude Code stop hook
- PyInstaller-based builds
- 115 tests
