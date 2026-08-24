from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from typing import Any

from youtube_cli import __version__
from youtube_cli.core.channels import get_channel_metadata, get_channel_videos
from youtube_cli.core.comments import get_comments
from youtube_cli.core.playlists import get_playlist_videos
from youtube_cli.core.transcripts import get_transcript
from youtube_cli.core.videos import get_video_metadata, search_videos
from youtube_cli.format import serialize

Handler = Callable[..., Any]


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _command(parser: argparse.ArgumentParser, handler: Handler) -> None:
    parser.set_defaults(handler=handler)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="youtube-cli", description="Search and read YouTube")
    parser.add_argument("--version", action="version", version=__version__)
    resources = parser.add_subparsers(dest="resource", required=True)

    video = resources.add_parser("video", help="Video operations")
    video_commands = video.add_subparsers(dest="operation", required=True)

    search = video_commands.add_parser("search", help="Search YouTube videos")
    search.add_argument("query")
    search.add_argument("--limit", type=_positive_int, default=10)
    _command(search, search_videos)

    metadata = video_commands.add_parser("metadata", help="Get video metadata")
    metadata.add_argument("video_id")
    _command(metadata, get_video_metadata)

    transcript = video_commands.add_parser("transcript", help="Save a video transcript")
    transcript.add_argument("video_id")
    transcript.add_argument("--timestamps", action="store_true")
    _command(transcript, get_transcript)

    comments = video_commands.add_parser("comments", help="Save video comments")
    comments.add_argument("video_id")
    comments.add_argument("--sort", choices=["top", "new"], default="top")
    comments.add_argument("--limit", type=_positive_int, default=50)
    _command(comments, get_comments)

    channel = resources.add_parser("channel", help="Channel operations")
    channel_commands = channel.add_subparsers(dest="operation", required=True)

    channel_metadata = channel_commands.add_parser("metadata", help="Get channel metadata")
    channel_metadata.add_argument("channel")
    _command(channel_metadata, get_channel_metadata)

    channel_videos = channel_commands.add_parser("videos", help="List channel videos")
    channel_videos.add_argument("channel")
    channel_videos.add_argument("--sort", choices=["date", "popular"], default="date")
    channel_videos.add_argument("--limit", type=_positive_int, default=20)
    _command(channel_videos, get_channel_videos)

    playlist = resources.add_parser("playlist", help="Playlist operations")
    playlist_commands = playlist.add_subparsers(dest="operation", required=True)
    playlist_videos = playlist_commands.add_parser("videos", help="List playlist videos")
    playlist_videos.add_argument("playlist")
    playlist_videos.add_argument("--limit", type=_positive_int, default=50)
    _command(playlist_videos, get_playlist_videos)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = vars(parser.parse_args(argv))
    handler: Handler = args.pop("handler")
    args.pop("resource")
    args.pop("operation")
    try:
        result = handler(**args)
        print(serialize(result))
    except KeyboardInterrupt:
        raise
    except Exception as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
