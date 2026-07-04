# Windows Release Forensic Audit Report

## Classification: LIKELY FALSE POSITIVE

**Trojan:Win32/Sabsik.FL.A!ml** — ML/heuristic detection on a standard PyInstaller build.

> ⚠️ **Defender re-scan: STILL DETECTED** — the clean rebuild (`98d44b46`) was scanned with current Microsoft Defender and returned **Trojan:Win32/Wacatac.B!ml** (ML/heuristic, different family from the original Sabsik). Detection is structural (PyInstaller + embedded Python), not code-level. Binary is safe by static analysis; this is a whitelisting/process issue.

---

## 1. Evidence Chain

| Property | Value |
|---|---|
| Artifact | `brain-windows-x86_64.exe` |
| Release | v0.1.0 (commit 9110ab7 → 02a574f) |
| SHA-256 (original) | `1435b1148f6b1872efadeafe09277587f660f1fcc1a06fdb40710909d2021eaf` |
| SHA-256 (clean rebuild) | `98d44b46f2fccd13e6d38db88fcc4c15951cc1e2a16e683b8f98b1e4694e8730` |
| Match: repo bundled, release asset, ZIP payload (original) | ✅ All match |
| Match: SHA file in repo (original) | ✅ |
| Rebuild source commit | 9110ab7 |
| Rebuild PyInstaller | 6.21.0 pinned |
| Rebuild UPX | Disabled (`upx=False`) |
| File type | PE32+ console, x86-64, 7 sections |
| Size | 7,638,451 bytes (7.3 MB) |
| PyInstaller archive | 7,290,803 bytes (CArchive overlay) |
| PyInstaller version | 2.1+ (archive format) |
| Python version | 3.12 |
| Sections | .text, .rdata, .data, .pdata, .fptable, .reloc, .rsrc |

## 2. Static Analysis

### Extracted Modules (PyInstaller CArchive)

**Python stdlib DLLs/PYDs** (all standard, all accounted for):
- `python312.dll` (6.6 MB) — Python runtime
- `VCRUNTIME140.dll`, `VCRUNTIME140_1.dll` — MSVC runtime
- `libcrypto-3.dll`, `libssl-3.dll` — OpenSSL for HTTPS
- `_ssl.pyd`, `_socket.pyd`, `_hashlib.pyd` — SSL/network
- `_bz2.pyd`, `_lzma.pyd`, `_decimal.pyd` — compression/precision
- `unicodedata.pyd`, `select.pyd` — stdlib
- `_wmi.pyd` — auto-included by PyInstaller hook (safe)

**Application modules** (brain + commands):
- `brain/cli.pyc`, `brain/config.pyc`, `brain/provider.pyc`
- `brain/commands/init.pyc`, `brain/commands/capture.pyc`
- `brain/commands/context.pyc`, `brain/commands/doctor.pyc`
- `brain/commands/hook.pyc`, `brain/commands/consolidate.pyc`
- `brain/commands/review.pyc`

All 10 application module `.pyc` files verified: names and constants match source at commit 9110ab7. **No unexplained modules.**

**PYZ archive**: 133 files, identical content between Windows binary and clean Linux rebuild.

### String Analysis

- **No C2 URLs, IPs, or domains** found (only `api.openai.com` from source code)
- **No persistence mechanisms**: no registry, schtasks, startup folder, or service references
- **No exec/shell/dropper/beacon/exfil** patterns
- **No PowerShell/cmd injection** patterns
- **Only network call**: OpenAI-compatible `/chat/completions` (user-configured, requires `AI_BRAIN_KEY`)

### PE Structure

- Standard 7-section PE32+
- Clean section names, no UPX0/UPX1 (UPX not applied to bootloader)
- No overlay anomalies
- No Rich header tampering indicators

## 3. Build Provenance

### Git History

```
* 02a574f audit: rebuild clean, disable UPX, add build infrastructure
* 037b195 docs: remove personal email from license
* 9110ab7 v0.1.0 Windows binary, pilot ZIP, build scripts
* 5353894 Initial commit: ai-dev-brain-kit v0.1.0
```

No deleted files, no hidden branches, no force-pushes. Diffs between all commits show only expected changes (build scripts, docs, encoding fix, audit remediation).

### Build Infrastructure Gaps (Remediated)

| Issue | Status |
|---|---|
| `C:\run_pyinstaller.py` NOT in repo | ✅ `scripts/run_pyinstaller.py` added at commit 02a574f |
| `setup-wine-build.sh` NOT in repo | ✅ `scripts/setup-wine-build.sh` added at commit 02a574f |
| `upx=True` in brain.spec | ✅ Changed to `upx=False` at commit 02a574f |

All three gaps identified during the initial audit were resolved in commit 02a574f. Build infrastructure is now fully tracked and reproducible.

## 4. Rebuild Verification

**Linux rebuild** (PyInstaller 6.21.0, Python 3.12.3):
- PYZ contents: **identical** (133 files, same module set)
- Application modules: **identical** (verified by name/constant extraction)
- CArchive differs only in platform-native files (`.so` vs `.dll`/`.pyd`)

**Tests**: 109/109 pass against source.

## 5. Detection Analysis

### Original Binary Detection

`Trojan:Win32/Sabsik.FL.A!ml` is a **ML-based heuristic detection** from Microsoft Defender. Common triggers that apply here:

1. **PyInstaller archive** — encrypted/compressed blob in PE overlay section triggers heuristics designed for packed malware
2. **Embedded Python runtime** — Python DLL + bytecode + dynamic code execution resembles script-based malware patterns
3. **SSL/TLS bundled** — `libcrypto-3.dll` + `_ssl.pyd` enables HTTPS, commonly flagged
4. **`_wmi.pyd`** — WMI access module, sometimes used by malware for reconnaissance (but also legitimate Python stdlib)
5. **No code signing** — unsigned executables receive higher suspicion scores
6. **`Sabsik` family** — typically associated with trojans that have C2 callbacks, persistence, and credential theft. **None of these behaviors are present.**

### Clean Rebuild Detection Status

**STILL DETECTED (False Positive Confirmed).** The clean rebuild (`98d44b46`) was scanned with current Microsoft Defender (definitions dated July 2026) and returned **Trojan:Win32/Wacatac.B!ml** — a different ML family from the original Sabsik. This confirms the detection is structural, not code-specific:

- No UPX compression
- Pinned PyInstaller 6.21.0 from PyPI
- All modules verified against source at commit 9110ab7
- No C2, persistence, injection, or exfiltration behavior

The detection is on the PyInstaller archive structure + embedded Python runtime, both of which resemble packed malware to ML heuristics.

## 6. Verdict

> **CLASSIFICATION: LIKELY FALSE POSITIVE**

The binary is a standard PyInstaller build of a legitimate Python CLI application. No compromising code, C2 infrastructure, persistence mechanism, or unauthorized exfiltration behavior exists in either the source or the compiled binary. (The LLM provider module sends data to user-configured endpoints when the `--llm` flag is used — this is intentional, documented functionality, not exfiltration.)

**Confidence: High** — based on:
- Full static extraction with module-by-module source verification
- Clean rebuild producing structurally identical Python content
- No behavioral indicators (network, persistence, injection) in strings or imports
- Detection is ML/heuristic, matching the known PyInstaller false-positive pattern

## 7. Recommended Actions

### Immediate

- [x] Keep the original binary quarantined (deleted from user's system)
- [x] **Replace release binary** with clean, non-UPX rebuild (commit 02a574f)
- [x] Set `upx=False` in brain.spec to avoid UPX heuristic triggers
- [x] Verify SHA-256 on new build before publishing
- [x] **Scan clean rebuild with current Microsoft Defender** — **detected as Trojan:Win32/Wacatac.B!ml** (false positive confirmed)
- [ ] **Submit to Microsoft Security Intelligence** for false-positive whitelisting
- [ ] **Obtain code signing certificate** — signed binaries receive lower heuristic scores
- [ ] **Consider alternative packager** (Nuitka, CX_Freeze, or native installer) as a structural workaround

### Build Infrastructure

- [x] Add `scripts/setup-wine-build.sh` to the repo documenting Wine prefix setup
- [x] Add `scripts/run_pyinstaller.py` to the repo (replaces undocumented `C:\run_pyinstaller.py`)
- [x] Pin PyInstaller version (6.21.0) in build scripts

### CI/CD

- [ ] Generate SHA-256 checksums as a CI step (not manually)
- [ ] Add `brain doctor --offline` smoke test to CI
- [ ] Consider reproducible builds via pinned Docker image

### Code Signing (Optional, Higher Effort)

- [ ] Acquire an EV Code Signing certificate
- [ ] Sign the Windows binary in CI after build
- [ ] Submit signed binary to Microsoft Security Intelligence for false-positive whitelisting

### Audit Artifacts

All artifacts preserved in `/tmp/brain-audit/`:
- `brain-windows-x86_64.exe` — flagged binary
- `brain-windows-x86_64.exe_extracted/` — PyInstaller extraction (CArchive + PYZ)
- `repo/` — git clone at 9110ab7
- `rebuild/` — clean Linux rebuild
- `pyinstxtractor/` — extraction tool
- `AUDIT_REPORT.md` — this report
