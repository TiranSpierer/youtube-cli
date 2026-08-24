from __future__ import annotations

from typing import Any

import yaml


class _ReadableDumper(yaml.SafeDumper):
    pass


def _represent_string(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    if "\n" in value:
        value = "\n".join(line.rstrip() for line in value.splitlines())
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


_ReadableDumper.add_representer(str, _represent_string)


def serialize(data: Any) -> str:
    return yaml.dump(
        data,
        Dumper=_ReadableDumper,
        allow_unicode=True,
        sort_keys=False,
        width=1000,
    ).rstrip()
