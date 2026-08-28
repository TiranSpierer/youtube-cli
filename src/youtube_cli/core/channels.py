from __future__ import annotations

from typing import Any

from .common import normalize_channel, ydl
from .models import compact, video_summary


def get_channel_metadata(channel: str) -> dict[str, Any]:
    url = normalize_channel(channel)
    try:
        with ydl({"extract_flat": True, "playlist_items": "0:0", "noplaylist": False}) as client:
            try:
                result = client.extract_info(f"{url}/videos", download=False)
            except Exception:
                result = client.extract_info(url, download=False)
    except Exception:
        raise RuntimeError(f"Channel unavailable: {channel}") from None
    return compact(
        {
            "id": result.get("channel_id") or result.get("id"),
            "name": result.get("channel") or result.get("uploader") or result.get("title"),
            "url": result.get("channel_url") or url,
            "subscribers": result.get("channel_follower_count"),
            "description": result.get("description"),
            "video_count": result.get("playlist_count"),
        }
    )


def get_channel_videos(
    channel: str,
    limit: int = 20,
) -> list[dict[str, Any]]:
    if limit < 1:
        raise ValueError("limit must be at least 1")
    url = normalize_channel(channel)
    options = {
        "extract_flat": True,
        "playlist_items": f"1:{limit}",
        "noplaylist": False,
    }
    try:
        with ydl(options) as client:
            result = client.extract_info(f"{url}/videos", download=False)
    except Exception:
        raise RuntimeError(f"Channel unavailable: {channel}") from None
    channel_name = result.get("channel") or result.get("uploader") or result.get("title")
    channel_id = result.get("channel_id")
    channel_url = result.get("channel_url") or url
    videos = []
    for entry in result.get("entries", []):
        if not entry:
            continue
        enriched = {
            **entry,
            "channel": entry.get("channel") or channel_name,
            "channel_id": entry.get("channel_id") or channel_id,
            "channel_url": entry.get("channel_url") or channel_url,
        }
        videos.append(video_summary(enriched))
    return videos
