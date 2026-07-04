#!/usr/bin/env bash
set -euo pipefail

# Brain CLI — Linux installer
# Usage: curl -fsSL https://github.com/owner/repo/releases/latest/download/install.sh | bash
#        bash install.sh [--version v0.1.0] [--dir ~/.local/bin]

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- defaults ---
REPO="MohamedHussien-zseeker/ai-dev-brain-kit"
VERSION="v0.1.0"
INSTALL_DIR="${HOME}/.local/bin"
CONFIG_DIR="${HOME}/.brain"
VERIFY=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    --dir) INSTALL_DIR="$2"; shift 2 ;;
    --no-verify) VERIFY=0; shift ;;
    --help) echo "Usage: install.sh [--version vX.Y.Z] [--dir <path>] [--no-verify]"; exit 0 ;;
    *) error "Unknown option: $1"; exit 1 ;;
  esac
done

ARCH="$(uname -m)"
case "$ARCH" in
  x86_64|amd64)  ARCH="x86_64" ;;
  aarch64|arm64) ARCH="aarch64" ;;
  *) error "Unsupported architecture: $ARCH"; exit 1 ;;
esac

BINARY_NAME="brain-linux-${ARCH}"
BINARY_URL="https://github.com/${REPO}/releases/download/${VERSION}/${BINARY_NAME}"
CHECKSUM_URL="${BINARY_URL}.sha256"
INSTALL_PATH="${INSTALL_DIR}/brain"

# --- step 1: create install dir ---
mkdir -p "$INSTALL_DIR"
info "Install target: $INSTALL_DIR"

# --- step 2: download binary ---
if command -v curl &>/dev/null; then
  DL="curl -fsSL"
elif command -v wget &>/dev/null; then
  DL="wget -qO-"
else
  error "Neither curl nor wget found. Install one and retry."
  exit 1
fi

info "Downloading $BINARY_NAME..."
if ! $DL "$BINARY_URL" > "/tmp/${BINARY_NAME}.tmp"; then
  error "Download failed. Check version and network."
  exit 1
fi
mv "/tmp/${BINARY_NAME}.tmp" "$INSTALL_PATH"
chmod +x "$INSTALL_PATH"
info "Downloaded: $INSTALL_PATH"

# --- step 3: verify checksum ---
if [[ "$VERIFY" -eq 1 ]]; then
  info "Verifying SHA-256..."
  EXPECTED="$($DL "$CHECKSUM_URL" 2>/dev/null | awk '{print $1}')"
  if [[ -z "$EXPECTED" ]]; then
    warn "Could not fetch checksum; skipping verification."
  else
    ACTUAL="$(sha256sum "$INSTALL_PATH" | awk '{print $1}')"
    if [[ "$EXPECTED" != "$ACTUAL" ]]; then
      error "Checksum mismatch! Expected $EXPECTED, got $ACTUAL"
      rm -f "$INSTALL_PATH"
      exit 1
    fi
    info "Checksum verified: $ACTUAL"
  fi
fi

# --- step 4: create config directory (preserve existing) ---
mkdir -p "$CONFIG_DIR"
if [[ ! -f "$CONFIG_DIR/config.json" ]]; then
  cat > "$CONFIG_DIR/config.json" <<'EOF'
{
  "version": 1,
  "vaultPath": "",
  "provider": "openai-compatible",
  "baseUrl": "",
  "model": "",
  "captureMode": "approval-required"
}
EOF
  info "Default config created at $CONFIG_DIR/config.json"
else
  info "Existing config preserved at $CONFIG_DIR/config.json"
fi

# --- step 5: ensure install dir is on PATH ---
case ":$PATH:" in
  *:"$INSTALL_DIR":*) ;;
  *)
    SHELL_RC="${HOME}/.bashrc"
    if [[ "$SHELL" == *zsh* ]]; then SHELL_RC="${HOME}/.zshrc"; fi
    echo "" >> "$SHELL_RC"
    echo "# Brain CLI" >> "$SHELL_RC"
    echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> "$SHELL_RC"
    info "Added $INSTALL_DIR to PATH in $SHELL_RC"
    info "Run 'source $SHELL_RC' or restart your shell"
    ;;
esac

# --- step 6: verify installation ---
if [[ "$VERIFY" -eq 1 ]]; then
  info "Verifying installation..."
  INSTALLED="$("$INSTALL_PATH" --version 2>&1)" && info "$INSTALLED" || warn "Binary at $INSTALL_PATH but version check failed"
  "$INSTALL_PATH" doctor --offline 2>&1 || true
fi

info "Installation complete."
echo ""
echo "  brain --version"
echo "  brain doctor --offline"
echo "  brain init"
echo "  brain note 'your quick thought'"
echo "  brain today"
echo "  brain context"
echo ""
