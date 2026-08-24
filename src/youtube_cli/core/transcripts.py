from __future__ import annotations

from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi

from youtube_cli.files import video_directory, write_text

from .common import require_video_id
from .models import format_timestamp


def _fetch_transcript(video_id: str) -> Any:
    api = YouTubeTranscriptApi()
    try:
        return api.fetch(video_id)
    except Exception as original_error:
        try:
            available = list(api.list(video_id))
            if not available:
                raise original_error
            return available[0].fetch()
        except Exception:
            raise original_error


def get_transcript(video_id: str, timestamps: bool = False) -> dict[str, Any]:
    video_id = require_video_id(video_id)
    transcript = _fetch_transcript(video_id)
    snippets = list(transcript)
    if timestamps:
        content = "\n".join(
            f"[{format_timestamp(snippet.start)}] {snippet.text.strip()}"
            for snippet in snippets
            if snippet.text.strip()
        )
        filename = f"{video_id}-transcript-timestamps.txt"
    else:
        content = " ".join(
            snippet.text.strip() for snippet in snippets if snippet.text.strip()
        )
        filename = f"{video_id}-transcript.txt"
    content = f"{content.strip()}\n"
    path = video_directory(video_id) / filename
    write_text(path, content)
    return {
        "video_id": video_id,
        "language": getattr(transcript, "language_code", None),
        "generated": getattr(transcript, "is_generated", None),
        "timestamps": timestamps,
        "segments": len(snippets),
        "characters": len(content),
        "path": str(path),
    }
