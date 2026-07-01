from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import frontmatter

from healf_max.kb.schemas import KBRecord


def parse_markdown_file(path: Path, *, kb_root: Path | None = None) -> KBRecord:
    source_path = str(path.relative_to(kb_root)) if kb_root else str(path)
    return parse_markdown_text(path.read_text(encoding="utf-8"), source_path=source_path)


def parse_markdown_text(markdown: str, *, source_path: str) -> KBRecord:
    post = frontmatter.loads(markdown)
    frontmatter_data: dict[str, Any] = dict(post.metadata)
    record_id = str(frontmatter_data.get("id", "") or _default_id(source_path))
    title = str(frontmatter_data.get("title", "") or _default_title(source_path))
    record_type = str(frontmatter_data.get("type", "") or frontmatter_data.get("kind", "") or _type_from_path(source_path))
    status = str(frontmatter_data.get("status", "active"))
    tags = frontmatter_data.get("tags", [])
    retrieval_priority = int(frontmatter_data.get("retrieval_priority", 1) or 1)

    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    normalised_tags = [str(tag) for tag in tags]
    body = post.content.strip()
    embedding_text = _embedding_text(
        title=title,
        record_type=record_type,
        tags=normalised_tags,
        summary=str(frontmatter_data.get("summary", "")),
        body=body,
    )

    return KBRecord(
        id=record_id,
        title=title,
        type=record_type,
        status=status,
        tags=normalised_tags,
        frontmatter=frontmatter_data,
        body=body,
        path=source_path,
        embedding_text=embedding_text,
        content_hash=hashlib.sha256(markdown.encode("utf-8")).hexdigest()[:16],
        retrieval_priority=retrieval_priority,
    )


def _default_id(source_path: str) -> str:
    return Path(source_path).with_suffix("").as_posix().replace("/", ".")


def _default_title(source_path: str) -> str:
    return Path(source_path).stem.replace("-", " ").replace("_", " ").title()


def _type_from_path(source_path: str) -> str:
    first = Path(source_path).parts[0] if Path(source_path).parts else "reference"
    return {
        "evidence": "evidence_claim",
        "biomarkers": "biomarker",
        "products": "product_category",
        "editorial": "editorial_signal",
        "trust": "trust_signal",
        "tone": "tone_pattern",
        "moments": "wellbeing_moment",
        "examples": "example",
        "brand": "brand_signal",
    }.get(first, "reference")


def _embedding_text(*, title: str, record_type: str, tags: list[str], summary: str, body: str) -> str:
    return "\n".join(
        part
        for part in [
            title,
            record_type,
            " ".join(tags),
            summary,
            body,
        ]
        if part
    )
