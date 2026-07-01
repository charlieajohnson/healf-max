from __future__ import annotations

from pathlib import Path
from typing import Any

import frontmatter

from healf_max.kb.schemas import KBRecord


def parse_markdown_file(path: Path, *, kb_root: Path | None = None) -> KBRecord:
    source_path = str(path.relative_to(kb_root)) if kb_root else str(path)
    return parse_markdown_text(path.read_text(encoding="utf-8"), source_path=source_path)


def parse_markdown_text(markdown: str, *, source_path: str) -> KBRecord:
    post = frontmatter.loads(markdown)
    metadata: dict[str, Any] = dict(post.metadata)
    record_id = str(metadata.pop("id", "") or _default_id(source_path))
    title = str(metadata.pop("title", "") or _default_title(source_path))
    kind = str(metadata.pop("kind", "") or _kind_from_path(source_path))
    tags = metadata.pop("tags", [])

    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    return KBRecord(
        id=record_id,
        title=title,
        kind=kind,  # type: ignore[arg-type]
        tags=[str(tag) for tag in tags],
        body=post.content.strip(),
        path=source_path,
        metadata=metadata,
    )


def _default_id(source_path: str) -> str:
    return Path(source_path).with_suffix("").as_posix().replace("/", ".")


def _default_title(source_path: str) -> str:
    return Path(source_path).stem.replace("-", " ").replace("_", " ").title()


def _kind_from_path(source_path: str) -> str:
    first = Path(source_path).parts[0] if Path(source_path).parts else "reference"
    if first in {
        "evidence",
        "biomarkers",
        "products",
        "editorial",
        "trust",
        "tone",
        "moments",
        "examples",
    }:
        return first
    return "reference"
