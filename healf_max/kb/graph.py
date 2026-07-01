from __future__ import annotations

from collections import Counter
from typing import Any

from healf_max.kb.schemas import KBRecord

GRAPH_FILE = "kb_graph.json"
LINK_FIELDS = (
    "biomarker_routes",
    "evidence_routes",
    "wearable_signals",
    "product_lanes",
    "editorial_signals",
    "tone_patterns",
    "trust_signals",
)


def build_record_graph(records: list[KBRecord]) -> dict[str, Any]:
    nodes = {
        record.id: {
            "id": record.id,
            "type": record.type,
            "group": record.kind,
            "title": record.title,
            "path": record.path,
        }
        for record in records
    }
    known_ids = set(nodes)
    edges: list[dict[str, str]] = []
    adjacency: dict[str, list[dict[str, str]]] = {record.id: [] for record in records}
    reverse_adjacency: dict[str, list[dict[str, str]]] = {record.id: [] for record in records}
    field_counts: Counter[str] = Counter()

    for record in records:
        for field in LINK_FIELDS:
            for target_id in linked_ids(record.frontmatter.get(field)):
                if target_id not in known_ids:
                    continue
                edge = {"source": record.id, "target": target_id, "field": field}
                edges.append(edge)
                adjacency[record.id].append({"target": target_id, "field": field})
                reverse_adjacency[target_id].append({"source": record.id, "field": field})
                field_counts[field] += 1

    return {
        "nodes": nodes,
        "edges": edges,
        "adjacency": adjacency,
        "reverse_adjacency": reverse_adjacency,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "edge_counts_by_field": dict(sorted(field_counts.items())),
        },
    }


def linked_ids(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
