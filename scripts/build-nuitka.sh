#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
RELEASES="$ROOT/releases"
NUITKA="/tmp/nuitka-venv/bin/nuitka"

if [ ! -f "$NUITKA" ]; then
    echo "Nuitka not found at $NUITKA"
    echo "Run: python3 -m venv /tmp/nuitka-venv && /tmp/nuitka-venv/bin/pip install nuitka"
    exit 1
fi

mkdir -p "$RELEASES"

echo "=== Building Linux binary with Nuitka ==="
cd "$ROOT"

"$NUITKA" \
    --standalone \
    --onefile \
    --output-dir="$RELEASES/nuitka-build" \
    --output-filename=brain-linux-x86_64 \
    --python-flag=no_docstrings \
    --python-flag=-O \
    --python-flag=-m \
    --enable-plugin=no-qt \
    --noinclude-pytest-mode=nofollow \
    --noinclude-setuptools-mode=nofollow \
    brain 2>&1

# Nuitka outputs to output-dir with the output-filename
if [ -f "$RELEASES/nuitka-build/brain-linux-x86_64" ]; then
    mv "$RELEASES/nuitka-build/brain-linux-x86_64" "$RELEASES/brain-linux-x86_64"
    rm -rf "$RELEASES/nuitka-build"
fi

echo ""
echo "=== Generated SHA-256 ==="
cd "$RELEASES"
sha256sum brain-linux-x86_64 > brain-linux-x86_64.sha256
echo "SHA-256: $(sha256sum brain-linux-x86_64 | cut -d' ' -f1)"

echo ""
echo "=== Binary size ==="
ls -lh brain-linux-x86_64

echo ""
echo "=== Smoke test: version ==="
./brain-linux-x86_64 --version

echo ""
echo "=== Smoke test: doctor --offline ==="
./brain-linux-x86_64 doctor --offline || true

echo ""
echo "=== Build complete ==="
