from __future__ import annotations

import os
import tempfile
from pathlib import Path

import yaml

from youtube_cli.format import _ReadableDumper


def video_directory(video_id: str) -> Path:
    path = Path(tempfile.gettempdir()) / "youtube-cli" / video_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_yaml(path: Path, content: object) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            yaml.dump(
                content,
                handle,
                Dumper=_ReadableDumper,
                allow_unicode=True,
                sort_keys=False,
                width=1000,
            )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
