from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import yaml

from youtube_cli.files import write_text, write_yaml


def test_concurrent_text_writes_are_atomic(tmp_path) -> None:
    path = tmp_path / "transcript.txt"
    contents = [character * 10_000 for character in "abcdefgh"]
    with ThreadPoolExecutor(max_workers=len(contents)) as executor:
        list(executor.map(lambda content: write_text(path, content), contents))
    assert path.read_text() in contents
    assert list(tmp_path.glob(".*")) == []


def test_concurrent_yaml_writes_are_atomic(tmp_path) -> None:
    path = tmp_path / "comments.yml"
    values = [{"value": index, "text": "x" * 10_000} for index in range(8)]
    with ThreadPoolExecutor(max_workers=len(values)) as executor:
        list(executor.map(lambda value: write_yaml(path, value), values))
    assert yaml.safe_load(path.read_text()) in values
    assert list(tmp_path.glob(".*")) == []
