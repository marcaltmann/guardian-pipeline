"""Stage 30 — build the works, voters and votes tables out of the decoded ballots.

Extracts the distinct works and voters, and every individual vote, from the stage-20
``gb.json`` and writes:

    data/derived/works.tsv    # author, work
    data/derived/voters.tsv   # slug, name, is{Academic,Critic,Author,Journalist}
    data/derived/votes.tsv    # voterSlug, position, author, work, openLibraryId

Works are collected from every ballot, so the table covers every work anyone voted
for, not just the ones that made the top-100 list (which, being computed from the
ballots, adds nothing). A work is keyed by ``(author, work)``, which is what
``votes.tsv`` joins back on.

The openLibraryId sits on the vote, not on the work, because that is where the source
puts it: two voters naming the same work can carry different ids (19 ballots name Bleak
House between three ids), so there is no one id to hang on the work until someone
reconciles them. All three tables are regenerable from ``raw`` alone and never
hand-edited.

Offline, no flags. Run from the ``pipeline/`` directory::

    uv run 30_build_tables.py
"""

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from jsonio import read_json
from paths import DERIVED_DIR, RAW_DIR
from tsv import write_tsv

_FLAG_FIELDS = ('isAcademic', 'isCritic', 'isAuthor', 'isJournalist')

WORKS_FIELDS = ['author', 'work']
VOTERS_FIELDS = ['slug', 'name', *_FLAG_FIELDS]
VOTES_FIELDS = ['voterSlug', 'position', 'author', 'work', 'openLibraryId']


def distinct_works(gb: Iterable[Mapping[str, Any]]) -> list[dict[str, str]]:
    """Return the distinct ``(author, work)`` pairs across every ballot, as sorted
    ``{'author', 'work'}`` dicts."""
    seen = {(vote['author'], vote['name']) for voter in gb for vote in voter['topTen']}
    return [{'author': author, 'work': work} for author, work in sorted(seen)]


def voter_rows(gb: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return one row per voter — ``slug``, ``name`` and the boolean role flags —
    sorted by slug. The opaque ``id`` hash is dropped."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for voter in sorted(gb, key=lambda v: v['slug']):
        if voter['slug'] in seen:
            continue
        seen.add(voter['slug'])
        rows.append(
            {
                'slug': voter['slug'],
                'name': voter['name'],
                **{flag: voter[flag] for flag in _FLAG_FIELDS},
            }
        )
    return rows


def vote_rows(gb: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return one row per ballot entry — the voter's slug, the position they gave it,
    and the work as *that voter* named it — sorted by slug, then position.

    ``author``/``work`` join back to :file:`works.tsv`; ``openLibraryId`` is the id
    this particular vote carries, which need not agree with another voter's.
    """
    return [
        {
            'voterSlug': voter['slug'],
            'position': vote['position'],
            'author': vote['author'],
            'work': vote['name'],
            'openLibraryId': vote['openLibraryId'],
        }
        for voter in sorted(gb, key=lambda v: v['slug'])
        for vote in sorted(voter['topTen'], key=lambda v: v['position'])
    ]


def build_tables(raw_dir: Path, derived_dir: Path) -> dict[str, int]:
    """Build the works, voters and votes tables. Returns a count summary."""
    gb = read_json(raw_dir / 'gb.json', 'run stage 20 first')

    works = distinct_works(gb)
    voters = voter_rows(gb)
    votes = vote_rows(gb)

    write_tsv(derived_dir / 'works.tsv', WORKS_FIELDS, works)
    write_tsv(derived_dir / 'voters.tsv', VOTERS_FIELDS, voters)
    write_tsv(derived_dir / 'votes.tsv', VOTES_FIELDS, votes)

    return {'works': len(works), 'voters': len(voters), 'votes': len(votes)}


def main() -> None:
    summary = build_tables(RAW_DIR, DERIVED_DIR)
    print(
        f'works: {summary["works"]} → {DERIVED_DIR}/works.tsv\n'
        f'voters: {summary["voters"]} → {DERIVED_DIR}/voters.tsv\n'
        f'votes: {summary["votes"]} → {DERIVED_DIR}/votes.tsv'
    )


if __name__ == '__main__':
    main()
