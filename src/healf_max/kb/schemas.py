from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


KBKind = Literal[
    "evidence",
    "biomarkers",
    "products",
    "editorial",
    "trust",
    "tone",
    "moments",
    "examples",
    "reference",
]


class KBRecord(BaseModel):
    id: str
    title: str
    kind: KBKind
    tags: list[str] = Field(default_factory=list)
    body: str
    path: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    score: float = 0.0

    def searchable_text(self) -> str:
        return " ".join(
            [
                self.id,
                self.title,
                self.kind,
                " ".join(self.tags),
                self.body,
            ]
        )


class KBValidationResult(BaseModel):
    ok: bool
    record_count: int
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
