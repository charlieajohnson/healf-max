from __future__ import annotations

import json
import os
from pathlib import Path

from healf_max.config import load_settings
from healf_max.kb.graph import GRAPH_FILE, build_record_graph
from healf_max.kb.loader import load_kb_records
from healf_max.kb.schemas import KBRecord
from healf_max.kb.validator import validate_kb

INDEX_FILE = "kb_index.jsonl"
MANIFEST_FILE = "kb_manifest.json"
EMBEDDINGS_FILE = "kb_embeddings.npy"
LEGACY_RECORDS_FILE = "kb_records.jsonl"
LEGACY_VOCAB_FILE = "kb_vocab.json"
LEGACY_MATRIX_FILE = "kb_matrix.npy"


def build_index(*, kb_dir: str | Path, storage_dir: str | Path) -> int:
    storage = Path(storage_dir)
    storage.mkdir(parents=True, exist_ok=True)

    validation = validate_kb(kb_dir)
    if not validation.ok:
        raise ValueError("KB validation failed: " + "; ".join(validation.errors))

    records = load_kb_records(kb_dir)

    with (storage / INDEX_FILE).open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
    graph = build_record_graph(records)
    (storage / GRAPH_FILE).write_text(json.dumps(graph, indent=2, sort_keys=True), encoding="utf-8")

    embedding_status = "not_requested"
    embedding_model = os.getenv("HEALF_MAX_EMBEDDING_MODEL", "text-embedding-3-small")
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            import numpy as np
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model=embedding_model,
                input=[record.embedding_text for record in records],
            )
            embeddings = np.array([item.embedding for item in response.data], dtype=np.float32)
            np.save(storage / EMBEDDINGS_FILE, embeddings)
            embedding_status = "created"
        except Exception as exc:  # pragma: no cover - provider state depends on local account.
            embedding_status = f"failed:{exc.__class__.__name__}"
    else:
        (storage / EMBEDDINGS_FILE).unlink(missing_ok=True)

    manifest = {
        "record_count": len(records),
        "counts_by_type": validation.counts_by_type,
        "embedding_status": embedding_status,
        "embedding_model": embedding_model,
        "index_file": INDEX_FILE,
        "graph_file": GRAPH_FILE,
        "graph_edge_count": graph["stats"]["edge_count"],
        "embeddings_file": EMBEDDINGS_FILE if embedding_status == "created" else None,
        "content_hashes": {record.id: record.content_hash for record in records},
    }
    (storage / MANIFEST_FILE).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    for legacy in (LEGACY_RECORDS_FILE, LEGACY_VOCAB_FILE, LEGACY_MATRIX_FILE):
        (storage / legacy).unlink(missing_ok=True)
    return len(records)


def search_index(
    query: str,
    *,
    storage_dir: str | Path,
    limit: int = 6,
    kinds: set[str] | None = None,
) -> list[KBRecord]:
    storage = Path(storage_dir)
    records_path = storage / INDEX_FILE
    if not records_path.exists():
        return []

    records = _load_records(records_path)
    embedding_scores = _embedding_scores(query, storage_dir=storage, records=records)

    from healf_max.kb.search import score_records

    return score_records(
        query,
        records,
        limit=limit,
        kinds=kinds,
        embedding_scores=embedding_scores,
    )


def load_index_records(storage_dir: str | Path) -> list[KBRecord]:
    records_path = Path(storage_dir) / INDEX_FILE
    if not records_path.exists():
        return []
    return _load_records(records_path)


def _load_records(path: Path) -> list[KBRecord]:
    records: list[KBRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(KBRecord.model_validate_json(line))
    return records


def _embedding_scores(query: str, *, storage_dir: Path, records: list[KBRecord]) -> dict[str, float]:
    embeddings_path = storage_dir / EMBEDDINGS_FILE
    if not embeddings_path.exists() or not os.getenv("OPENAI_API_KEY"):
        return {}
    try:
        import numpy as np
        from openai import OpenAI

        settings = load_settings()
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.embeddings.create(model=settings.embedding_model, input=query)
        query_vector = np.array(response.data[0].embedding, dtype=np.float32)
        matrix = np.load(embeddings_path)
        query_norm = np.linalg.norm(query_vector)
        matrix_norm = np.linalg.norm(matrix, axis=1)
        denominator = matrix_norm * query_norm
        similarities = np.divide(
            matrix @ query_vector,
            denominator,
            out=np.zeros(len(records), dtype=np.float32),
            where=denominator != 0,
        )
        return {record.id: float(score) for record, score in zip(records, similarities, strict=False)}
    except Exception:  # pragma: no cover - provider state depends on local account.
        return {}


def legacy_index_files() -> tuple[str, str, str]:
    return LEGACY_RECORDS_FILE, LEGACY_VOCAB_FILE, LEGACY_MATRIX_FILE
