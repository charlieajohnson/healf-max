from __future__ import annotations

from healf_max.config import load_settings
from healf_max.kb.search import search_kb


def search_products(query: str, *, limit: int = 4) -> list[dict[str, object]]:
    settings = load_settings()
    records = search_kb(
        query,
        kb_dir=settings.kb_dir,
        storage_dir=settings.storage_dir,
        limit=limit,
        kinds={"products"},
    )
    return [record.model_dump() for record in records]
