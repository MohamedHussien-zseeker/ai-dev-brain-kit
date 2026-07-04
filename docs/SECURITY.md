# Security

## Binary Integrity

All releases include a SHA-256 checksum file. The install script verifies the checksum before completing installation.

```bash
# Manual verification
sha256sum brain-linux-x86_64
cat brain-linux-x86_64.sha256
# Compare outputs
```

## API Key Safety

Brain reads the LLM API key from the `AI_BRAIN_KEY` environment variable. It is **never** written to disk by brain commands. Best practices:

```bash
# Set in your shell profile
export AI_BRAIN_KEY="sk-..."

# Or use a password manager
export AI_BRAIN_KEY="$(op read op://Personal/OpenAI/api-key)"

# Or use .env (never commit it)
echo "AI_BRAIN_KEY=sk-..." >> ~/.brain/.env
```

## File Permissions

Brain creates files and directories with default OS permissions. The config directory at `~/.brain/` stores only metadata paths — no secrets. If you store sensitive notes, ensure your vault directory has appropriate permissions:

```bash
chmod 700 ~/my-brain
```

## Network

Brain does not make network connections unless you:
1. Run `brain consolidate --llm` — sends note content to configured LLM provider
2. Run an install script — downloads binary over HTTPS

All network calls use HTTPS. The default provider URL is `https://api.openai.com/v1`. Custom URLs are supported for self-hosted models.

## Dependencies

The binary is a standalone PyInstaller build with zero external runtime dependencies. It bundles only the Python standard library plus the brain package source. No dynamic loading of untrusted code.

## Supply Chain

- Source code is readable at the project repository
- Binaries are built from tagged commits
- SHA-256 checksums are published alongside each release
- Build scripts are in `scripts/build.sh` for reproducibility
