from __future__ import annotations

from typing import Any

from .common import video_url, ydl
from .models import video_metadata as map_video_metadata
from .models import video_summary


def search_videos(query: str, limit: int = 10) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        raise ValueError("query must not be empty")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    with ydl({"extract_flat": True, "playlist_items": f"1:{limit}"}) as client:
        result = client.extract_info(f"ytsearch{limit}:{query}", download=False)
    return [video_summary(entry) for entry in result.get("entries", []) if entry]


def get_video_metadata(video_id: str) -> dict[str, Any]:
    with ydl({"skip_download": True}) as client:
        result = client.extract_info(video_url(video_id), download=False)
    return map_video_metadata(result)
