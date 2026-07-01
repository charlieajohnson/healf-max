from __future__ import annotations

from healf_max.domain.models import TurnPlan
from healf_max.domain.safety import SafetyCheck


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


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            output.append(value)
    return output
