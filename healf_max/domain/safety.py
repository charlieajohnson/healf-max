from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel


SafetyCategory = Literal[
    "wellness_ok",
    "biomarker_followup",
    "medication_interaction",
    "pregnancy_or_child",
    "urgent_symptoms",
    "diagnosis_or_prescription_request",
    "out_of_scope",
]


class SafetyCheck(BaseModel):
    category: SafetyCategory
    rationale: str
    boundary: str
    allow_product_recommendations: bool = True


URGENT_PATTERNS = (
    r"\bchest pain\b",
    r"\bshortness of breath\b",
    r"\bbreathless\b",
    r"\bfaint(?:ed|ing)?\b",
    r"\bsevere pain\b",
    r"\bstroke\b",
    r"\bsuicidal\b",
    r"\bheart attack\b",
)

PREGNANCY_OR_CHILD_PATTERNS = (
    r"\bpregnan(?:t|cy)\b",
    r"\bbreastfeeding\b",
    r"\btrying to conceive\b",
    r"\bchild\b",
    r"\bkid\b",
    r"\btoddler\b",
    r"\bunder 18\b",
)

MEDICATION_PATTERNS = (
    r"\bmedication\b",
    r"\bmedicine\b",
    r"\bssri\b",
    r"\bsertraline\b",
    r"\bprozac\b",
    r"\bfluoxetine\b",
    r"\bbeta blocker\b",
    r"\bblood thinner\b",
    r"\bwarfarin\b",
    r"\bmetformin\b",
    r"\bstatin\b",
    r"\binteract(?:ion|s)?\b",
    r"\bcontraindicat",
)

DIAGNOSIS_PATTERNS = (
    r"\bdiagnose\b",
    r"\bdiagnosis\b",
    r"\bwhat disease\b",
    r"\bdo i have\b",
    r"\bprescribe\b",
    r"\btreat my\b",
    r"\bcure\b",
)

BIOMARKER_PATTERNS = (
    r"\bferritin\b",
    r"\bhaemoglobin\b",
    r"\bhemoglobin\b",
    r"\biron\b",
    r"\bb12\b",
    r"\bvitamin d\b",
    r"\bthyroid\b",
    r"\btsh\b",
    r"\bhdl\b",
    r"\bldl\b",
    r"\bhba1c\b",
    r"\bcortisol\b",
    r"\btestosterone\b",
    r"\boestrogen\b",
    r"\bestrogen\b",
    r"\bcrp\b",
    r"\bmarker\b",
    r"\bbloods?\b",
)

OUT_OF_SCOPE_PATTERNS = (
    r"\bcrypto\b",
    r"\bstock pick\b",
    r"\bfootball accumulator\b",
)


def classify_safety(message: str) -> SafetyCheck:
    text = _normalise(message)

    if _matches(text, URGENT_PATTERNS):
        return SafetyCheck(
            category="urgent_symptoms",
            rationale="Potential urgent symptom language detected.",
            boundary="Do not recommend products. Advise urgent medical help.",
            allow_product_recommendations=False,
        )
    if _matches(text, PREGNANCY_OR_CHILD_PATTERNS):
        return SafetyCheck(
            category="pregnancy_or_child",
            rationale="Pregnancy, breastfeeding, conception or child-related context detected.",
            boundary="Recommend clinician, pharmacist or qualified practitioner review before supplements.",
            allow_product_recommendations=False,
        )
    if _matches(text, MEDICATION_PATTERNS):
        return SafetyCheck(
            category="medication_interaction",
            rationale="Medication or interaction context detected.",
            boundary="Recommend clinician or pharmacist review before adding supplements.",
            allow_product_recommendations=False,
        )
    if _matches(text, DIAGNOSIS_PATTERNS):
        return SafetyCheck(
            category="diagnosis_or_prescription_request",
            rationale="Diagnosis, prescription, cure or treatment request detected.",
            boundary="Do not diagnose, prescribe or claim treatment.",
            allow_product_recommendations=False,
        )
    if _matches(text, BIOMARKER_PATTERNS) and _has_abnormal_qualifier(text):
        return SafetyCheck(
            category="biomarker_followup",
            rationale="Abnormal or uncertain biomarker language detected.",
            boundary="Explain the signal in plain English and route to appropriate follow-up before products.",
            allow_product_recommendations=False,
        )
    if _matches(text, OUT_OF_SCOPE_PATTERNS):
        return SafetyCheck(
            category="out_of_scope",
            rationale="The request is outside Healf-Max's wellbeing scope.",
            boundary="Decline briefly and redirect to wellbeing goals.",
            allow_product_recommendations=False,
        )
    return SafetyCheck(
        category="wellness_ok",
        rationale="No deterministic safety escalation detected.",
        boundary="Stay in wellness guidance; keep recommendations category-first.",
        allow_product_recommendations=True,
    )


def _normalise(message: str) -> str:
    return re.sub(r"\s+", " ", message.strip().lower())


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _has_abnormal_qualifier(text: str) -> bool:
    return bool(
        re.search(
            r"\b(low|high|raised|elevated|suboptimal|deficien(?:t|cy)|out of range|abnormal|flagged|below|above|tired|fatigue|exhausted)\b",
            text,
        )
    )
