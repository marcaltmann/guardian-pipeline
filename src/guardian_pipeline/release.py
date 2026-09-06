"""Which Guardian app.js release the stages work on."""

import re

from paths import MANUAL_DIR

SELECTED_URL_PATH = MANUAL_DIR / 'selected_url'

_VERSION_RE = re.compile(r'/(\d+)/app\.js')


def read_selected_url() -> str:
    """Read the single configured app.js URL, or exit with a helpful message."""
    if not SELECTED_URL_PATH.exists():
        raise SystemExit(
            f'{SELECTED_URL_PATH} not found — create the file with the app.js URL first'
        )
    url = SELECTED_URL_PATH.read_text(encoding='utf-8').strip()
    if not url:
        raise SystemExit(f'{SELECTED_URL_PATH} is empty — add the app.js URL first')
    return url


def version_from_url(url: str) -> str:
    """Extract the version — the ``/v/{digits}/app.js`` path segment — from a URL."""
    match = _VERSION_RE.search(url)
    if match is None:
        raise ValueError(f'could not parse a version from URL: {url!r}')
    return match.group(1)
