from __future__ import annotations

import re
from pathlib import Path

from healf_max.kb.loader import load_kb_records
from healf_max.kb.schemas import KBRecord


def lexical_search(
    query: str,
    records: list[KBRecord],
    *,
    limit: int = 6,
    kinds: set[str] | None = None,
) -> list[KBRecord]:
    query_terms = _tokenise(query)
    if not query_terms:
        return []

    scored: list[KBRecord] = []
    for record in records:
        if kinds and record.kind not in kinds:
            continue
        text_terms = _tokenise(record.searchable_text())
        if not text_terms:
            continue
        overlap = query_terms.intersection(text_terms)
        if not overlap:
            continue
        title_terms = _tokenise(record.title)
        tag_terms = set(record.tags)
        score = float(len(overlap))
        score += 1.5 * len(query_terms.intersection(title_terms))
        score += 1.2 * len(query_terms.intersection(tag_terms))
        scored.append(record.model_copy(update={"score": score}))

    return sorted(scored, key=lambda item: item.score, reverse=True)[:limit]


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


def _tokenise(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z0-9]+", text.lower())
        if len(token) > 2 and token not in {"and", "the", "for", "with", "that", "this"}
    }


def tokenise_for_index(text: str) -> list[str]:
    return sorted(_tokenise(text))
