"""Read and write the tab-separated tables the pipeline stages hand to each other.

Cells are untyped text: booleans are written ``TRUE``/``FALSE``, ``None`` blank, and
several values fit in one cell joined by ``|``. Reading always gives strings back.
"""

import csv
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

VALUE_SEPARATOR = '|'


def _tsv_cell(value: Any) -> str:
    """Format one value for a TSV cell: bools as ``TRUE``/``FALSE``, ``None`` blank."""
    if value is None:
        return ''
    if value is True:
        return 'TRUE'
    if value is False:
        return 'FALSE'
    return str(value)


def write_tsv(
    path: Path,
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, Any]],
) -> None:
    """Write ``rows`` (dicts) to ``path`` as a tab-separated table with a header.

    Columns follow ``fieldnames``; missing keys are written blank. Parent
    directories are created as needed.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t', lineterminator='\n')
        writer.writerow(fieldnames)
        for row in rows:
            writer.writerow([_tsv_cell(row.get(name)) for name in fieldnames])


def read_tsv(path: Path) -> list[dict[str, str]]:
    """Read a tab-separated table into a list of dicts (values are strings).

    Blank lines and ``#`` comment lines are ignored, matching the hand-maintained
    ``data/manual/`` tables.
    """
    with path.open(encoding='utf-8', newline='') as f:
        lines = [ln for ln in f if ln.strip() and not ln.startswith('#')]
    return list(csv.DictReader(lines, delimiter='\t'))


def join_values(values: Iterable[Any]) -> str:
    """Render several values into one TSV cell, separated by ``|``.

    There is no escaping scheme: a value that contains the separator is refused.
    """
    values = [str(value) for value in values]
    for value in values:
        if VALUE_SEPARATOR in value:
            raise ValueError(
                f'value contains the {VALUE_SEPARATOR!r} cell separator: {value!r}'
            )
    return VALUE_SEPARATOR.join(values)


def split_values(cell: str) -> list[str]:
    """Split a ``|``-separated TSV cell back into values; a blank cell yields none."""
    return cell.split(VALUE_SEPARATOR) if cell else []
