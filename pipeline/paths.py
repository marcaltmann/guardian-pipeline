"""Where the pipeline's data lives, relative to the repository root."""

import pathlib

RAW_DIR = pathlib.Path('data/raw')
RAW_APPJS_DIR = RAW_DIR / 'app_js'
RAW_WIKIDATA_DIR = RAW_DIR / 'wikidata'
MANUAL_DIR = pathlib.Path('data/manual')
DERIVED_DIR = pathlib.Path('data/derived')
DERIVED_APPJS_DIR = DERIVED_DIR / 'app_js'
OUTPUT_DIR = pathlib.Path('output')
