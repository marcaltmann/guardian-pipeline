"""Node ids for the works and voters, built from their curated Wikidata ids.

A work is ``work_Q…``, a voter ``voter_Q…``. The prefix keeps the two node types
apart even if one Wikidata item ever showed up on both sides.
"""

WORK_PREFIX = 'work'
VOTER_PREFIX = 'voter'


def work_id(wikidata_id: str) -> str:
    return f'{WORK_PREFIX}_{wikidata_id}'


def voter_id(wikidata_id: str) -> str:
    return f'{VOTER_PREFIX}_{wikidata_id}'


def work_key(author: str, work: str) -> tuple[str, str]:
    """The ``(author, work)`` pair the stage-30 tables join on, as a dict key."""
    return (author, work)
