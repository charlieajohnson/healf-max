from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from healf_max.kb.loader import load_kb_records
from healf_max.kb.schemas import KBRecord
from healf_max.kb.search import tokenise_for_index

RECORDS_FILE = "kb_records.jsonl"
VOCAB_FILE = "kb_vocab.json"
MATRIX_FILE = "kb_matrix.npy"


def build_index(*, kb_dir: str | Path, storage_dir: str | Path) -> int:
    storage = Path(storage_dir)
    storage.mkdir(parents=True, exist_ok=True)

    records = load_kb_records(kb_dir)
    vocab = _build_vocab(records)
    matrix = _build_matrix(records, vocab)

    with (storage / RECORDS_FILE).open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")

    (storage / VOCAB_FILE).write_text(json.dumps(vocab, indent=2), encoding="utf-8")
    np.save(storage / MATRIX_FILE, matrix)
    return len(records)


def search_index(
    query: str,
    *,
    storage_dir: str | Path,
    limit: int = 6,
    kinds: set[str] | None = None,
) -> list[KBRecord]:
    storage = Path(storage_dir)
    records_path = storage / RECORDS_FILE
    vocab_path = storage / VOCAB_FILE
    matrix_path = storage / MATRIX_FILE
    if not records_path.exists() or not vocab_path.exists() or not matrix_path.exists():
        return []

    records = _load_records(records_path)
    vocab = json.loads(vocab_path.read_text(encoding="utf-8"))
    matrix = np.load(matrix_path)
    query_vector = np.zeros(len(vocab), dtype=np.float32)
    for token in tokenise_for_index(query):
        index = vocab.get(token)
        if index is not None:
            query_vector[index] = 1.0

    if not query_vector.any():
        return []

    scores = matrix @ query_vector
    ranked_indices = np.argsort(scores)[::-1]
    output: list[KBRecord] = []
    for index in ranked_indices:
        score = float(scores[index])
        if score <= 0:
            break
        record = records[int(index)]
        if kinds and record.kind not in kinds:
            continue
        output.append(record.model_copy(update={"score": score}))
        if len(output) >= limit:
            break
    return output


def _build_vocab(records: list[KBRecord]) -> dict[str, int]:
    terms = sorted({term for record in records for term in tokenise_for_index(record.searchable_text())})
    return {term: index for index, term in enumerate(terms)}


def _build_matrix(records: list[KBRecord], vocab: dict[str, int]) -> np.ndarray:
    matrix = np.zeros((len(records), len(vocab)), dtype=np.float32)
    for row, record in enumerate(records):
        for term in tokenise_for_index(record.searchable_text()):
            matrix[row, vocab[term]] += 1.0
    return matrix


def _load_records(path: Path) -> list[KBRecord]:
    records: list[KBRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(KBRecord.model_validate_json(line))
    return records
