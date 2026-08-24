from __future__ import annotations

import re
from typing import Any

import yt_dlp

VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

BASE_OPTIONS: dict[str, Any] = {
    "quiet": True,
    "no_warnings": True,
    "noplaylist": True,
}


def require_video_id(value: str) -> str:
    if not VIDEO_ID_PATTERN.fullmatch(value):
        raise ValueError("video_id must be an 11-character YouTube video ID")
    return value


def video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={require_video_id(video_id)}"


def normalize_channel(value: str) -> str:
    value = value.strip().rstrip("/")
    if value.startswith("https://") or value.startswith("http://"):
        return value
    if not value.startswith("@"):
        value = f"@{value}"
    return f"https://www.youtube.com/{value}"


def ydl(options: dict[str, Any] | None = None) -> yt_dlp.YoutubeDL:
    return yt_dlp.YoutubeDL({**BASE_OPTIONS, **(options or {})})
