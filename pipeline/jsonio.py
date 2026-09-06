"""Read and write the JSON files the pipeline stages hand to each other."""

import json
from pathlib import Path
from typing import Any


def write_json(
    path: Path, obj: Any, *, indent: int = 2, sort_keys: bool = False
) -> None:
    """Write ``obj`` to ``path`` as JSON, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(obj, ensure_ascii=False, indent=indent, sort_keys=sort_keys) + '\n',
        encoding='utf-8',
    )


def read_json(path: Path, hint: str) -> Any:
    """Read JSON from ``path``, or exit with ``hint`` telling the user how to produce it."""
    if not path.exists():
        raise SystemExit(f'{path} not found — {hint}')
    return json.loads(path.read_text(encoding='utf-8'))
