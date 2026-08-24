from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml


def video_directory(video_id: str) -> Path:
    path = Path(tempfile.gettempdir()) / "youtube-cli" / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def write_yaml(path: Path, content: object) -> None:
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            content,
            handle,
            allow_unicode=True,
            sort_keys=False,
            width=1000,
        )
    os.replace(temporary, path)
