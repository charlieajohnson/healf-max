from __future__ import annotations

from typing import Any

from healf_max.domain.models import TurnPlan, WellbeingMoment
from healf_max.domain.safety import SafetyCheck
from healf_max.tools.bloods import summarise_bloods_markers

BLOODS_FLAGSHIP_QUERY = (
    "hyrox recovery bottleneck low deep sleep low ferritin low vitamin d "
    "suboptimal magnesium tired HRV below baseline creatine electrolytes protein"
)


def build_turn_plan(user_message: str, safety: SafetyCheck) -> TurnPlan:
    text = user_message.lower()
    intents: list[str] = []
    pillars: list[str] = []

    if any(term in text for term in ("energy", "tired", "fatigue", "exhausted")):
        intents.append("improve_energy")
        pillars.extend(["recovery", "nutrition"])
    if any(term in text for term in ("sleep", "oura", "deep sleep", "recovery")):
        intents.append("improve_sleep_quality")
        pillars.append("sleep")
    if any(term in text for term in ("hyrox", "marathon", "training", "gym", "run")):
        intents.append("support_training")
        pillars.extend(["performance", "hydration"])
    if any(term in text for term in ("blood", "ferritin", "b12", "vitamin d", "thyroid")):
        intents.append("understand_biomarkers")
        pillars.append("biomarkers")

    if not intents:
        intents.append("general_wellbeing_decision")
    if not pillars:
        pillars.extend(["recovery", "routine"])

    posture = {
        "tone": "direct_low_shame",
        "commercial_pressure": "low",
        "confidence_goal": "one_next_useful_decision",
    }
    answer_shape = (
        "safety_first_followup"
        if safety.category != "wellness_ok"
        else "first_read_then_priority_lanes"
    )

    return TurnPlan(
        user_intent=_dedupe(intents),
        inferred_pillars=_dedupe(pillars),
        retrieval_needed=True,
        safety_mode=safety.category,
        customer_posture=posture,
        answer_shape=answer_shape,
    )


def infer_wellbeing_moment(customer: dict[str, Any], bloods: dict[str, Any], wearable: dict[str, Any]) -> WellbeingMoment:
    bloods_summary = summarise_bloods_markers(bloods)
    goals = _as_text_list(customer.get("goals"))
    constraints = _as_text_list(customer.get("constraints"))
    marker_status = {str(marker["marker"]): str(marker["status"]) for marker in bloods.get("markers", [])}
    signal_status = {str(signal["signal"]): str(signal["status"]) for signal in wearable.get("signals", [])}

    has_hyrox_goal = any("hyrox" in goal for goal in goals) or signal_status.get("training_load") == "high"
    low_deep_sleep = signal_status.get("deep_sleep_avg") == "low" or signal_status.get("deep_sleep") == "low"
    fatigue_goal = any("energy" in goal or "fatigue" in goal for goal in goals)
    recovery_marker = (
        marker_status.get("ferritin") == "low"
        or marker_status.get("vitamin_d") == "low"
        or marker_status.get("magnesium_status") == "suboptimal"
    )

    if has_hyrox_goal and low_deep_sleep and fatigue_goal and recovery_marker:
        return WellbeingMoment(
            id="recovery_bottleneck_with_bloods",
            title="Recovery bottleneck with Bloods",
            primary_interpretation="recovery_bottleneck",
            signals=[
                "hyrox_training_block",
                "low_deep_sleep",
                "hrv_below_baseline",
                "resting_hr_slightly_elevated",
                "fatigue",
                "low_ferritin",
                "low_vitamin_d",
                "suboptimal_magnesium",
                "suboptimal_b12",
            ],
            pillars=["eat", "move", "sleep"],
            customer_confidence_goal="next_best_step",
            commercial_mode="category_first",
            safety_boundaries=_dedupe(
                [
                    bloods_summary["safety_mode"],
                    "no_diagnosis",
                    "abnormal_bloods_need_follow_up",
                    "no_prescriptive_dosing",
                ]
            ),
            product_lanes=[
                "magnesium_glycinate",
                "electrolytes",
                "creatine",
                "protein",
                "vitamin_d_contextual",
                "omega_3",
            ],
            priority_order=[
                "ferritin_follow_up",
                "vitamin_d_practitioner_guided",
                "sleep_support",
                "training_basics",
                "omega_3_contextual",
            ],
            retrieval_query=BLOODS_FLAGSHIP_QUERY,
        )

    return WellbeingMoment(
        id="general_bloods_check_in",
        title="General Bloods check-in",
        primary_interpretation="bloods_context_review",
        signals=_dedupe(list(marker_status) + list(signal_status) + constraints),
        pillars=["eat", "move", "sleep"],
        customer_confidence_goal="next_best_step",
        commercial_mode="category_first",
        safety_boundaries=_dedupe([bloods_summary["safety_mode"], *bloods_summary["safety_boundaries"]]),
        product_lanes=[],
        priority_order=["bloods_follow_up", "sleep_support", "training_basics"],
        retrieval_query=BLOODS_FLAGSHIP_QUERY,
    )


def _as_text_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).lower() for item in value]
    if value is None:
        return []
    return [str(value).lower()]


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output
