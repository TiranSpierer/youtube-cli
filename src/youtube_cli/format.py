from __future__ import annotations

import json
from typing import Any

import yaml


def serialize(data: Any, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000).rstrip()
