# Quickstart

## Install

**Linux:**
```bash
curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash
source ~/.bashrc
```

**Windows (PowerShell):**
```powershell
powershell -c "Invoke-WebRequest -Uri https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.ps1 -OutFile install.ps1; .\install.ps1"
```

Manual download: grab `brain-linux-x86_64` or `brain-windows-x86_64.exe` from [releases](https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases), place it somewhere on your PATH, and run `brain --version` to confirm.

## Initialize a Vault

**Linux/macOS:**
```bash
brain init --vault ~/my-brain
# Or let brain create a fresh vault in the current directory
brain init
```

**Windows (PowerShell):**
```powershell
brain init --vault "$env:USERPROFILE\brain-vault"
# Or let brain create a fresh vault in the current directory
brain init
```

## Daily Workflow

```bash
# Quick capture
brain note "Remember to check the API rate limits"

# Daily log
brain today

# Build context for your next AI session
brain context --clipboard
```

## Consolidate and Review

```bash
# Stage inbox items for review
brain consolidate

# Review and approve/reject proposals
brain review

# Check review stats
brain review-stats
```

## Health Check

```bash
brain doctor --offline
```
