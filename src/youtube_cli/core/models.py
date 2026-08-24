from __future__ import annotations

from typing import Any


def compact(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            key: compact(value)
            for key, value in data.items()
            if value is not None and value != "" and value != [] and value != {}
        }
    if isinstance(data, list):
        return [compact(value) for value in data]
    return data


def format_duration(seconds: int | float | None) -> str | None:
    if seconds is None:
        return None
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_timestamp(seconds: int | float) -> str:
    return format_duration(seconds) or "0:00"


def video_summary(entry: dict[str, Any]) -> dict[str, Any]:
    video_id = entry.get("id") or ""
    url = entry.get("webpage_url") or entry.get("url")
    if not isinstance(url, str) or not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={video_id}"
    live_status = entry.get("live_status")
    return compact(
        {
            "id": video_id,
            "title": entry.get("title"),
            "unavailable": True if not entry.get("title") else None,
            "channel": entry.get("channel") or entry.get("uploader"),
            "channel_id": entry.get("channel_id"),
            "channel_url": entry.get("channel_url") or entry.get("uploader_url"),
            "duration": format_duration(entry.get("duration")),
            "duration_seconds": entry.get("duration"),
            "views": entry.get("view_count"),
            "live_status": live_status if live_status != "not_live" else None,
            "upload_date": entry.get("upload_date"),
            "url": url,
        }
    )


def video_metadata(entry: dict[str, Any]) -> dict[str, Any]:
    chapters = [
        compact(
            {
                "title": chapter.get("title"),
                "start": format_timestamp(chapter.get("start_time", 0)),
                "start_seconds": chapter.get("start_time"),
                "end": format_timestamp(chapter["end_time"])
                if chapter.get("end_time") is not None
                else None,
            }
        )
        for chapter in entry.get("chapters") or []
    ]
    return compact(
        {
            **video_summary(entry),
            "likes": entry.get("like_count"),
            "comments": entry.get("comment_count"),
            "language": entry.get("language"),
            "concurrent_viewers": entry.get("concurrent_view_count"),
            "description": entry.get("description"),
            "tags": entry.get("tags"),
            "categories": entry.get("categories"),
            "chapters": chapters,
            "thumbnail": entry.get("thumbnail"),
            "availability": entry.get("availability"),
            "live_status": entry.get("live_status"),
            "age_limit": entry.get("age_limit"),
        }
    )
