"""Stage 20 — decode the ``gb`` array literal out of the archived bundle::

    data/raw/gb.json   # every voter's ballot

The array is a JavaScript literal, not JSON, so the decode shells out to ``node`` —
see extract.py. Decoded strings are NFC-normalized and trimmed, because the dirty
source text would otherwise break the exact-match joins in later stages.

The bundle also holds ``pb``, the published top-100 list. Nothing downstream needs
it — every listed work is on some ballot under the same spelling — so it is not
decoded. The lines are kept commented out below in case its extra fields (year,
blurb, published vote count) are ever wanted.

Run from the ``pipeline/`` directory::

    uv run 20_extract_votes.py
"""

from pathlib import Path

from extract import extract_array, normalize_decoded
from jsonio import write_json
from paths import RAW_APPJS_DIR, RAW_DIR
from release import read_selected_url, version_from_url


def extract_votes(appjs_dir: Path, out_dir: Path) -> str:
    """Decode the selected release's ``gb`` array into ``out_dir``; return the version."""
    version = version_from_url(read_selected_url())
    bundle_path = appjs_dir / f'{version}.js'
    if not bundle_path.exists():
        raise SystemExit(f'{bundle_path} not found — run stage 10 first')

    src = bundle_path.read_text(encoding='utf-8')
    gb = normalize_decoded(extract_array(src, 'gb'))
    # pb = normalize_decoded(extract_array(src, 'pb'))

    write_json(out_dir / 'gb.json', gb)
    # write_json(out_dir / 'pb.json', pb)
    return version


def main() -> None:
    version = extract_votes(RAW_APPJS_DIR, RAW_DIR)
    print(f'extracted {version} → {RAW_DIR}/gb.json')


if __name__ == '__main__':
    main()
