"""Stage 11 — beautify an archived app.js snapshot for line-by-line diffing::

    data/raw/app_js/{version}.js  ->  data/derived/app_js/{version}-beautified.js

The beautified copies are committed; nothing downstream reads them. Defaults to the
selected release.

Run from the repo root::

    uv run pipeline/11_beautify_appjs.py [--version VERSION]
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

import jsbeautifier

from paths import DERIVED_APPJS_DIR, RAW_APPJS_DIR
from release import read_selected_url, version_from_url


def beautify_appjs(version: str, raw_dir: Path, out_dir: Path) -> Path:
    """Beautify ``raw_dir/{version}.js`` into ``out_dir/{version}-beautified.js``."""
    bundle_path = raw_dir / f'{version}.js'
    if not bundle_path.exists():
        raise SystemExit(f'{bundle_path} not found — fetch it first with stage 10')

    pretty = jsbeautifier.beautify(bundle_path.read_text(encoding='utf-8'))
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f'{version}-beautified.js'
    out_path.write_text(pretty, encoding='utf-8')
    return out_path


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description='Beautify an archived app.js snapshot for line-by-line diffing.'
    )
    parser.add_argument(
        '--version',
        help='which archived snapshot to beautify (default: the selected release)',
    )
    args = parser.parse_args(argv)

    version = args.version or version_from_url(read_selected_url())
    out_path = beautify_appjs(version, RAW_APPJS_DIR, DERIVED_APPJS_DIR)
    print(f'beautified {version} → {out_path}')


if __name__ == '__main__':
    main()
