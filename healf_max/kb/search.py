from __future__ import annotations

import re
from collections import Counter
from math import log
from pathlib import Path
from typing import Any

from healf_max.kb.graph import LINK_FIELDS, linked_ids
from healf_max.kb.loader import load_kb_records
from healf_max.kb.schemas import KBRecord

TYPE_ORDER = {
    "wellbeing_moment": 0,
    "biomarker": 1,
    "evidence_claim": 2,
    "wearable_signal": 3,
    "product_category": 4,
    "editorial_signal": 5,
    "trust_signal": 6,
    "tone_pattern": 7,
    "brand_signal": 8,
    "example": 9,
}

TRACE_REQUIRED_TYPES = ("wearable_signal", "editorial_signal", "trust_signal", "tone_pattern", "brand_signal")
TRACE_BALANCE_LIMIT = 16
BM25_K1 = 1.2
BM25_B = 0.75


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
    bm25_scores = _bm25_scores(query_terms, records)
    base_scores: dict[str, tuple[float, list[str]]] = {}
    id_to_record = {record.id: record for record in records}

    for record in records:
        if kinds and record.kind not in kinds and record.type not in kinds:
            continue
        score, reasons = _score_record(query_terms, record)
        bm25_score = bm25_scores.get(record.id, 0.0)
        if bm25_score:
            bm25_weight = 0.3 if "specificity:missing" in reasons else 3.0
            score += bm25_score * bm25_weight
            reasons.append(f"bm25:{bm25_score:.2f}")
        embedding_score = embedding_scores.get(record.id, 0.0)
        if embedding_score:
            score += embedding_score * 5
            reasons.append(f"embedding:{embedding_score:.2f}")
        if score > 0:
            base_scores[record.id] = (score, reasons)

    # Expand linked records from high-signal matches so a matched moment can pull
    # its evidence, product, editorial, trust and tone routes into the debug trace.
    direct_scores = dict(base_scores)
    for source_id, (source_score, source_reasons) in direct_scores.items():
        source = id_to_record[source_id]
        if source.type not in {"wellbeing_moment", "biomarker", "evidence_claim", "wearable_signal"}:
            continue
        if source_score < 18:
            continue
        if "specificity:missing" in source_reasons:
            continue
        for field, linked_id in _linked_ids_by_field(source.frontmatter):
            linked = id_to_record.get(linked_id)
            if linked is None:
                continue
            if kinds and linked.kind not in kinds and linked.type not in kinds:
                continue
            linked_score, reasons = base_scores.get(linked_id, (0.0, []))
            boost = min(3.0, source_score * 0.15)
            base_scores[linked_id] = (
                linked_score + boost,
                reasons + [f"graph_hop:{field}:{source.id}"],
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


def _bm25_scores(query_terms: set[str], records: list[KBRecord]) -> dict[str, float]:
    if not records:
        return {}
    document_terms = {record.id: _tokenise_list(record.searchable_text()) for record in records}
    document_frequency: Counter[str] = Counter()
    for terms in document_terms.values():
        document_frequency.update(set(terms))
    document_lengths = {record_id: len(terms) for record_id, terms in document_terms.items()}
    average_length = sum(document_lengths.values()) / max(len(document_lengths), 1)
    scores: dict[str, float] = {}
    total_documents = len(records)

    for record in records:
        terms = document_terms[record.id]
        if not terms:
            continue
        term_counts = Counter(terms)
        score = 0.0
        doc_length = document_lengths[record.id]
        for term in query_terms:
            frequency = term_counts.get(term, 0)
            if not frequency:
                continue
            df = document_frequency[term]
            idf = log(1 + (total_documents - df + 0.5) / (df + 0.5))
            denominator = frequency + BM25_K1 * (1 - BM25_B + BM25_B * doc_length / average_length)
            score += idf * (frequency * (BM25_K1 + 1) / denominator)
        if score:
            scores[record.id] = score
    return scores


def _tokenise_list(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 2 and token not in {"and", "the", "for", "with", "that", "this"}
    ]


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
    specificity_terms = _tokenise(" ".join(_as_strings(record.frontmatter.get("required_query_terms"))))
    if score and specificity_terms:
        specificity_match = query_terms.intersection(specificity_terms)
        if specificity_match:
            score += 6.0 * len(specificity_match)
            reasons.append("specificity:" + ",".join(sorted(specificity_match)))
        else:
            score *= 0.30
            reasons.append("specificity:missing")
    if score:
        type_boost = {
            "wellbeing_moment": 14.0,
            "biomarker": 18.0,
            "evidence_claim": 2.5,
            "wearable_signal": 1.5,
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
        "routes_to_goals",
        "signals",
        "routing",
        "wearable_correlates",
        "population_risk",
        "ingredient_lanes",
        "bands",
        "aliases",
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


def _as_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, dict):
        return [str(item) for item in value.values()]
    return [str(value)]


def _linked_ids_by_field(frontmatter: dict[str, Any]) -> list[tuple[str, str]]:
    linked: list[tuple[str, str]] = []
    for field in LINK_FIELDS:
        linked.extend((field, linked_id) for linked_id in linked_ids(frontmatter.get(field)))
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
