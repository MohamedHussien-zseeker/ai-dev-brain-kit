#!/usr/bin/env bash
# Setup Wine prefix for Windows PyInstaller builds
set -euo pipefail

WINEPREFIX="${WINEPREFIX:-/tmp/wine-brain}"
PYTHON_VERSION="3.12.3"
PYTHON_INSTALLER="python-${PYTHON_VERSION}-amd64.exe"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/${PYTHON_INSTALLER}"
PYINSTALLER_VERSION="6.21.0"

echo "=== Setting up Wine prefix: $WINEPREFIX ==="

# Create Wine prefix
export WINEPREFIX
if [ ! -d "$WINEPREFIX" ]; then
    wineboot -u 2>/dev/null || true
fi

# Install Python if not present
if [ ! -f "$WINEPREFIX/drive_c/Python312/python.exe" ]; then
    echo "=== Downloading Python $PYTHON_VERSION ==="
    wget -q "$PYTHON_URL" -O "/tmp/$PYTHON_INSTALLER"
    echo "=== Installing Python (silent) ==="
    wine cmd /c "$PYTHON_INSTALLER /quiet InstallAllUsers=0 TargetDir=C:\\Python312 PrependPath=1" 2>&1
    rm "/tmp/$PYTHON_INSTALLER"
fi

# Install PyInstaller
echo "=== Installing PyInstaller $PYINSTALLER_VERSION ==="
wine cmd /c "C:\\Python312\\python.exe -m pip install pyinstaller==${PYINSTALLER_VERSION}" 2>&1

echo "=== Wine build environment ready ==="
echo "WINEPREFIX=$WINEPREFIX"
echo "Python: C:\\Python312\\python.exe"
