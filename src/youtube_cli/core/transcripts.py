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


class TranscriptLanguageUnavailable(ValueError):
    pass


LANGUAGE_ALIASES = {"he": "iw", "id": "in", "yi": "ji"}


def _language_matches(available: str, requested: str) -> bool:
    available = LANGUAGE_ALIASES.get(available.lower(), available.lower())
    requested = LANGUAGE_ALIASES.get(requested.lower(), requested.lower())
    return available == requested or available.startswith(f"{requested}-")


def _select_transcript(available: list[Any], language: str | None = None) -> Any:
    if language is not None:
        selected = next(
            (
                transcript
                for transcript in available
                if _language_matches(transcript.language_code, language)
                and not transcript.is_generated
            ),
            None,
        ) or next(
            (
                transcript
                for transcript in available
                if _language_matches(transcript.language_code, language)
            ),
            None,
        )
        if selected is None:
            languages = ", ".join(dict.fromkeys(t.language_code for t in available))
            raise TranscriptLanguageUnavailable(
                f"Transcript language '{language}' is unavailable. Available: {languages or 'none'}."
            )
        return selected

    generated = next((transcript for transcript in available if transcript.is_generated), None)
    if generated is None:
        return available[0]
    return next(
        (
            transcript
            for transcript in available
            if transcript.language_code == generated.language_code
            and not transcript.is_generated
        ),
        generated,
    )


def _fetch_transcript(video_id: str, language: str | None = None) -> Any:
    api = YouTubeTranscriptApi()
    available = list(api.list(video_id))
    if not available:
        raise TranscriptLanguageUnavailable("No transcript languages are available.")
    return _select_transcript(available, language).fetch()


def get_transcript(
    video_id: str,
    timestamps: bool = False,
    language: str | None = None,
) -> dict[str, Any]:
    video_id = require_video_id(video_id)
    try:
        transcript = _fetch_transcript(video_id, language)
    except TranscriptLanguageUnavailable:
        raise
    except TranscriptsDisabled:
        raise RuntimeError(f"No captions or transcript available for {video_id}.") from None
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
        suffix = "-timestamps"
    else:
        content = "\n".join(text for text in cleaned if text)
        suffix = ""
    content = f"{content.strip()}\n"
    selected_language = getattr(transcript, "language_code", "unknown")
    filename = f"{video_id}-transcript-{selected_language}{suffix}.txt"
    path = video_directory(video_id) / filename
    write_text(path, content)
    return {
        "video_id": video_id,
        "language": selected_language,
        "generated": getattr(transcript, "is_generated", None),
        "timestamps": timestamps,
        "segments": len(snippets),
        "characters": len(content),
        "path": str(path),
    }
