"""Stage 30 — build the works/voters curation tables (reconcile phase).

Extracts the distinct works and voters out of the decoded raw arrays, left-joins
the hand-maintained id tables in ``data/manual/``, and writes:

    data/derived/works.tsv    # author, work, wikidataId, goodreadsId
    data/derived/voters.tsv   # slug, name, is{Academic,Critic,Author,Journalist}, wikidataId
    output/missing_work_ids.tsv    # rows still lacking a wikidataId (curator worklist)
    output/missing_voter_ids.tsv

The derived tables are regenerable (``raw`` + ``manual``) and never hand-edited; the
worklists are disposable. The curator researches the worklist rows, adds them to the
matching ``data/manual/*_ids.tsv`` table (which is never written by any script), and
re-runs — the derived tables fill in and the worklist shrinks. Wikidata *props*
(author id, gender, dates, language) are not touched here; that is the enrich phase
(stages 40/41), keyed off the ids curated here.

Offline, no flags. Run from the repo root::

    uv run pipeline/30_build_curation_tables.py
"""

from jsonio import read_json
from paths import DERIVED_DIR, MANUAL_DIR, OUTPUT_DIR, RAW_DIR
from tsv import read_tsv, write_tsv

_FLAG_FIELDS = ('isAcademic', 'isCritic', 'isAuthor', 'isJournalist')

WORKS_DERIVED_FIELDS = ['author', 'work', 'wikidataId', 'goodreadsId']
VOTERS_DERIVED_FIELDS = ['slug', 'name', *_FLAG_FIELDS, 'wikidataId']
# Worklists mirror the manual-table schema, so a filled-in row pastes straight in.
WORKS_MISSING_FIELDS = ['author', 'work', 'wikidataId', 'goodreadsId', 'notes']
VOTERS_MISSING_FIELDS = ['slug', 'name', 'wikidataId', 'notes']


def distinct_works(pb, gb):
    """Return the distinct ``(author, work)`` pairs across the top-100 and every
    ballot, as sorted ``{'author', 'work'}`` dicts."""
    seen = set()
    for book in pb:
        seen.add((book['author'], book['title']))
    for voter in gb:
        for vote in voter['topTen']:
            seen.add((vote['author'], vote['name']))
    return [{'author': author, 'work': work} for author, work in sorted(seen)]


def voter_rows(gb):
    """Return one row per voter — ``slug``, ``name`` and the boolean role flags —
    sorted by slug. The opaque ``id`` hash is dropped."""
    rows = []
    seen = set()
    for voter in sorted(gb, key=lambda v: v['slug']):
        if voter['slug'] in seen:
            continue
        seen.add(voter['slug'])
        rows.append(
            {'slug': voter['slug'], 'name': voter['name'],
             **{flag: voter[flag] for flag in _FLAG_FIELDS}}
        )
    return rows


def join_works(works, manual_rows):
    """Left-join ``works`` onto the manual id table, keyed by ``(author, work)``.

    Returns ``(derived, missing)``: ``derived`` is every work with its ids filled in
    where known (blank otherwise); ``missing`` is the subset still lacking a
    ``wikidataId``, carrying any existing note forward for the curator.
    """
    by_key = {(r['author'], r['work']): r for r in manual_rows}
    derived, missing = [], []
    for work in works:
        m = by_key.get((work['author'], work['work']), {})
        wikidata_id = m.get('wikidataId') or ''
        goodreads_id = m.get('goodreadsId') or ''
        derived.append({'author': work['author'], 'work': work['work'],
                        'wikidataId': wikidata_id, 'goodreadsId': goodreads_id})
        if not wikidata_id:
            missing.append({'author': work['author'], 'work': work['work'],
                            'wikidataId': '', 'goodreadsId': goodreads_id,
                            'notes': m.get('notes') or ''})
    return derived, missing


def join_voters(voters, manual_rows):
    """Left-join ``voters`` onto the manual id table, keyed by ``slug``.

    Returns ``(derived, missing)`` as :func:`join_works` does, per voter.
    """
    by_slug = {r['slug']: r for r in manual_rows}
    derived, missing = [], []
    for voter in voters:
        m = by_slug.get(voter['slug'], {})
        wikidata_id = m.get('wikidataId') or ''
        derived.append({**voter, 'wikidataId': wikidata_id})
        if not wikidata_id:
            missing.append({'slug': voter['slug'], 'name': voter['name'],
                            'wikidataId': '', 'notes': m.get('notes') or ''})
    return derived, missing


def _read_manual(path):
    """Read a hand-maintained id table, or return no rows if it doesn't exist yet."""
    return read_tsv(path) if path.exists() else []


def build_curation_tables(raw_dir, manual_dir, derived_dir, output_dir):
    """Build the derived curation tables and worklists. Returns a count summary."""
    pb = read_json(raw_dir / 'pb.json', 'run stage 20 first')
    gb = read_json(raw_dir / 'gb.json', 'run stage 20 first')

    works = distinct_works(pb, gb)
    voters = voter_rows(gb)

    derived_works, missing_works = join_works(
        works, _read_manual(manual_dir / 'works_ids.tsv')
    )
    derived_voters, missing_voters = join_voters(
        voters, _read_manual(manual_dir / 'voters_ids.tsv')
    )

    write_tsv(derived_dir / 'works.tsv', WORKS_DERIVED_FIELDS, derived_works)
    write_tsv(derived_dir / 'voters.tsv', VOTERS_DERIVED_FIELDS, derived_voters)
    write_tsv(output_dir / 'missing_work_ids.tsv', WORKS_MISSING_FIELDS, missing_works)
    write_tsv(output_dir / 'missing_voter_ids.tsv', VOTERS_MISSING_FIELDS, missing_voters)

    return {'works': len(works), 'voters': len(voters),
            'missing_works': len(missing_works), 'missing_voters': len(missing_voters)}


def main():
    s = build_curation_tables(RAW_DIR, MANUAL_DIR, DERIVED_DIR, OUTPUT_DIR)
    print(
        f"works: {s['works']} ({s['missing_works']} missing ids) → {DERIVED_DIR}/works.tsv\n"
        f"voters: {s['voters']} ({s['missing_voters']} missing ids) → {DERIVED_DIR}/voters.tsv"
    )


if __name__ == '__main__':
    main()
