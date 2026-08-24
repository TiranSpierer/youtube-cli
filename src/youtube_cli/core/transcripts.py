from __future__ import annotations

from typing import Any

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    AgeRestricted,
    IpBlocked,
    NoTranscriptFound,
    PoTokenRequired,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
)

from youtube_cli.files import video_directory, write_text

from .common import require_video_id
from .models import format_timestamp


def _fetch_transcript(video_id: str) -> Any:
    api = YouTubeTranscriptApi()
    try:
        return api.fetch(video_id)
    except Exception:
        available = list(api.list(video_id))
        if not available:
            raise
        transcript = next(
            (candidate for candidate in available if candidate.is_generated),
            available[0],
        )
        return transcript.fetch()


def get_transcript(video_id: str, timestamps: bool = False) -> dict[str, Any]:
    video_id = require_video_id(video_id)
    try:
        transcript = _fetch_transcript(video_id)
    except TranscriptsDisabled:
        raise RuntimeError(f"No transcript available for {video_id}: subtitles are disabled.") from None
    except NoTranscriptFound:
        raise RuntimeError(f"No transcript available for {video_id}.") from None
    except VideoUnavailable:
        raise RuntimeError(f"Video unavailable: {video_id}.") from None
    except AgeRestricted:
        raise RuntimeError(f"Transcript unavailable for age-restricted video {video_id}.") from None
    except (IpBlocked, RequestBlocked):
        raise RuntimeError("YouTube blocked the transcript request; retry later or from another network.") from None
    except PoTokenRequired:
        raise RuntimeError(f"Transcript retrieval requires a YouTube proof-of-origin token for {video_id}.") from None
    except Exception as error:
        raise RuntimeError(f"Transcript retrieval failed for {video_id}: {type(error).__name__}.") from None
    snippets = list(transcript)
    cleaned = [" ".join(snippet.text.split()) for snippet in snippets]
    if timestamps:
        content = "\n".join(
            f"[{format_timestamp(snippet.start)}] {text}"
            for snippet, text in zip(snippets, cleaned, strict=True)
            if text
        )
        filename = f"{video_id}-transcript-timestamps.txt"
    else:
        content = "\n".join(text for text in cleaned if text)
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
