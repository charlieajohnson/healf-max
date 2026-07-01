from typing import Literal

from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    id: str
    age: int | None = None
    sex: str | None = None
    goals: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    diet: str | None = None
    supplement_appetite: str | None = None
    optimisation_style: str | None = None


class BloodMarker(BaseModel):
    marker: str
    value: float | str
    unit: str | None = None
    status: Literal["low", "suboptimal", "optimal", "high", "unknown"]
    plain_language: str | None = None


class WearableSignal(BaseModel):
    signal: str
    value: float | str
    unit: str | None = None
    status: Literal["low", "below_baseline", "normal", "high", "unknown"]
    window: str | None = None


class WellbeingMoment(BaseModel):
    id: str
    title: str
    signals: list[str] = Field(default_factory=list)
    pillars: list[str] = Field(default_factory=list)
    primary_interpretation: str
    customer_confidence_goal: str
    commercial_mode: str
    safety_boundaries: list[str] = Field(default_factory=list)
    product_lanes: list[str] = Field(default_factory=list)
    priority_order: list[str] = Field(default_factory=list)
    retrieval_query: str = ""


class RecommendationLane(BaseModel):
    id: str
    title: str
    role: str = ""
    priority: int = 0
    mode: str = ""
    reason: str = ""
    evidence_routes: list[str] = Field(default_factory=list)
    product_categories: list[str] = Field(default_factory=list)
    safety_notes: list[str] = Field(default_factory=list)
    do_not_claim: list[str] = Field(default_factory=list)
    evidence_supported: bool = True
    retrieved_support: list[str] = Field(default_factory=list)
    support_note: str = ""


class TurnPlan(BaseModel):
    user_intent: list[str] = Field(default_factory=list)
    inferred_pillars: list[str] = Field(default_factory=list)
    retrieval_needed: bool
    safety_mode: str
    customer_posture: dict[str, str] = Field(default_factory=dict)
    answer_shape: str
