"""Stage 20 — decode the ``pb``/``gb`` array literals out of the archived bundle::

    data/raw/pb.json   # the top-100 list
    data/raw/gb.json   # every voter's ballot

The arrays are JavaScript literals, not JSON, so the decode shells out to ``node`` —
see extract.py. Decoded strings are NFC-normalized and trimmed, because the dirty
source text would otherwise break the exact-match joins in later stages.

Run from the ``pipeline/`` directory::

    uv run 20_extract_arrays.py
"""

from pathlib import Path

from extract import extract_array, normalize_decoded
from jsonio import write_json
from paths import RAW_APPJS_DIR, RAW_DIR
from release import read_selected_url, version_from_url


def extract_arrays(appjs_dir: Path, out_dir: Path) -> str:
    """Decode the selected release's arrays into ``out_dir``; return the version."""
    version = version_from_url(read_selected_url())
    bundle_path = appjs_dir / f'{version}.js'
    if not bundle_path.exists():
        raise SystemExit(f'{bundle_path} not found — run stage 10 first')

    src = bundle_path.read_text(encoding='utf-8')
    pb = normalize_decoded(extract_array(src, 'pb'))
    gb = normalize_decoded(extract_array(src, 'gb'))

    write_json(out_dir / 'pb.json', pb)
    write_json(out_dir / 'gb.json', gb)
    return version


def main() -> None:
    version = extract_arrays(RAW_APPJS_DIR, RAW_DIR)
    print(f'extracted {version} → {RAW_DIR}/pb.json, {RAW_DIR}/gb.json')


if __name__ == '__main__':
    main()
