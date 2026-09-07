"""Stage 50 — turn the reconciled tables into the bipartite voter–work graph.

Reads the stage-35 tables and stage-30 votes and writes:

    output/guardian.graphml

One node per work, one per voter, one undirected edge per vote. Nodes are keyed by
their Wikidata id (``work_Q…``, ``voter_Q…``), so the graph cannot be built while
any row still lacks one — the stage stops and points at the stage-35 worklist.

Keying by Wikidata id is what merges spelling variants: the source names one work
several ways (``Alice in Wonderland`` / ``Alice's Adventures in Wonderland``), and
once they share a Wikidata id they are one node. The node's ``label`` and
``author_label`` come from the variant with the most votes; a voter who named the
same work twice under different spellings gets one edge, not two.

Every edge weighs ``1.0`` — a vote is a vote; the ballot position is not on the
edge. Works nobody voted for would appear as isolated nodes, since ``works.tsv``
covers the published top-100 as well as every ballot.

Offline, no flags. Run from the ``pipeline/`` directory::

    uv run 50_build_graphml.py
"""

from collections import Counter

from graphml import Edge, Key, Node, write_graphml
from ids import voter_id, work_id, work_key
from paths import DERIVED_DIR, OUTPUT_DIR
from tsv import read_tsv

GRAPHML_NAME = 'guardian.graphml'

KEYS = (
    Key('label', 'node', 'string'),
    Key('node_type', 'node', 'string'),
    Key('wikidata_id', 'node', 'string'),
    Key('author_label', 'node', 'string'),
    Key('weight', 'edge', 'double'),
)


def _require_ids(rows, describe, worklist):
    """Stop if any row has a blank ``wikidataId``; the graph is keyed by it."""
    blank = [row for row in rows if not row['wikidataId']]
    if blank:
        raise SystemExit(
            f'{len(blank)} {describe} without a wikidataId (e.g. {blank[0]!r}) — '
            f'curate {worklist} and re-run stage 35'
        )


def work_ids_by_key(works):
    """Map each ``(author, work)`` spelling to its ``work_Q…`` node id."""
    return {
        work_key(row['author'], row['work']): work_id(row['wikidataId'])
        for row in works
    }


def group_works(works, votes):
    """Group the works table by node id. Each group lists the spellings sharing a
    Wikidata id, most-voted first (ties keep table order) — the first one names the
    node; the rest are what it absorbed."""
    vote_counts = Counter(work_key(row['author'], row['work']) for row in votes)
    groups = {}
    for row in works:
        groups.setdefault(work_id(row['wikidataId']), []).append(row)
    return {
        node_id: sorted(
            rows, key=lambda r: -vote_counts[work_key(r['author'], r['work'])]
        )
        for node_id, rows in groups.items()
    }


def work_nodes(groups):
    """One node per Wikidata id, labelled by its group's first spelling."""
    return [
        Node(
            node_id,
            {
                'label': rows[0]['work'],
                'node_type': 'work',
                'wikidata_id': rows[0]['wikidataId'],
                'author_label': rows[0]['author'],
            },
        )
        for node_id, rows in groups.items()
    ]


def merged_groups(groups):
    """The groups with more than one spelling — the merges worth eyeballing."""
    return {node_id: rows for node_id, rows in groups.items() if len(rows) > 1}


def voter_nodes(voters):
    """One node per voter, keyed by their Wikidata id, their name as ``label``."""
    return [
        Node(
            voter_id(row['wikidataId']),
            {
                'label': row['name'],
                'node_type': 'voter',
                'wikidata_id': row['wikidataId'],
            },
        )
        for row in voters
    ]


def vote_edges(votes, work_ids, voter_ids):
    """One undirected edge per distinct (voter, work) pair. A vote naming a work or
    voter the tables don't know is a broken join and stops the stage."""
    seen = set()
    edges = []
    for row in votes:
        key = work_key(row['author'], row['work'])
        if key not in work_ids:
            raise SystemExit(
                f'{row["voterSlug"]} voted for {key!r}, which is not in '
                'works_reconciled.tsv — re-run stages 30 and 35'
            )
        if row['voterSlug'] not in voter_ids:
            raise SystemExit(
                f'{row["voterSlug"]} is not in voters_reconciled.tsv — '
                're-run stages 30 and 35'
            )
        pair = (voter_ids[row['voterSlug']], work_ids[key])
        if pair in seen:
            continue
        seen.add(pair)
        edges.append(Edge(*pair, {'weight': 1.0}))
    return edges


def build_graph(derived_dir, output_dir):
    """Build the GraphML file from the reconciled tables. Returns a count summary."""
    works = read_tsv(derived_dir / 'works_reconciled.tsv')
    voters = read_tsv(derived_dir / 'voters_reconciled.tsv')
    votes = read_tsv(derived_dir / 'votes.tsv')

    _require_ids(works, 'works', 'output/missing_works_wikidata.tsv')
    _require_ids(voters, 'voters', 'output/missing_voters_wikidata.tsv')

    work_ids = work_ids_by_key(works)
    voter_ids = {row['slug']: voter_id(row['wikidataId']) for row in voters}

    groups = group_works(works, votes)
    nodes = [*work_nodes(groups), *voter_nodes(voters)]
    edges = vote_edges(votes, work_ids, voter_ids)

    path = output_dir / GRAPHML_NAME
    write_graphml(path, KEYS, nodes, edges)
    return {
        'work_rows': len(works),
        'work_nodes': len(groups),
        'voters': len(voters),
        'votes': len(votes),
        'edges': len(edges),
        'merged': merged_groups(groups),
    }


def main():
    s = build_graph(DERIVED_DIR, OUTPUT_DIR)
    print(
        f'{s["work_nodes"]} works (from {s["work_rows"]} spellings) + '
        f'{s["voters"]} voters, {s["edges"]} edges (from {s["votes"]} votes) '
        f'→ {OUTPUT_DIR}/{GRAPHML_NAME}'
    )
    if s['merged']:
        print('merged into one node (label first, then what it absorbed):')
        for rows in s['merged'].values():
            spellings = [f'{r["work"]} ({r["author"]})' for r in rows]
            print(
                f'  {rows[0]["wikidataId"]:<11}{spellings[0]}  ← {", ".join(spellings[1:])}'
            )


if __name__ == '__main__':
    main()
