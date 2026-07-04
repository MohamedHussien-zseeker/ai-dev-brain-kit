#!/usr/bin/env bash
# Build brain-windows-x86_64.exe via wine + PyInstaller
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
RELEASES="$ROOT/releases"
mkdir -p "$RELEASES"

WINEPREFIX="${WINEPREFIX:-/tmp/wine-brain}"
PYTHON="${PYTHON:-C:\Python312\python.exe}"

echo "=== Building Windows binary ==="
echo "WINEPREFIX=$WINEPREFIX"

# Ensure wine prefix exists
if [ ! -d "$WINEPREFIX/drive_c/Python312" ]; then
    echo "ERROR: Python 3.12 not found in $WINEPREFIX"
    echo "Run scripts/setup-wine-build.sh first"
    exit 1
fi

# Copy source + build scripts to wine drive
rm -rf "$WINEPREFIX/drive_c/brain-build"
mkdir -p "$WINEPREFIX/drive_c/brain-build"
cp -r "$ROOT/brain" "$WINEPREFIX/drive_c/brain-build/"
cp "$ROOT/brain.spec" "$WINEPREFIX/drive_c/brain-build/"
cp "$ROOT/scripts/run_pyinstaller.py" "$WINEPREFIX/drive_c/brain-build/"

# Run PyInstaller (uses scripts/run_pyinstaller.py)
wine cmd /c "$PYTHON C:\brain-build\run_pyinstaller.py" 2>&1

# Copy artifacts
cp "$WINEPREFIX/drive_c/brain-build/dist/brain.exe" "$RELEASES/brain-windows-x86_64.exe"

echo ""
echo "=== Generated SHA-256 ==="
cd "$RELEASES"
sha256sum brain-windows-x86_64.exe > brain-windows-x86_64.sha256
echo "SHA-256: $(cut -d' ' -f1 brain-windows-x86_64.sha256)"

echo ""
echo "=== Binary size ==="
ls -lh brain-windows-x86_64.exe

echo ""
echo "=== Smoke tests (wine) ==="
# Clean test env
rm -rf "$WINEPREFIX/drive_c/brain-test-vault" "$WINEPREFIX/drive_c/brain-test-config"

cat > "$WINEPREFIX/drive_c/_test_win.bat" << 'BAT'
@echo off
setlocal
set BRAIN_CONFIG_DIR=C:\brain-test-config
set BRAIN_VAULT_PATH=C:\brain-test-vault
echo --- version ---
C:\brain-build\dist\brain.exe --version
echo --- init ---
C:\brain-build\dist\brain.exe init --vault C:\brain-test-vault --non-interactive
echo --- doctor ---
C:\brain-build\dist\brain.exe doctor --offline
echo --- note ---
C:\brain-build\dist\brain.exe note "Windows build smoke test"
echo --- context ---
C:\brain-build\dist\brain.exe context
echo --- consolidate ---
C:\brain-build\dist\brain.exe consolidate
echo --- done ---
BAT

wine cmd /c "C:\_test_win.bat" 2>&1 | grep -v "^$" | grep -v "err:winediag" | grep -v "err:systray" | grep -v "0024:err"
echo ""
echo "=== Windows build complete ==="
