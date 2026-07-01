from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from healf_max.kb.loader import iter_markdown_files
from healf_max.kb.parser import parse_markdown_file
from healf_max.kb.schemas import KBValidationResult


def validate_kb(kb_dir: str | Path) -> KBValidationResult:
    root = Path(kb_dir)
    if not root.exists():
        return KBValidationResult(
            ok=True,
            record_count=0,
            warnings=[f"KB directory does not exist yet: {root}"],
        )

    errors: list[str] = []
    warnings: list[str] = []
    count = 0
    seen_ids: set[str] = set()

    for path in iter_markdown_files(root):
        try:
            record = parse_markdown_file(path, kb_root=root)
        except (ValidationError, ValueError, OSError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
            continue
        count += 1
        if record.id in seen_ids:
            errors.append(f"{path.relative_to(root)}: duplicate id '{record.id}'")
        seen_ids.add(record.id)
        if not record.body:
            warnings.append(f"{path.relative_to(root)}: empty body")
        if not record.tags:
            warnings.append(f"{path.relative_to(root)}: no tags")

    return KBValidationResult(ok=not errors, record_count=count, warnings=warnings, errors=errors)
