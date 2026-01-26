from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> Any:
    """Read JSON from disk (UTF-8) and parse.

    This is a small shared helper to keep JSON IO consistent across deterministic
    evidence-related tooling.
    """

    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def write_json(
    path: str | Path,
    data: Any,
    *,
    make_parents: bool = False,
    indent: int = 2,
    sort_keys: bool = True,
    ensure_ascii: bool = False,
) -> None:
    """Write JSON deterministically (UTF-8, LF newlines, trailing newline).

    Default settings match the repo's determinism conventions.
    """

    p = Path(path)
    if make_parents:
        p.parent.mkdir(parents=True, exist_ok=True)

    p.write_text(
        json.dumps(
            data,
            indent=indent,
            sort_keys=sort_keys,
            ensure_ascii=ensure_ascii,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
