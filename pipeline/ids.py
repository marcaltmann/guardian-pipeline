"""Node ids for the works and voters, derived from the data itself.

Voters have the Guardian's ``slug``; works are keyed only by the ``(author, work)``
pair the tables join on, slugified. Nothing external is consulted.
"""

import re
import unicodedata
from collections.abc import Iterable, Mapping

WORK_PREFIX = 'work'
VOTER_PREFIX = 'voter'

_NON_SLUG = re.compile(r'[^a-z0-9]+')


def slugify(text: str) -> str:
    """Fold ``text`` to lowercase ``a-z0-9`` runs joined by hyphens.

    Accents are stripped to their base letter (``Brontë`` → ``bronte``); every other
    character is a separator.
    """
    decomposed = unicodedata.normalize('NFKD', text)
    ascii_only = ''.join(c for c in decomposed if not unicodedata.combining(c))
    return _NON_SLUG.sub('-', ascii_only.lower()).strip('-')


def voter_id(slug: str) -> str:
    """The node id for a voter — the Guardian slug, which is already id-shaped."""
    return f'{VOTER_PREFIX}_{slug}'


def work_key(author: str, work: str) -> tuple[str, str]:
    """The ``(author, work)`` pair the tables join on, as a dict/set key."""
    return (author, work)


def assign_work_ids(works: Iterable[Mapping[str, str]]) -> dict[tuple[str, str], str]:
    """Map every work's ``(author, work)`` key to a unique ``work_{author}_{title}`` id.

    Two works can slugify alike (none do today); the later one — in the caller's
    order, which is ``works.tsv``'s sort — takes a ``-2``, ``-3``, … suffix, so ids
    stay unique and stay a pure function of the table.
    """
    ids: dict[tuple[str, str], str] = {}
    used: dict[str, int] = {}
    for row in works:
        key = work_key(row['author'], row['work'])
        if key in ids:
            continue
        base = f"{WORK_PREFIX}_{slugify(row['author'])}_{slugify(row['work'])}"
        used[base] = used.get(base, 0) + 1
        ids[key] = base if used[base] == 1 else f'{base}-{used[base]}'
    return ids
