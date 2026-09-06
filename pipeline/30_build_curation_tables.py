"""Stage 30 — build the works, voters and votes tables out of the decoded raw arrays.

Extracts the distinct works and voters, and every individual vote, from the stage-20
JSON and writes:

    data/derived/works.tsv    # author, work
    data/derived/voters.tsv   # slug, name, is{Academic,Critic,Author,Journalist}
    data/derived/votes.tsv    # voterSlug, position, author, work, openLibraryId

Works are collected across both sources — the top-100 list *and* every ballot — so
the table covers every work anyone voted for, not just the ones that made the list.
A work is keyed by ``(author, work)``, which is what ``votes.tsv`` joins back on.

The openLibraryId sits on the vote, not on the work, because that is where the source
puts it: two voters naming the same work can carry different ids (19 ballots name Bleak
House between three ids), so there is no one id to hang on the work until someone
reconciles them. All three tables are regenerable from ``raw`` alone and never
hand-edited.

Offline, no flags. Run from the ``pipeline/`` directory::

    uv run 30_build_curation_tables.py
"""

from jsonio import read_json
from paths import DERIVED_DIR, RAW_DIR
from tsv import write_tsv

_FLAG_FIELDS = ('isAcademic', 'isCritic', 'isAuthor', 'isJournalist')

WORKS_FIELDS = ['author', 'work']
VOTERS_FIELDS = ['slug', 'name', *_FLAG_FIELDS]
VOTES_FIELDS = ['voterSlug', 'position', 'author', 'work', 'openLibraryId']


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


def vote_rows(gb):
    """Return one row per ballot entry — the voter's slug, the position they gave it,
    and the work as *that voter* named it — sorted by slug, then position.

    ``author``/``work`` join back to :file:`works.tsv`; ``openLibraryId`` is the id
    this particular vote carries, which need not agree with another voter's.
    """
    return [
        {'voterSlug': voter['slug'], 'position': vote['position'],
         'author': vote['author'], 'work': vote['name'],
         'openLibraryId': vote['openLibraryId']}
        for voter in sorted(gb, key=lambda v: v['slug'])
        for vote in sorted(voter['topTen'], key=lambda v: v['position'])
    ]


def build_tables(raw_dir, derived_dir):
    """Build the works, voters and votes tables. Returns a count summary."""
    pb = read_json(raw_dir / 'pb.json', 'run stage 20 first')
    gb = read_json(raw_dir / 'gb.json', 'run stage 20 first')

    works = distinct_works(pb, gb)
    voters = voter_rows(gb)
    votes = vote_rows(gb)

    write_tsv(derived_dir / 'works.tsv', WORKS_FIELDS, works)
    write_tsv(derived_dir / 'voters.tsv', VOTERS_FIELDS, voters)
    write_tsv(derived_dir / 'votes.tsv', VOTES_FIELDS, votes)

    return {'works': len(works), 'voters': len(voters), 'votes': len(votes)}


def main():
    s = build_tables(RAW_DIR, DERIVED_DIR)
    print(
        f"works: {s['works']} → {DERIVED_DIR}/works.tsv\n"
        f"voters: {s['voters']} → {DERIVED_DIR}/voters.tsv\n"
        f"votes: {s['votes']} → {DERIVED_DIR}/votes.tsv"
    )


if __name__ == '__main__':
    main()
