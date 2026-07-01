from __future__ import annotations

from healf_max.domain.models import RecommendationLane


DEFAULT_LANES = [
    RecommendationLane(
        id="lane.recovery_basics",
        title="Recovery basics",
        role="Stabilise sleep, meals, hydration and training load before adding complexity.",
        priority=1,
        evidence_routes=["sleep", "energy", "training-load"],
        product_categories=["electrolytes", "protein", "magnesium"],
        safety_notes=["Do not frame fatigue as solved by supplements."],
        do_not_claim=["treats insomnia", "treats fatigue"],
    ),
    RecommendationLane(
        id="lane.biomarker_followup",
        title="Biomarker follow-up",
        role="Route abnormal blood markers into appropriate review before product selection.",
        priority=0,
        evidence_routes=["ferritin", "b12", "vitamin-d", "thyroid"],
        product_categories=[],
        safety_notes=["No product trigger from abnormal bloods."],
        do_not_claim=["treats deficiency", "replaces clinician review"],
    ),
]


def default_recommendation_lanes() -> list[RecommendationLane]:
    return list(DEFAULT_LANES)
