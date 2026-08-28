from __future__ import annotations

import argparse
import re
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
LEADING_ID = re.compile(r"^-[A-Za-z0-9_-]{10}$")
VIDEO_ID_SENTINEL = "__YOUTUBE_LEADING_DASH_VIDEO_ID__"


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _error_message(error: Exception) -> str:
    message = str(error).strip() or type(error).__name__
    while message.startswith("ERROR:"):
        message = message.removeprefix("ERROR:").strip()
    message = re.sub(r"^\[youtube(?::[^]]+)?]\s+[^:]+:\s*", "", message)
    message = re.sub(r"\s*\(caused by <[^>]+>\)\s*$", "", message)
    return message


def _command(parser: argparse.ArgumentParser, handler: Handler) -> None:
    parser.set_defaults(handler=handler, command_parser=parser)


def _leaf(subparsers: Any, name: str, description: str) -> argparse.ArgumentParser:
    return subparsers.add_parser(
        name,
        help=description,
        description=description,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )


def _protect_leading_dash_video_id(argv: list[str]) -> tuple[list[str], str | None]:
    if len(argv) < 3 or argv[0] != "video" or argv[1] not in {"metadata", "transcript", "comments"}:
        return argv, None
    protected = list(argv)
    for index in range(2, len(protected)):
        if LEADING_ID.fullmatch(protected[index]):
            video_id = protected[index]
            protected[index] = VIDEO_ID_SENTINEL
            return protected, video_id
    return protected, None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="youtube-cli", description="Search and read YouTube")
    parser.add_argument("--version", action="version", version=__version__)
    resources = parser.add_subparsers(dest="resource", required=True)

    video = resources.add_parser("video", help="Video operations")
    video_commands = video.add_subparsers(dest="operation", required=True)

    search = _leaf(video_commands, "search", "Search YouTube videos")
    search.add_argument("query", help="YouTube search query")
    search.add_argument("--limit", type=_positive_int, default=10, help="Maximum results")
    _command(search, search_videos)

    metadata = _leaf(video_commands, "metadata", "Get video metadata")
    metadata.add_argument("video_id", help="11-character YouTube video or Short ID")
    _command(metadata, get_video_metadata)

    transcript = _leaf(video_commands, "transcript", "Save a video transcript")
    transcript.add_argument("video_id", help="11-character YouTube video or Short ID")
    transcript.add_argument("--timestamps", action="store_true", help="Include timestamps")
    transcript.add_argument(
        "--language",
        default=argparse.SUPPRESS,
        help="Select an available caption language code; defaults to the original language",
    )
    _command(transcript, get_transcript)

    comments = _leaf(video_commands, "comments", "Save video comments")
    comments.add_argument("video_id", help="11-character YouTube video or Short ID")
    comments.add_argument(
        "--sort", choices=["top", "new"], default="top", help="Comment order"
    )
    comments.add_argument("--limit", type=_positive_int, default=50, help="Maximum comments")
    comments.add_argument(
        "--replies",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Include replies",
    )
    _command(comments, get_comments)

    channel = resources.add_parser("channel", help="Channel operations")
    channel_commands = channel.add_subparsers(dest="operation", required=True)

    channel_metadata = _leaf(channel_commands, "metadata", "Get channel metadata")
    channel_metadata.add_argument("channel", help="Channel handle or URL")
    _command(channel_metadata, get_channel_metadata)

    channel_videos = _leaf(channel_commands, "videos", "List channel videos")
    channel_videos.add_argument("channel", help="Channel handle or URL")
    channel_videos.add_argument("--limit", type=_positive_int, default=20, help="Maximum results")
    _command(channel_videos, get_channel_videos)

    playlist = resources.add_parser("playlist", help="Playlist operations")
    playlist_commands = playlist.add_subparsers(dest="operation", required=True)
    playlist_videos = _leaf(playlist_commands, "videos", "List playlist videos")
    playlist_videos.add_argument("playlist", help="Playlist ID or URL")
    playlist_videos.add_argument("--limit", type=_positive_int, default=50, help="Maximum results")
    _command(playlist_videos, get_playlist_videos)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    protected_argv, leading_video_id = _protect_leading_dash_video_id(raw_argv)
    namespace, extras = parser.parse_known_args(protected_argv)
    args = vars(namespace)
    if extras:
        args["command_parser"].error(f"unrecognized arguments: {' '.join(extras)}")
    if leading_video_id is not None and args.get("video_id") == VIDEO_ID_SENTINEL:
        args["video_id"] = leading_video_id
    handler: Handler = args.pop("handler")
    args.pop("command_parser")
    args.pop("resource")
    args.pop("operation")
    try:
        result = handler(**args)
        print(serialize(result))
    except KeyboardInterrupt:
        raise
    except Exception as error:
        print(f"Error: {_error_message(error)}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
