# youtube-cli

CLI for searching and reading YouTube. Search videos, inspect video and channel metadata, save transcripts and comments to local files, and browse channel or playlist videos.

## Install

Run directly with `uvx`:

```bash
uvx --from git+https://github.com/TiranSpierer/youtube-cli.git youtube-cli --help
```

Or install it:

```bash
uv tool install git+https://github.com/TiranSpierer/youtube-cli.git
```

---

<details>
<summary>Video commands</summary>

```bash
youtube-cli video search "iphone 16" --limit 10
youtube-cli video metadata <video-id>
youtube-cli video transcript <video-id>
youtube-cli video transcript <video-id> --timestamps
youtube-cli video transcript <video-id> --language es
youtube-cli video comments <video-id> --sort top --limit 50
youtube-cli video comments <video-id> --no-replies
```

Transcripts are saved as text under the OS temporary directory. Comments are saved as structured YAML. Both commands print the resulting file path.

Transcripts default to the video's original spoken language. Use `--language` to select another available caption track.

</details>

<details>
<summary>Channel commands</summary>

```bash
youtube-cli channel metadata @mkbhd
youtube-cli channel videos @mkbhd --limit 20
```

</details>

<details>
<summary>Playlist commands</summary>

```bash
youtube-cli playlist videos <playlist-url-or-id> --limit 50
```

</details>

<details>
<summary>Output</summary>

Commands print compact YAML.

Large results are written under:

```text
<os-temp>/youtube-cli/<video-id>/
```

</details>

<details>
<summary>Requirements</summary>

- Python 3.11+
- No YouTube API key

YouTube access uses `yt-dlp` and `youtube-transcript-api`.

</details>

<details>
<summary>Local development</summary>

```bash
uv sync
uv run pytest
uv run youtube-cli --help
```

</details>
