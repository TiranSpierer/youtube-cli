from __future__ import annotations

from typing import Any

from youtube_cli.files import video_directory, write_yaml

from .common import video_url, ydl
from .models import compact


def _comment(entry: dict[str, Any]) -> dict[str, Any]:
    return compact(
        {
            "id": entry.get("id"),
            "parent": entry.get("parent"),
            "author": entry.get("author"),
            "author_id": entry.get("author_id"),
            "text": entry.get("text"),
            "likes": entry.get("like_count"),
            "replies": entry.get("reply_count"),
            "published": entry.get("time_text"),
            "timestamp": entry.get("timestamp"),
            "author_is_uploader": entry.get("author_is_uploader"),
            "is_favorited": entry.get("is_favorited"),
        }
    )


def get_comments(
    video_id: str,
    sort: str = "top",
    limit: int = 50,
    replies: bool = True,
) -> dict[str, Any]:
    if sort not in {"top", "new"}:
        raise ValueError("sort must be 'top' or 'new'")
    if limit < 1:
        raise ValueError("limit must be at least 1")
    max_comments = (
        [str(limit), str(limit), str(limit), "3", "all"]
        if replies
        else [str(limit), str(limit), "0", "0", "1"]
    )
    options = {
        "skip_download": True,
        "getcomments": True,
        "extractor_args": {
            "youtube": {
                "comment_sort": [sort],
                "max_comments": max_comments,
            }
        },
    }
    with ydl(options) as client:
        result = client.extract_info(video_url(video_id), download=False)
    comments = [_comment(comment) for comment in (result.get("comments") or [])]
    reply_suffix = "with-replies" if replies else "without-replies"
    path = video_directory(video_id) / f"{video_id}-comments-{sort}-{reply_suffix}.yml"
    write_yaml(
        path,
        {
            "video_id": video_id,
            "sort": sort,
            "requested": limit,
            "retrieved": len(comments),
            "replies": replies,
            "comments": comments,
        },
    )
    return {
        "video_id": video_id,
        "sort": sort,
        "requested": limit,
        "retrieved": len(comments),
        "replies": replies,
        "path": str(path),
    }
