from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from healf_max.kb.loader import iter_markdown_files
from healf_max.kb.parser import parse_markdown_file
from healf_max.kb.schemas import KBValidationResult

BANNED_BODY_PHRASES = (
    "cures",
    "treats anaemia",
    "fixes fatigue",
    "guaranteed",
    "clinically proven stack",
)

REQUIRED_FIELDS = ("id", "type", "title", "status", "retrieval_priority", "reviewed_at")
HEALTH_TYPES = {"evidence_claim", "biomarker", "product_category", "wellbeing_moment", "wearable_signal"}
LINK_FIELDS = (
    "biomarker_routes",
    "evidence_routes",
    "wearable_signals",
    "product_lanes",
    "editorial_signals",
    "tone_patterns",
    "trust_signals",
)


def validate_kb(kb_dir: str | Path, *, strict: bool = False) -> KBValidationResult:
    root = Path(kb_dir)
    if not root.exists():
        return KBValidationResult(
            ok=True,
            record_count=0,
            warnings=[f"KB directory does not exist yet: {root}"],
        )

    errors: list[str] = []
    warnings: list[str] = []
    records = []
    seen_ids: set[str] = set()
    counts_by_type: dict[str, int] = {}

    for path in iter_markdown_files(root):
        try:
            record = parse_markdown_file(path, kb_root=root)
        except (ValidationError, ValueError, OSError) as exc:
            errors.append(f"{path.relative_to(root)}: {exc}")
            continue
        records.append(record)
        counts_by_type[record.type] = counts_by_type.get(record.type, 0) + 1
        if record.id in seen_ids:
            errors.append(f"{path.relative_to(root)}: duplicate id '{record.id}'")
        seen_ids.add(record.id)
        if not record.body:
            warnings.append(f"{path.relative_to(root)}: empty body")
        if not record.tags:
            warnings.append(f"{path.relative_to(root)}: no tags")
        for field in REQUIRED_FIELDS:
            if field not in record.frontmatter:
                errors.append(f"{path.relative_to(root)}: missing required frontmatter '{field}'")
        if record.type in HEALTH_TYPES:
            for field in ("safety_boundary", "prohibited_claims"):
                if not record.frontmatter.get(field):
                    errors.append(f"{path.relative_to(root)}: health record missing '{field}'")
        body_lower = record.body.lower()
        for phrase in BANNED_BODY_PHRASES:
            if phrase in body_lower:
                errors.append(f"{path.relative_to(root)}: banned body phrase '{phrase}'")

    ids = {record.id for record in records}
    for record in records:
        for field in LINK_FIELDS:
            for linked_id in _as_list(record.frontmatter.get(field)):
                if linked_id not in ids:
                    warnings.append(f"{record.path}: linked id '{linked_id}' in '{field}' not found")

    if strict and warnings:
        errors.extend(f"strict warning: {warning}" for warning in warnings)

    return KBValidationResult(
        ok=not errors,
        record_count=len(records),
        counts_by_type=counts_by_type,
        warnings=warnings,
        errors=errors,
    )


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]
