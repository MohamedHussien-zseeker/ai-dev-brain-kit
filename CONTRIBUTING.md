# Contributing

## Development setup

AI Dev Brain Kit is built in Python and distributed as a standalone binary.

```bash
git clone https://github.com/MohamedHussien-zseeker/ai-dev-brain-kit.git
cd ai-dev-brain-kit
pip install -r requirements.txt
```

## Running tests

```bash
pytest tests/ -v
```

## Building

```bash
pyinstaller SaveSync.spec --noconfirm
```

## Release expectations

- All tests must pass before merge
- Releases are built via GitHub Actions
- Binaries are uploaded as release artifacts
- Checksums are generated for verification

## License

This project uses a proprietary license. See [LICENSE](LICENSE) for details.
