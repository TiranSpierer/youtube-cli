from __future__ import annotations

from typing import Any

import yaml


def serialize(data: Any) -> str:
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000).rstrip()
