"""Validate ``output/guardian.graphml`` against the GraphML XML Schema.

The schema in ``schema/`` is the one published at graphml.graphdrawing.org —
``graphml.xsd`` plus the two files it pulls in — with its two absolute URLs rewritten
to local file names so validation runs offline. Besides well-formedness it checks
the things that break graph tools: duplicate node ids, edges pointing at missing
nodes, ``<data>`` using an undeclared key.

Needs ``lxml`` (dev group). Run from the ``pipeline/`` directory::

    uv run validate_graphml.py [FILE]
"""

import sys
from pathlib import Path

from lxml import etree

from paths import OUTPUT_DIR

SCHEMA_PATH = Path('../schema/graphml.xsd')
DEFAULT_GRAPHML = OUTPUT_DIR / 'guardian.graphml'


def validate(graphml_path: Path, schema_path: Path = SCHEMA_PATH) -> list[str]:
    """Return the schema violations in ``graphml_path``; an empty list means valid."""
    schema = etree.XMLSchema(etree.parse(schema_path))
    schema.validate(etree.parse(graphml_path))
    return [f'{e.line}: {e.message}' for e in schema.error_log]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GRAPHML
    if not path.exists():
        raise SystemExit(f'{path} not found — run stage 50 first')
    errors = validate(path)
    if errors:
        print('\n'.join(errors))
        raise SystemExit(f'{path}: {len(errors)} schema violation(s)')
    print(f'{path} validates against {SCHEMA_PATH.name}')


if __name__ == '__main__':
    main()
