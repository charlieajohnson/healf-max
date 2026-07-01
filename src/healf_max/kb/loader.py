from __future__ import annotations

from pathlib import Path

from healf_max.kb.parser import parse_markdown_file
from healf_max.kb.schemas import KBRecord


def iter_markdown_files(kb_dir: str | Path) -> list[Path]:
    root = Path(kb_dir)
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.md")
        if not any(part.startswith(".") for part in path.relative_to(root).parts)
        and "_schemas" not in path.relative_to(root).parts
        and path.name not in {"README.md", "LLM.md"}
    )


def load_kb_records(kb_dir: str | Path) -> list[KBRecord]:
    root = Path(kb_dir)
    records: list[KBRecord] = []
    for path in iter_markdown_files(root):
        records.append(parse_markdown_file(path, kb_root=root))
    return records
