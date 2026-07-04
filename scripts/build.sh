#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
RELEASES="$ROOT/releases"

mkdir -p "$RELEASES"

echo "=== Building Linux binary ==="
cd "$ROOT"
pyinstaller --clean \
  --onefile \
  --name brain \
  --distpath "$RELEASES" \
  --workpath /tmp/pyibuild \
  --hidden-import brain.commands.consolidate \
  --hidden-import brain.commands.review \
  --hidden-import brain.commands.context \
  --hidden-import brain.commands.capture \
  --hidden-import brain.commands.doctor \
  --hidden-import brain.commands.hook \
  --hidden-import brain.commands.init \
  --hidden-import brain.provider \
  --hidden-import brain.config \
  --exclude tkinter \
  --exclude PyQt5 \
  --exclude PySide2 \
  --exclude PySide6 \
  --exclude matplotlib \
  --exclude numpy \
  --exclude pandas \
  --exclude PIL \
  --exclude cv2 \
  --exclude scipy \
  --exclude yaml \
  brain/__main__.py 2>&1

mv "$RELEASES/brain" "$RELEASES/brain-linux-x86_64"

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
echo "=== Windows binary already built ==="
echo ""
echo "Windows binary: releases/brain-windows-x86_64.exe"
echo "Windows SHA-256: releases/brain-windows-x86_64.sha256"
echo ""
echo "=== Build complete ==="
echo ""
echo "To rebuild the Windows binary on this host:"
echo "  export WINEPREFIX=/tmp/wine-brain && bash scripts/build-windows.sh"
