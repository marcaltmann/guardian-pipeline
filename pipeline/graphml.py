"""Write a GraphML document — the one graph format every network tool reads.

Attribute keys are declared up front and nodes/edges carry ``<data>`` values for
them. Escaping is ElementTree's job, not string formatting's. Booleans are written
``true``/``false``; a ``None`` value is left out of the file.
"""

import xml.etree.ElementTree as ET
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any, NamedTuple

GRAPHML_NS = 'http://graphml.graphdrawing.org/xmlns'


class Key(NamedTuple):
    """One declared attribute: its id, whether it sits on nodes or edges, its type."""

    id: str
    domain: str  # 'node' or 'edge'
    type: str  # 'string', 'double', 'int', 'boolean'


class Node(NamedTuple):
    id: str
    data: Mapping[str, Any]


class Edge(NamedTuple):
    source: str
    target: str
    data: Mapping[str, Any]


def _data_text(value: Any) -> str:
    """Render one attribute value as GraphML text."""
    if value is True:
        return 'true'
    if value is False:
        return 'false'
    return str(value)


def _append_data(parent: ET.Element, data: Mapping[str, Any]) -> None:
    for key, value in data.items():
        if value is None:
            continue
        element = ET.SubElement(parent, 'data', {'key': key})
        element.text = _data_text(value)


def build_document(
    keys: Sequence[Key],
    nodes: Iterable[Node],
    edges: Iterable[Edge],
    *,
    edgedefault: str = 'undirected',
) -> ET.ElementTree:
    """Build the tree: the key declarations, then one graph of nodes and edges."""
    root = ET.Element('graphml', {'xmlns': GRAPHML_NS})
    for key in keys:
        ET.SubElement(
            root,
            'key',
            {
                'id': key.id,
                'for': key.domain,
                'attr.name': key.id,
                'attr.type': key.type,
            },
        )
    graph = ET.SubElement(root, 'graph', {'edgedefault': edgedefault})
    for node in nodes:
        _append_data(ET.SubElement(graph, 'node', {'id': node.id}), node.data)
    for edge in edges:
        element = ET.SubElement(
            graph, 'edge', {'source': edge.source, 'target': edge.target}
        )
        _append_data(element, edge.data)
    ET.indent(root, space='  ')
    return ET.ElementTree(root)


def write_graphml(
    path: Path,
    keys: Sequence[Key],
    nodes: Iterable[Node],
    edges: Iterable[Edge],
    *,
    edgedefault: str = 'undirected',
) -> None:
    """Write the document to ``path``, creating parent directories as needed."""
    tree = build_document(keys, nodes, edges, edgedefault=edgedefault)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('wb') as f:
        # By hand: ``xml_declaration=True`` spells it with single quotes and a
        # lowercase encoding name.
        f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        tree.write(f, encoding='utf-8', xml_declaration=False)
        f.write(b'\n')
