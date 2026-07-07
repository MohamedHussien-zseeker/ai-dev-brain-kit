# AI Dev Brain

A local-first memory system for solo developers. Capture notes, log daily
activity, build session context for AI tools, and consolidate raw captures
into durable knowledge — all on your own machine.

Handoff between AI sessions with a single command — no more re-explaining
your project every time you start fresh.

## Features

- **Session handoff** — `brain handoff now "task"` + `brain handoff show`
  between sessions. 5 fields, 15 lines max. No context degradation.
- **Quick capture** — `brain note "remember this"` from anywhere
- **Daily logs** — `brain today` appends to your daily journal
- **AI context** — `brain context --clipboard` builds a prompt-ready summary
  of recent activity for your AI coding session
- **Consolidate & review** — stage inbox items, review interactively, approve
  or reject — no data leaves your machine unless you opt in
- **Claude Code hook** — auto-capture session summaries when Claude stops
- **Zero telemetry** — no phone-home, no analytics, no accounts

## Download

Download the latest binary for your platform from the
[releases page](https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases).

Verify the SHA-256 checksum before running:

```bash
sha256sum -c brain-linux-x86_64.sha256
chmod +x brain-linux-x86_64
./brain-linux-x86_64 --version
```

Install scripts (auto-download + PATH setup):

```bash
# Linux
curl -fsSL https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.sh | bash
source ~/.bashrc

# Windows (PowerShell)
powershell -c "Invoke-WebRequest -Uri https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit/releases/latest/download/install.ps1 -OutFile install.ps1; .\install.ps1"
```

Full install details: [docs/QUICKSTART.md](docs/QUICKSTART.md)

## Quick Start

```bash
# Initialize a vault
brain init --vault ~/my-brain

# Set your current task (creates HANDOFF.md)
brain handoff now "Build login flow"

# At end of session
brain handoff done "Finished auth middleware"
brain handoff next "Add tests"
brain handoff watch "Edge case: null token crashes"

# Next session — full context in 10 lines
brain handoff show
```

## Commands

| Command | Description |
|---|---|
| `brain handoff` | Per-project session handoff (now/done/next/watch/files) |
| `brain init` | Create vault and configuration |
| `brain note <text>` | Capture a quick note |
| `brain today` | Daily log entry |
| `brain context` | Build session context from vault |
| `brain doctor` | Health check |
| `brain consolidate` | Stage inbox items for review |
| `brain review` | Review proposals interactively |
| `brain review-stats` | Pending/approved/rejected counts |
| `brain hook install` | Install Claude Code stop hook |
| `brain feedback` | Report bugs or share ideas |

## Privacy

- **Local-first**: all data stays in your vault directory
- **No telemetry**: brain never phones home
- **LLM is opt-in**: `--llm` flag required to send content to any provider
- **SHA-256**: all releases are checksum-verified

See [docs/PRIVACY.md](docs/PRIVACY.md) and [docs/SECURITY.md](docs/SECURITY.md).

## Documentation

| Document | Description |
|---|---|
| [QUICKSTART.md](docs/QUICKSTART.md) | Install & first workflow |
| [CUSTOMER_HANDBOOK.md](docs/CUSTOMER_HANDBOOK.md) | What pilot customers get |
| [PRIVACY.md](docs/PRIVACY.md) | Data handling & privacy |
| [SECURITY.md](docs/SECURITY.md) | Binary integrity, key safety |
| [REMOTE_INSTALL.md](docs/REMOTE_INSTALL.md) | Remote setup instructions |
| [UNINSTALL.md](docs/UNINSTALL.md) | How to remove |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [EULA.md](EULA.md) | Binary software license |

## License

The AI Dev Brain binary is distributed under the terms of [EULA.md](EULA.md).
This repository does not include source code.
