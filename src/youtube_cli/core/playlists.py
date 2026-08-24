from __future__ import annotations

from typing import Any

from .common import ydl
from .models import video_summary


def get_playlist_videos(playlist: str, limit: int = 50) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    url = playlist if playlist.startswith("http") else f"https://www.youtube.com/playlist?list={playlist}"
    options = {
        "extract_flat": True,
        "playlist_items": f"1:{limit}",
        "noplaylist": False,
    }
    with ydl(options) as client:
        result = client.extract_info(url, download=False)
    return [video_summary(entry) for entry in result.get("entries", []) if entry]
