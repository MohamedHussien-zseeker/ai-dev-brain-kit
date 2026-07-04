# Privacy

## Data Residency

Brain CLI is a **local-first** tool. All data — notes, daily logs, decisions, knowledge pages, and review proposals — is stored **on your own machine** in your vault directory. No data is ever sent to external servers unless you explicitly configure an LLM provider.

## LLM Provider Integration

The `brain consolidate --llm` feature sends note content to your configured LLM provider only when you invoke it. Brain uses the OpenAI-compatible protocol and can work with any provider:

- **OpenAI** — data leaves your machine
- **Local models** (Ollama, LM Studio) — data stays on your machine
- **Self-hosted** — data stays on your network

The `--llm` flag is always opt-in. The default `brain consolidate` uses local heuristics only and never sends content anywhere.

## What Brain Collects

Brain does **not**:
- Phone home or call analytics endpoints
- Track usage
- Collect crash reports
- Send diagnostic data
- Use a telemetry system

## Configuration Storage

Your config file at `~/.brain/config.json` contains:
- Your vault path (local filesystem path)
- Your provider URL and model name (optional)
- Your `AI_BRAIN_KEY` is read from the environment, never stored in config

## Third-Party Access

No third party has access to your vault or config. The software is open source and the binary is reproducible from source.

## Updates

Brain does not auto-update. Install scripts verify SHA-256 checksums before installing. Updates are manual and cryptographically verified.
