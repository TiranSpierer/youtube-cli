from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import yaml
from youtube_transcript_api._errors import TranscriptsDisabled

from youtube_cli.core.channels import get_channel_metadata, get_channel_videos
from youtube_cli.core.comments import get_comments
from youtube_cli.core.common import normalize_channel
from youtube_cli.core.models import video_summary
from youtube_cli.core.playlists import get_playlist_videos
from youtube_cli.core.transcripts import (
    TranscriptLanguageUnavailable,
    _fetch_transcript,
    _select_transcript,
    get_transcript,
)
from youtube_cli.core.videos import get_video_metadata, search_videos

VIDEO_ID = "dQw4w9WgXcQ"


class FakeFetchedTranscript(list):
    language_code = "en"
    is_generated = False


def context_client(result: dict) -> MagicMock:
    client = MagicMock()
    client.__enter__.return_value = client
    client.extract_info.return_value = result
    return client


def summary_entry() -> dict:
    return {
        "id": VIDEO_ID,
        "title": "Test video",
        "channel": "Test channel",
        "channel_id": "channel-id",
        "channel_url": "https://youtube.com/@test",
        "duration": 125,
        "view_count": 42,
        "upload_date": "20260824",
    }


@patch("youtube_cli.core.videos.ydl")
def test_search_videos(mock_ydl: MagicMock) -> None:
    mock_ydl.return_value = context_client({"entries": [summary_entry()]})
    result = search_videos("test", limit=1)
    assert result[0]["id"] == VIDEO_ID
    assert result[0]["duration"] == "2:05"


def test_search_rejects_blank_query() -> None:
    with pytest.raises(ValueError, match="query must not be empty"):
        search_videos("  ")


@patch("youtube_cli.core.videos.ydl")
def test_video_metadata_keeps_full_fields(mock_ydl: MagicMock) -> None:
    entry = {
        **summary_entry(),
        "like_count": 10,
        "comment_count": 3,
        "language": "en",
        "concurrent_view_count": 25,
        "description": "Description",
        "tags": ["one", "two"],
        "categories": ["Education"],
        "chapters": [{"title": "Intro", "start_time": 0, "end_time": 30}],
        "thumbnail": "https://example.com/image.jpg",
        "availability": "public",
        "live_status": "not_live",
        "age_limit": 0,
    }
    mock_ydl.return_value = context_client(entry)
    result = get_video_metadata(VIDEO_ID)
    assert result["description"] == "Description"
    assert result["tags"] == ["one", "two"]
    assert result["chapters"][0]["end"] == "0:30"
    assert result["language"] == "en"
    assert result["concurrent_viewers"] == 25


def test_video_summary_includes_only_meaningful_live_status() -> None:
    normal = summary_entry()
    normal["live_status"] = "not_live"
    live = summary_entry()
    live["live_status"] = "is_live"
    assert "live_status" not in video_summary(normal)
    assert video_summary(live)["live_status"] == "is_live"


@patch("youtube_cli.core.channels.ydl")
def test_channel_metadata(mock_ydl: MagicMock) -> None:
    mock_ydl.return_value = context_client(
        {
            "channel_id": "channel-id",
            "channel": "Test channel",
            "channel_url": "https://youtube.com/@test",
            "channel_follower_count": 100,
            "description": "Channel description",
            "playlist_count": 20,
        }
    )
    result = get_channel_metadata("@test")
    assert result["subscribers"] == 100
    assert result["video_count"] == 20


@patch("youtube_cli.core.channels.ydl")
def test_channel_videos(mock_ydl: MagicMock) -> None:
    entry = summary_entry()
    entry.pop("channel")
    entry.pop("channel_id")
    entry.pop("channel_url")
    client = context_client(
        {
            "channel": "Parent channel",
            "channel_id": "parent-id",
            "channel_url": "https://youtube.com/@parent",
            "entries": [entry],
        }
    )
    mock_ydl.return_value = client
    result = get_channel_videos("@test", limit=1)
    assert result[0]["id"] == VIDEO_ID
    assert result[0]["channel"] == "Parent channel"
    assert client.extract_info.call_args.args[0] == "https://www.youtube.com/@test/videos"


def test_channel_url_normalization_removes_content_tabs() -> None:
    assert normalize_channel("https://www.youtube.com/@test/videos?view=0") == (
        "https://www.youtube.com/@test"
    )


def test_channel_rejects_blank_value() -> None:
    with pytest.raises(ValueError, match="channel must not be empty"):
        normalize_channel("  ")


@patch("youtube_cli.core.playlists.ydl")
def test_playlist_videos(mock_ydl: MagicMock) -> None:
    mock_ydl.return_value = context_client(
        {"entries": [summary_entry(), {"id": "missing1234"}]}
    )
    result = get_playlist_videos("playlist-id", limit=1)
    assert result[0]["id"] == VIDEO_ID
    assert result[1]["unavailable"] is True


def test_playlist_rejects_blank_value() -> None:
    with pytest.raises(ValueError, match="playlist must not be empty"):
        get_playlist_videos("  ")


@patch("youtube_cli.core.transcripts.video_directory")
@patch("youtube_cli.core.transcripts._fetch_transcript")
def test_transcript_without_timestamps(
    mock_fetch: MagicMock,
    mock_directory: MagicMock,
    tmp_path,
) -> None:
    transcript = FakeFetchedTranscript(
        [
            SimpleNamespace(text="Hello", start=0.0, duration=1.0),
            SimpleNamespace(text="world", start=2.0, duration=1.0),
        ]
    )
    mock_fetch.return_value = transcript
    mock_directory.return_value = tmp_path
    result = get_transcript(VIDEO_ID)
    assert result["timestamps"] is False
    assert (tmp_path / f"{VIDEO_ID}-transcript-en.txt").read_text() == "Hello\nworld\n"


@patch("youtube_cli.core.transcripts.video_directory")
@patch("youtube_cli.core.transcripts._fetch_transcript")
def test_transcript_with_timestamps(
    mock_fetch: MagicMock,
    mock_directory: MagicMock,
    tmp_path,
) -> None:
    mock_fetch.return_value = FakeFetchedTranscript(
        [SimpleNamespace(text="Hello", start=65.0, duration=1.0)]
    )
    mock_directory.return_value = tmp_path
    result = get_transcript(VIDEO_ID, timestamps=True)
    assert result["timestamps"] is True
    assert (tmp_path / f"{VIDEO_ID}-transcript-en-timestamps.txt").read_text() == "[1:05] Hello\n"


@patch("youtube_cli.core.transcripts.video_directory")
@patch("youtube_cli.core.transcripts._fetch_transcript")
def test_transcript_rejects_empty_caption_track(
    mock_fetch: MagicMock,
    mock_directory: MagicMock,
    tmp_path,
) -> None:
    mock_fetch.return_value = FakeFetchedTranscript(
        [SimpleNamespace(text="  ", start=0.0, duration=1.0)]
    )
    mock_directory.return_value = tmp_path
    with pytest.raises(RuntimeError, match=f"Transcript is empty for {VIDEO_ID}"):
        get_transcript(VIDEO_ID)
    assert not list(tmp_path.iterdir())


@patch("youtube_cli.core.transcripts._fetch_transcript")
def test_transcript_disabled_has_concise_error(mock_fetch: MagicMock) -> None:
    mock_fetch.side_effect = TranscriptsDisabled(VIDEO_ID)
    with pytest.raises(RuntimeError, match=f"No captions or transcript available for {VIDEO_ID}"):
        get_transcript(VIDEO_ID)


@patch("youtube_cli.core.transcripts.YouTubeTranscriptApi")
def test_transcript_fallback_prefers_generated_original(mock_api_class: MagicMock) -> None:
    api = mock_api_class.return_value
    translated = MagicMock(is_generated=False, language_code="vi")
    generated = MagicMock(is_generated=True, language_code="en")
    generated.fetch.return_value = [SimpleNamespace(text="שלום", start=0.0, duration=1.0)]
    api.list.return_value = [translated, generated]
    assert _fetch_transcript(VIDEO_ID) == generated.fetch.return_value
    generated.fetch.assert_called_once_with()
    translated.fetch.assert_not_called()


def test_transcript_prefers_manual_caption_in_original_language() -> None:
    vietnamese = SimpleNamespace(is_generated=False, language_code="vi")
    manual_english = SimpleNamespace(is_generated=False, language_code="en")
    generated_english = SimpleNamespace(is_generated=True, language_code="en")
    assert _select_transcript([vietnamese, manual_english, generated_english]) is manual_english


def test_transcript_explicit_language_prefers_manual() -> None:
    manual_spanish = SimpleNamespace(is_generated=False, language_code="es")
    generated_spanish = SimpleNamespace(is_generated=True, language_code="es")
    assert _select_transcript([generated_spanish, manual_spanish], "es") is manual_spanish


def test_transcript_language_accepts_modern_hebrew_code() -> None:
    generated_hebrew = SimpleNamespace(is_generated=True, language_code="iw")
    assert _select_transcript([generated_hebrew], "he") is generated_hebrew


def test_transcript_language_accepts_regional_variant() -> None:
    generated_spanish = SimpleNamespace(is_generated=True, language_code="es-419")
    assert _select_transcript([generated_spanish], "es") is generated_spanish


def test_transcript_explicit_language_reports_available_languages() -> None:
    english = SimpleNamespace(is_generated=True, language_code="en")
    with pytest.raises(TranscriptLanguageUnavailable, match="Available: en"):
        _select_transcript([english], "es")


@patch("youtube_cli.core.comments.video_directory")
@patch("youtube_cli.core.comments.ydl")
def test_comments_file(
    mock_ydl: MagicMock,
    mock_directory: MagicMock,
    tmp_path,
) -> None:
    client = context_client(
        {
            "comments": [
                {
                    "id": "comment-id",
                    "author": "Person",
                    "text": "Useful correction",
                    "like_count": 5,
                    "parent": "root",
                }
            ]
        }
    )
    mock_ydl.return_value = client
    mock_directory.return_value = tmp_path
    result = get_comments(VIDEO_ID)
    assert result["requested"] == 50
    assert result["retrieved"] == 1
    assert result["replies"] is True
    saved = yaml.safe_load(
        (tmp_path / f"{VIDEO_ID}-comments-top-50-with-replies.yml").read_text()
    )
    assert saved["comments"][0]["text"] == "Useful correction"
    options = mock_ydl.call_args.args[0]
    assert options["extractor_args"]["youtube"]["comment_sort"] == ["top"]
    assert options["extractor_args"]["youtube"]["max_comments"] == [
        "50",
        "50",
        "50",
        "3",
        "all",
    ]


@patch("youtube_cli.core.comments.video_directory")
@patch("youtube_cli.core.comments.ydl")
def test_comments_without_replies(
    mock_ydl: MagicMock,
    mock_directory: MagicMock,
    tmp_path,
) -> None:
    mock_directory.return_value = tmp_path
    mock_ydl.return_value = context_client({"comments": []})
    result = get_comments(VIDEO_ID, limit=10, replies=False)
    assert result["path"].endswith("-comments-top-10-without-replies.yml")
    options = mock_ydl.call_args.args[0]
    assert options["extractor_args"]["youtube"]["max_comments"] == [
        "10",
        "10",
        "0",
        "0",
        "1",
    ]
