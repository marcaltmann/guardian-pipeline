"""Stage 35 — reconcile the hand-curated Wikidata ids onto the works and voters.

Left-joins the stage-30 tables onto the manual id tables in ``data/manual/`` and
writes:

    data/derived/works_reconciled.tsv    # author, work, wikidataId
    data/derived/voters_reconciled.tsv   # slug, name, wikidataId
    output/missing_works_wikidata.tsv    # rows still lacking a wikidataId (curator worklist)
    output/missing_voters_wikidata.tsv

The manual tables (``works_wikidata.tsv`` keyed by ``(author, work)``,
``voters_wikidata.tsv`` keyed by ``slug``) are never written by any script; a missing
one just means nothing is curated yet. The worklists mirror the manual-table schema,
so a researched row pastes straight in. The curator fills rows in, re-runs this stage,
and the worklist shrinks. Manual rows that match no work or voter are reported so a
typo in a key doesn't silently leave the id unused.

Offline, no flags. Run from the ``pipeline/`` directory::

    uv run 35_reconcile_wikidata_ids.py
"""

from paths import DERIVED_DIR, MANUAL_DIR, OUTPUT_DIR
from tsv import read_tsv, write_tsv

WORKS_RECONCILED_FIELDS = ['author', 'work', 'wikidataId']
VOTERS_RECONCILED_FIELDS = ['slug', 'name', 'wikidataId']
# Worklists mirror the manual-table schema, so a filled-in row pastes straight in.
WORKS_MANUAL_FIELDS = ['author', 'work', 'wikidataId', 'notes']
VOTERS_MANUAL_FIELDS = ['slug', 'name', 'wikidataId', 'notes']


def join_works(works, manual_rows):
    """Left-join ``works`` onto the manual id table, keyed by ``(author, work)``.

    Returns ``(reconciled, missing, unmatched)``: ``reconciled`` is every work with
    its id filled in where known (blank otherwise); ``missing`` is the subset still
    lacking a ``wikidataId``, carrying any existing note forward for the curator;
    ``unmatched`` is the manual keys that match no work.
    """
    by_key = {(r['author'], r['work']): r for r in manual_rows}
    reconciled, missing = [], []
    for work in works:
        key = (work['author'], work['work'])
        m = by_key.pop(key, {})
        wikidata_id = m.get('wikidataId') or ''
        reconciled.append({'author': work['author'], 'work': work['work'],
                           'wikidataId': wikidata_id})
        if not wikidata_id:
            missing.append({'author': work['author'], 'work': work['work'],
                            'wikidataId': '', 'notes': m.get('notes') or ''})
    return reconciled, missing, sorted(by_key)


def join_voters(voters, manual_rows):
    """Left-join ``voters`` onto the manual id table, keyed by ``slug``.

    Returns ``(reconciled, missing, unmatched)`` as :func:`join_works` does.
    """
    by_slug = {r['slug']: r for r in manual_rows}
    reconciled, missing = [], []
    for voter in voters:
        m = by_slug.pop(voter['slug'], {})
        wikidata_id = m.get('wikidataId') or ''
        reconciled.append({'slug': voter['slug'], 'name': voter['name'],
                           'wikidataId': wikidata_id})
        if not wikidata_id:
            missing.append({'slug': voter['slug'], 'name': voter['name'],
                            'wikidataId': '', 'notes': m.get('notes') or ''})
    return reconciled, missing, sorted(by_slug)


def _read_manual(path):
    """Read a hand-maintained id table, or return no rows if it doesn't exist yet."""
    return read_tsv(path) if path.exists() else []


def _read_derived(path):
    if not path.exists():
        raise SystemExit(f'{path} not found — run stage 30 first')
    return read_tsv(path)


def reconcile(manual_dir, derived_dir, output_dir):
    """Build the reconciled tables and worklists. Returns a count summary."""
    works = _read_derived(derived_dir / 'works.tsv')
    voters = _read_derived(derived_dir / 'voters.tsv')

    works_reconciled, works_missing, works_unmatched = join_works(
        works, _read_manual(manual_dir / 'works_wikidata.tsv')
    )
    voters_reconciled, voters_missing, voters_unmatched = join_voters(
        voters, _read_manual(manual_dir / 'voters_wikidata.tsv')
    )

    write_tsv(derived_dir / 'works_reconciled.tsv', WORKS_RECONCILED_FIELDS,
              works_reconciled)
    write_tsv(derived_dir / 'voters_reconciled.tsv', VOTERS_RECONCILED_FIELDS,
              voters_reconciled)
    write_tsv(output_dir / 'missing_works_wikidata.tsv', WORKS_MANUAL_FIELDS,
              works_missing)
    write_tsv(output_dir / 'missing_voters_wikidata.tsv', VOTERS_MANUAL_FIELDS,
              voters_missing)

    return {'works': len(works), 'voters': len(voters),
            'works_missing': len(works_missing), 'voters_missing': len(voters_missing),
            'works_unmatched': works_unmatched, 'voters_unmatched': voters_unmatched}


def main():
    s = reconcile(MANUAL_DIR, DERIVED_DIR, OUTPUT_DIR)
    print(
        f"works: {s['works']} ({s['works_missing']} missing wikidataId) "
        f'→ {DERIVED_DIR}/works_reconciled.tsv\n'
        f"voters: {s['voters']} ({s['voters_missing']} missing wikidataId) "
        f'→ {DERIVED_DIR}/voters_reconciled.tsv'
    )
    for label, keys in (('works', s['works_unmatched']),
                        ('voters', s['voters_unmatched'])):
        for key in keys:
            print(f'warning: {label}_wikidata.tsv row matches nothing: {key!r}')


if __name__ == '__main__':
    main()
