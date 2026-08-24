from __future__ import annotations

from unittest.mock import patch

import pytest

from youtube_cli.cli import main


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
    }
    assert "path: /tmp/comments.yml" in capsys.readouterr().out


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
