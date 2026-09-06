"""Stage 10 — fetch the Guardian app.js bundle named in ``data/manual/selected_url``.

Writes a version-stamped snapshot plus a provenance sidecar::

    data/raw/app_js/{version}.js
    data/raw/app_js/{version}.json   # url, version, publication_date, fetched_at

The version is a Unix timestamp parsed from the URL path (``.../v/{version}/app.js``);
``publication_date`` is that timestamp decoded. Selecting a release means editing the
one-line config file ``data/manual/selected_url`` — there is no hardcoded URL.

Run from the repo root::

    uv run pipeline/10_fetch_appjs.py [--force]
"""

import argparse
from collections.abc import Sequence
from pathlib import Path

import requests

from jsonio import write_json
from paths import RAW_APPJS_DIR
from release import read_selected_url, version_from_url
from timestamps import format_iso_utc, from_unix, now_iso_utc


def _http_get(url: str) -> str:
    """Fetch ``url``, returning the decoded body; exit on a non-200 or empty response."""
    response = requests.get(url)
    if response.status_code != 200:
        raise SystemExit(f'fetch failed for {url}: HTTP {response.status_code}')
    body = response.content.decode('utf-8')
    if not body.strip():
        raise SystemExit(f'fetch returned an empty body for {url}')
    return body


def fetch_appjs(raw_dir: Path, force: bool = False) -> tuple[str, bool]:
    """Fetch the selected bundle into ``raw_dir`` unless it is already archived.

    Returns ``(version, fetched)``; ``fetched`` is ``False`` when a snapshot was reused.
    """
    url = read_selected_url()
    version = version_from_url(url)
    bundle_path = raw_dir / f'{version}.js'
    sidecar_path = raw_dir / f'{version}.json'

    if bundle_path.exists() and sidecar_path.exists() and not force:
        return version, False

    body = _http_get(url)
    raw_dir.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(body, encoding='utf-8')

    sidecar = {
        'url': url,
        'version': version,
        'publication_date': format_iso_utc(from_unix(int(version))),
        'fetched_at': now_iso_utc(),
    }
    write_json(sidecar_path, sidecar)
    return version, True


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description='Fetch the Guardian app.js bundle named in data/manual/selected_url.'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='refetch even if the snapshot is already archived',
    )
    args = parser.parse_args(argv)

    version, fetched = fetch_appjs(RAW_APPJS_DIR, force=args.force)
    if fetched:
        print(f'fetched {version} → {RAW_APPJS_DIR}/{version}.js')
    else:
        print(f'{version} already archived — use --force to refetch')


if __name__ == '__main__':
    main()
