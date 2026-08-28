from __future__ import annotations

from typing import Any

from .common import ydl
from .models import compact, video_summary


def get_playlist_videos(playlist: str, limit: int = 50) -> dict[str, Any]:
    playlist = playlist.strip()
    if not playlist:
        raise ValueError("playlist must not be empty")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    url = playlist if playlist.startswith("http") else f"https://www.youtube.com/playlist?list={playlist}"
    options = {
        "extract_flat": True,
        "playlist_items": f"1:{limit}",
        "noplaylist": False,
    }
    try:
        with ydl(options) as client:
            result = client.extract_info(url, download=False)
    except Exception:
        raise RuntimeError(f"Playlist unavailable: {playlist}") from None
    videos = [video_summary(entry) for entry in result.get("entries", []) if entry]
    return compact(
        {
            "id": result.get("id") or playlist,
            "title": result.get("title"),
            "channel": result.get("channel") or result.get("uploader"),
            "channel_id": result.get("channel_id") or result.get("uploader_id"),
            "url": result.get("webpage_url") or url,
            "video_count": result.get("playlist_count"),
            "videos": videos,
        }
    )
