from __future__ import annotations

from unittest.mock import patch

import pytest

from youtube_cli.cli import main
from youtube_cli.format import serialize


@patch("youtube_cli.cli.search_videos")
def test_video_search_command(mock_search, capsys) -> None:
    mock_search.return_value = [{"id": "abc", "title": "Result"}]
    main(["video", "search", "query", "--limit", "2"])
    assert mock_search.call_args.kwargs == {"query": "query", "limit": 2}
    assert "title: Result" in capsys.readouterr().out


@patch("youtube_cli.cli.get_comments")
def test_comments_defaults(mock_comments, capsys) -> None:
    mock_comments.return_value = {"path": "/tmp/comments.yml"}
    main(["video", "comments", "dQw4w9WgXcQ"])
    assert mock_comments.call_args.kwargs == {
        "video_id": "dQw4w9WgXcQ",
        "sort": "top",
        "limit": 50,
        "replies": True,
    }
    assert "path: /tmp/comments.yml" in capsys.readouterr().out


@patch("youtube_cli.cli.get_comments")
def test_comments_without_replies(mock_comments) -> None:
    mock_comments.return_value = {"path": "/tmp/comments.yml"}
    main(["video", "comments", "dQw4w9WgXcQ", "--no-replies"])
    assert mock_comments.call_args.kwargs["replies"] is False


@patch("youtube_cli.cli.get_transcript")
def test_transcript_timestamps(mock_transcript, capsys) -> None:
    mock_transcript.return_value = {"timestamps": True, "path": "/tmp/transcript.txt"}
    main(["video", "transcript", "dQw4w9WgXcQ", "--timestamps"])
    assert mock_transcript.call_args.kwargs == {
        "video_id": "dQw4w9WgXcQ",
        "timestamps": True,
    }


def test_invalid_limit_exits_nonzero() -> None:
    with pytest.raises(SystemExit) as error:
        main(["video", "search", "query", "--limit", "0"])
    assert error.value.code != 0


@patch("youtube_cli.cli.get_video_metadata")
def test_leading_dash_video_id(mock_metadata, capsys) -> None:
    mock_metadata.return_value = {"id": "-V6wgriNyOM"}
    main(["video", "metadata", "-V6wgriNyOM"])
    assert mock_metadata.call_args.kwargs == {"video_id": "-V6wgriNyOM"}
    assert "-V6wgriNyOM" in capsys.readouterr().out


@patch("youtube_cli.cli.get_video_metadata")
def test_yt_dlp_error_is_printed_once(mock_metadata, capsys) -> None:
    mock_metadata.side_effect = RuntimeError("ERROR: [youtube] unavailable")
    with pytest.raises(SystemExit) as error:
        main(["video", "metadata", "dQw4w9WgXcQ"])
    assert error.value.code == 1
    assert capsys.readouterr().err == "Error: [youtube] unavailable\n"


def test_multiline_yaml_uses_literal_block() -> None:
    assert serialize({"description": "first\nsecond"}) == "description: |-\n  first\n  second"
    assert serialize({"description": "first  \nsecond"}) == "description: |-\n  first\n  second"
