"""Stage 50 — turn the curation tables into the bipartite voter–work graph.

Reads the stage-30 tables and writes:

    output/guardian.graphml

One node per voter, one per work, one undirected edge per vote. Node ids come from
the data rather than any external authority (see :mod:`ids`), and the original
strings ride along as ``label``/``author_label``/``slug`` so a node can be joined
back to the TSVs.

Every edge weighs ``1.0`` — a vote is a vote; the ballot position is not on the
edge. Works nobody voted for would appear as isolated nodes, since ``works.tsv``
covers the published top-100 as well as every ballot.

Offline, no flags. Run from the ``pipeline/`` directory::

    uv run 50_build_graphml.py
"""

from graphml import Edge, Key, Node, write_graphml
from ids import assign_work_ids, voter_id, work_key
from paths import DERIVED_DIR, OUTPUT_DIR
from tsv import read_tsv

GRAPHML_NAME = 'guardian.graphml'

KEYS = (
    Key('label', 'node', 'string'),
    Key('node_type', 'node', 'string'),
    Key('slug', 'node', 'string'),
    Key('author_label', 'node', 'string'),
    Key('weight', 'edge', 'double'),
)


def work_nodes(works, work_ids):
    """One node per work: the title as ``label``, the author alongside it."""
    return [
        Node(
            work_ids[work_key(row['author'], row['work'])],
            {
                'label': row['work'],
                'node_type': 'work',
                'author_label': row['author'],
            },
        )
        for row in works
    ]


def voter_nodes(voters):
    """One node per voter: their name as ``label``, their slug kept for joining back."""
    return [
        Node(
            voter_id(row['slug']),
            {
                'label': row['name'],
                'node_type': 'voter',
                'slug': row['slug'],
            },
        )
        for row in voters
    ]


def vote_edges(votes, work_ids):
    """One undirected edge per vote. A missing ``(author, work)`` is a broken join
    and stops the stage rather than silently dropping the edge."""
    edges = []
    for row in votes:
        key = work_key(row['author'], row['work'])
        if key not in work_ids:
            raise SystemExit(
                f'{row["voterSlug"]} voted for {key!r}, which is not in works.tsv '
                '— re-run stage 30'
            )
        edges.append(Edge(voter_id(row['voterSlug']), work_ids[key], {'weight': 1.0}))
    return edges


def build_graph(derived_dir, output_dir):
    """Build the GraphML file from the derived tables. Returns a count summary."""
    works = read_tsv(derived_dir / 'works.tsv')
    voters = read_tsv(derived_dir / 'voters.tsv')
    votes = read_tsv(derived_dir / 'votes.tsv')

    work_ids = assign_work_ids(works)
    nodes = [*work_nodes(works, work_ids), *voter_nodes(voters)]
    edges = vote_edges(votes, work_ids)

    path = output_dir / GRAPHML_NAME
    write_graphml(path, KEYS, nodes, edges)
    return {'works': len(works), 'voters': len(voters), 'edges': len(edges)}


def main():
    s = build_graph(DERIVED_DIR, OUTPUT_DIR)
    print(
        f"{s['works']} works + {s['voters']} voters, {s['edges']} votes "
        f'→ {OUTPUT_DIR}/{GRAPHML_NAME}'
    )


if __name__ == '__main__':
    main()
