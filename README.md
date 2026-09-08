# guardian-pipeline

Turns the ballot data behind the Guardian's 2026 "The 100 best novels" list into a
bipartite voter–work graph, with every work and voter identified by its Wikidata id.

## Pipeline

Each stage is one script in `pipeline/`, numbered in run order. A stage reads what
the previous one wrote and never edits anything by hand.

| Stage | Script | Does |
|---|---|---|
| 10 | `10_fetch_appjs.py` | Fetches the Guardian `app.js` bundle named in `data/manual/selected_url` into `data/raw/app_js/`. Skips if already archived. |
| 15 | `15_beautify_appjs.py` | Beautifies the bundle for diffing. Optional; nothing reads its output. |
| 20 | `20_extract_votes.py` | Decodes every ballot out of the bundle into `data/raw/gb.json`. Needs `node`. |
| 30 | `30_build_tables.py` | Builds `works.tsv`, `voters.tsv` and `votes.tsv` in `data/derived/`. |
| 35 | `35_reconcile_wikidata_ids.py` | Joins the hand-curated Wikidata ids from `data/manual/` onto works and voters, writes `*_reconciled.tsv`, and lists anything still missing an id in `output/missing_*.tsv`. |
| 40 | *(planned)* | Wikidata enrichment. |
| 50 | `50_build_graphml.py` | Writes `output/guardian.graphml`, one node per Wikidata id, one edge per vote. Works spelled differently but sharing an id become one node; the stage reports those merges. |

Data directories under `pipeline/data/`:

- `raw/` — what stages 10 and 20 fetched and decoded.
- `manual/` — hand-maintained: the selected release URL and the Wikidata id tables. Never written by a script.
- `derived/` — regenerable from `raw` and `manual`.
- `output/` — the graph and the curator worklists. Not committed.

## Running

Requires `uv`, `node`, and `make`. From the repository root:

```
make            # fetch, extract, tables, reconcile, graphml
make tables     # one stage; run any subset in order, e.g. make tables reconcile graphml
make beautify   # the optional stage
make validate   # check output/guardian.graphml against the GraphML schema
```

`make validate` uses the GraphML XML Schema vendored in `schema/` and needs `lxml`, which
`uv` installs with the `dev` dependency group by default.

Stages can also be run directly from inside `pipeline/`, e.g. `uv run 30_build_tables.py`.

## Curating ids

Stage 50 refuses to build while any work or voter lacks a Wikidata id. Research the rows
in `output/missing_works_wikidata.tsv` or `missing_voters_wikidata.tsv`, paste them with
their id into the matching `data/manual/works_wikidata.tsv` or `voters_wikidata.tsv`,
and re-run `make reconcile graphml`. Stage 35 warns about manual rows that match no
work or voter, which usually means a spelling changed in the source.
