from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


TYPE_TO_GROUP = {
    "evidence_claim": "evidence",
    "biomarker": "biomarkers",
    "product_category": "products",
    "editorial_signal": "editorial",
    "trust_signal": "trust",
    "tone_pattern": "tone",
    "wellbeing_moment": "moments",
    "wearable_signal": "signals",
    "example": "examples",
    "brand_signal": "brand",
    "reference": "reference",
}


class KBRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    type: str = Field(validation_alias=AliasChoices("type", "kind"))
    title: str
    status: str = "active"
    tags: list[str] = Field(default_factory=list)
    path: str
    frontmatter: dict[str, Any] = Field(default_factory=dict)
    body: str
    embedding_text: str = ""
    content_hash: str = ""
    retrieval_priority: int = 1
    score: float = 0.0
    retrieval_reason: list[str] = Field(default_factory=list)

    @property
    def kind(self) -> str:
        return TYPE_TO_GROUP.get(self.type, self.type)

    @property
    def metadata(self) -> dict[str, Any]:
        return self.frontmatter

    def searchable_text(self) -> str:
        return " ".join(
            [
                self.id,
                self.title,
                self.type,
                self.kind,
                " ".join(self.tags),
                str(self.frontmatter.get("summary", "")),
                self.body,
            ]
        )


class KBValidationResult(BaseModel):
    ok: bool
    record_count: int
    counts_by_type: dict[str, int] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
