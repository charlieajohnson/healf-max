from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from healf_max.kb.loader import load_kb_records
from healf_max.kb.schemas import KBRecord

TYPE_ORDER = {
    "wellbeing_moment": 0,
    "biomarker": 1,
    "evidence_claim": 2,
    "product_category": 3,
    "editorial_signal": 4,
    "trust_signal": 5,
    "tone_pattern": 6,
    "brand_signal": 7,
    "example": 8,
}

LINK_FIELDS = ("evidence_routes", "product_lanes", "editorial_signals", "tone_patterns", "trust_signals")
TRACE_REQUIRED_TYPES = ("editorial_signal", "trust_signal", "tone_pattern", "brand_signal")
TRACE_BALANCE_LIMIT = 16


def lexical_search(
    query: str,
    records: list[KBRecord],
    *,
    limit: int = 6,
    kinds: set[str] | None = None,
) -> list[KBRecord]:
    return score_records(query, records, limit=limit, kinds=kinds)


def search_kb(
    query: str,
    *,
    kb_dir: str | Path,
    storage_dir: str | Path | None = None,
    limit: int = 6,
    kinds: set[str] | None = None,
) -> list[KBRecord]:
    if storage_dir:
        from healf_max.kb.index import search_index

        indexed = search_index(query, storage_dir=storage_dir, limit=limit, kinds=kinds)
        if indexed:
            return indexed
    return lexical_search(query, load_kb_records(kb_dir), limit=limit, kinds=kinds)


def score_records(
    query: str,
    records: list[KBRecord],
    *,
    limit: int = 6,
    kinds: set[str] | None = None,
    embedding_scores: dict[str, float] | None = None,
) -> list[KBRecord]:
    query_terms = _tokenise(query)
    if not query_terms:
        return []

    embedding_scores = embedding_scores or {}
    base_scores: dict[str, tuple[float, list[str]]] = {}
    id_to_record = {record.id: record for record in records}

    for record in records:
        if kinds and record.kind not in kinds and record.type not in kinds:
            continue
        score, reasons = _score_record(query_terms, record)
        embedding_score = embedding_scores.get(record.id, 0.0)
        if embedding_score:
            score += embedding_score * 5
            reasons.append(f"embedding:{embedding_score:.2f}")
        if score > 0:
            base_scores[record.id] = (score, reasons)

    # Expand linked records from high-signal matches so a matched moment can pull
    # its evidence, product, editorial, trust and tone routes into the debug trace.
    direct_scores = dict(base_scores)
    for source_id, (source_score, _) in direct_scores.items():
        source = id_to_record[source_id]
        if source.type not in {"wellbeing_moment", "biomarker", "evidence_claim"}:
            continue
        if source_score < 18:
            continue
        for linked_id in _linked_ids(source.frontmatter):
            linked = id_to_record.get(linked_id)
            if linked is None:
                continue
            if kinds and linked.kind not in kinds and linked.type not in kinds:
                continue
            linked_score, reasons = base_scores.get(linked_id, (0.0, []))
            boost = min(3.0, source_score * 0.15)
            base_scores[linked_id] = (
                linked_score + boost,
                reasons + [f"linked_from:{source.id}"],
            )

    scored: list[KBRecord] = []
    for record_id, (score, reasons) in base_scores.items():
        record = id_to_record[record_id]
        scored.append(record.model_copy(update={"score": score, "retrieval_reason": reasons}))

    ranked = sorted(
        scored,
        key=lambda item: (
            -item.score,
            TYPE_ORDER.get(item.type, 99),
            -item.retrieval_priority,
            item.path,
        ),
    )
    return _balanced_limit(ranked, limit)


def _tokenise(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 2 and token not in {"and", "the", "for", "with", "that", "this"}
    }


def tokenise_for_index(text: str) -> list[str]:
    return sorted(_tokenise(text))


def _score_record(query_terms: set[str], record: KBRecord) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    id_title_terms = _tokenise(f"{record.id} {record.title}")
    tag_terms = _tokenise(" ".join(record.tags))
    body_terms = _tokenise(record.body)
    frontmatter_terms = _tokenise(_frontmatter_text(record.frontmatter))

    id_title_match = query_terms.intersection(id_title_terms)
    if id_title_match:
        score += 5.0 * len(id_title_match)
        reasons.append("title/id:" + ",".join(sorted(id_title_match)))
    tag_match = query_terms.intersection(tag_terms)
    if tag_match:
        score += 4.0 * len(tag_match)
        reasons.append("tags:" + ",".join(sorted(tag_match)))
    frontmatter_match = query_terms.intersection(frontmatter_terms)
    if frontmatter_match:
        score += 2.0 * len(frontmatter_match)
        reasons.append("frontmatter:" + ",".join(sorted(frontmatter_match)))
    body_match = query_terms.intersection(body_terms)
    if body_match:
        score += 1.0 * len(body_match)
        reasons.append("body:" + ",".join(sorted(body_match)))
    if score:
        type_boost = {
            "wellbeing_moment": 14.0,
            "biomarker": 18.0,
            "evidence_claim": 2.5,
        }.get(record.type, 0.0)
        if type_boost:
            score += type_boost
            reasons.append(f"type:{record.type}")
        boost = record.retrieval_priority * 0.4
        score += boost
        reasons.append(f"priority:{record.retrieval_priority}")
    return score, reasons


def _frontmatter_text(frontmatter: dict[str, Any]) -> str:
    parts: list[str] = []
    score_keys = {
        "tags",
        "summary",
        "trigger_signals",
        "primary_interpretation",
        "related_symptoms_or_goals",
        "fit_when",
        "use_when",
        "category_role",
        "marker_unit",
        "demo_result",
    }
    for key, value in frontmatter.items():
        if key not in score_keys:
            continue
        if isinstance(value, list):
            parts.extend(str(item) for item in value)
        elif isinstance(value, dict):
            parts.extend(str(item) for item in value.values())
        else:
            parts.append(str(value))
    return " ".join(parts)


def _linked_ids(frontmatter: dict[str, Any]) -> list[str]:
    linked: list[str] = []
    for field in LINK_FIELDS:
        value = frontmatter.get(field)
        if isinstance(value, list):
            linked.extend(str(item) for item in value)
        elif value:
            linked.append(str(value))
    return linked


def _balanced_limit(ranked: list[KBRecord], limit: int) -> list[KBRecord]:
    selected = ranked[:limit]
    if limit < TRACE_BALANCE_LIMIT:
        return selected

    selected_ids = {record.id for record in selected}
    counts = Counter(record.type for record in selected)
    for record_type in TRACE_REQUIRED_TYPES:
        if any(record.type == record_type for record in selected):
            continue
        candidate = next((record for record in ranked if record.type == record_type), None)
        if candidate is None or candidate.id in selected_ids:
            continue
        replace_index = _replacement_index(selected, counts)
        if replace_index is None:
            continue
        removed = selected[replace_index]
        counts[removed.type] -= 1
        selected_ids.remove(removed.id)
        selected[replace_index] = candidate
        counts[candidate.type] += 1
        selected_ids.add(candidate.id)

    return sorted(
        selected,
        key=lambda item: (
            -item.score,
            TYPE_ORDER.get(item.type, 99),
            -item.retrieval_priority,
            item.path,
        ),
    )


def _replacement_index(selected: list[KBRecord], counts: Counter[str]) -> int | None:
    for index in range(len(selected) - 1, -1, -1):
        record = selected[index]
        if record.type in TRACE_REQUIRED_TYPES and counts[record.type] <= 1:
            continue
        if counts[record.type] <= 1:
            continue
        return index
    return None
