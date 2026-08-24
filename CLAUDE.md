# CLAUDE.md

Python CLI for searching and reading YouTube.

## Commands

```bash
uv sync
uv run pytest
uv run youtube-cli --help
```

## Architecture

- `core/` contains framework-neutral YouTube operations.
- `cli.py` defines the command hierarchy and calls the core.
- `files.py` writes transcript and comment results atomically under the OS temporary directory.
- `format.py` serializes terminal output as YAML.

YouTube access belongs in the core and goes through `yt-dlp` or `youtube-transcript-api`.

## Changes

- Keep CLI parsing and rendering out of the core modules.
- Use the shared video summary mapper for search, channel, and playlist results.
- Update README when commands or user-visible behavior change.
- Run the test suite and relevant live commands before committing.
