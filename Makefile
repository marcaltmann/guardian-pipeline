# One target per pipeline stage, in order. `make` runs them all; `make <stage>`
# runs just that one. Stages find their data relative to pipeline/, so run there.

RUN = cd pipeline && uv run

.PHONY: all fetch beautify extract tables reconcile graphml

all: fetch extract tables reconcile graphml

fetch:     ; $(RUN) 10_fetch_appjs.py
beautify:  ; $(RUN) 15_beautify_appjs.py
extract:   ; $(RUN) 20_extract_arrays.py
tables:    ; $(RUN) 30_build_tables.py
reconcile: ; $(RUN) 35_reconcile_wikidata_ids.py
graphml:   ; $(RUN) 50_build_graphml.py
