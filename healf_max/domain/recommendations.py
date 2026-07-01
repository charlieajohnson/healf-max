from __future__ import annotations

from typing import Any

from healf_max.domain.models import RecommendationLane, WellbeingMoment


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


def build_recommendation_lanes(
    moment: WellbeingMoment,
    retrieved_records: list[Any],
    *,
    drop_unsupported: bool = False,
) -> list[RecommendationLane]:
    if moment.id != "recovery_bottleneck_with_bloods":
        base = default_recommendation_lanes()
    else:
        base = _flagship_lanes()

    retrieved_ids = {getattr(record, "id", "") for record in retrieved_records}
    annotated = [_annotate_lane(lane, retrieved_ids) for lane in base]
    if drop_unsupported:
        annotated = [lane for lane in annotated if lane.evidence_supported or lane.priority <= 2]
    return annotated


def _flagship_lanes() -> list[RecommendationLane]:
    return [
        RecommendationLane(
            id="ferritin_follow_up",
            title="Ferritin first",
            mode="follow_up_not_product",
            role="Route low ferritin to proper follow-up before product comparison.",
            priority=1,
            reason=(
                "Low ferritin can be relevant to fatigue and training tolerance, "
                "but it is not something to wellness your way around."
            ),
            evidence_routes=["ferritin_low_fatigue"],
            safety_notes=["abnormal_bloods_need_follow_up", "no_diagnosis", "no_dosing"],
            do_not_claim=["iron product treats fatigue", "treats anaemia"],
        ),
        RecommendationLane(
            id="vitamin_d_contextual",
            title="Vitamin D next",
            mode="practitioner_guided",
            role="Keep low vitamin D inside the Bloods follow-up plan.",
            priority=2,
            reason="Vitamin D is low in this panel, so this is practitioner-guided context rather than guessed dosing.",
            evidence_routes=["vitamin_d_low_status"],
            product_categories=["vitamin_d_contextual"],
            safety_notes=["no_prescriptive_dosing", "abnormal_bloods_need_follow_up"],
            do_not_claim=["take X mg", "treats deficiency"],
        ),
        RecommendationLane(
            id="magnesium_glycinate",
            title="Magnesium glycinate",
            mode="category_comparison",
            role="Low-chaos sleep support category.",
            priority=3,
            reason="Suboptimal magnesium plus low deep sleep and recovery load makes magnesium glycinate a clean category to compare.",
            evidence_routes=["magnesium_sleep_recovery"],
            product_categories=["magnesium_glycinate"],
            safety_notes=["wellness_support_only", "check_medications_if_relevant"],
            do_not_claim=["cures insomnia", "fixes Oura scores"],
        ),
        RecommendationLane(
            id="electrolytes",
            title="Electrolytes",
            mode="training_basic",
            role="Support hydration around sweat-heavy Hyrox sessions.",
            priority=4,
            reason="Training basics matter before a bigger stack: electrolytes are a simple lane for sweat-heavy sessions.",
            evidence_routes=["electrolytes_training_hydration"],
            product_categories=["electrolytes"],
            safety_notes=["wellness_support_only"],
            do_not_claim=["treats fatigue"],
        ),
        RecommendationLane(
            id="protein",
            title="Protein",
            mode="intake_check_first",
            role="Check intake before buying anything.",
            priority=5,
            reason="Protein is a recovery basic, especially for a mostly plant-based Hyrox block, but intake comes before product certainty.",
            evidence_routes=["protein_training_recovery"],
            product_categories=["protein"],
            safety_notes=["food_first_comparison"],
            do_not_claim=["builds muscle by itself"],
        ),
        RecommendationLane(
            id="creatine",
            title="Creatine",
            mode="training_basic",
            role="Routine-compatible performance support.",
            priority=6,
            reason="Creatine is a category worth comparing if it fits the routine after follow-up and recovery basics are handled.",
            evidence_routes=["creatine_high_intensity_training"],
            product_categories=["creatine"],
            safety_notes=["wellness_support_only"],
            do_not_claim=["treats tiredness"],
        ),
        RecommendationLane(
            id="omega_3",
            title="Omega-3",
            mode="contextual_lower_priority",
            role="Lower-priority general health context.",
            priority=7,
            reason="Omega-3 is contextual here because the index is suboptimal, but it should not be framed as inflammation treatment.",
            evidence_routes=["omega_3_general_health"],
            product_categories=["omega_3"],
            safety_notes=["wellness_support_only"],
            do_not_claim=["anti-inflammatory treatment", "treats inflammation"],
        ),
    ]


def _annotate_lane(lane: RecommendationLane, retrieved_ids: set[str]) -> RecommendationLane:
    declared = set(lane.evidence_routes) | set(lane.product_categories)
    support = sorted(declared.intersection(retrieved_ids))
    supported = bool(support)
    note = (
        f"retrieved support: {', '.join(support)}"
        if supported
        else "no declared evidence/category route present in retrieval; treat as authored default"
    )
    return lane.model_copy(
        update={
            "evidence_supported": supported,
            "retrieved_support": support,
            "support_note": note,
        }
    )
