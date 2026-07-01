from __future__ import annotations

import json
from typing import Any

from healf_max.config import Settings, load_settings
from healf_max.domain.planner import infer_wellbeing_moment
from healf_max.domain.recommendations import build_recommendation_lanes
from healf_max.kb.loader import load_kb_records
from healf_max.kb.schemas import KBRecord
from healf_max.kb.search import search_kb
from healf_max.tools.bloods import get_bloods_context, get_latest_bloods_context, summarise_bloods_markers
from healf_max.tools.customer import get_customer_context

TRACE_RECORD_IDS = [
    "hyrox_recovery_bottleneck_with_bloods",
    "ferritin",
    "vitamin_d",
    "magnesium",
    "ferritin_low_fatigue",
    "vitamin_d_low_status",
    "magnesium_sleep_recovery",
    "creatine_high_intensity_training",
    "electrolytes_training_hydration",
    "protein_training_recovery",
    "magnesium_glycinate",
    "electrolytes",
    "creatine",
    "protein",
    "biology_has_answers",
    "stop_leaking_recovery",
    "curated_not_random",
    "group_chat_signal",
    "not_stack_moment",
]


def build_bloods_demo_plan(profile_path: str | None = None, *, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or load_settings()
    customer = get_customer_context()
    bloods = get_latest_bloods_context(profile_path)
    from healf_max.demo.wearable import get_wearable_context

    wearable = get_wearable_context()
    marker_summary = summarise_bloods_markers(bloods)
    moment = infer_wellbeing_moment(customer, bloods, wearable)
    retrieved = _retrieve_trace_records(moment.retrieval_query, settings=settings)
    lanes = build_recommendation_lanes(moment, retrieved)
    payload = {
        "customer_id": customer["id"],
        "panel_id": bloods["panel_id"],
        "wearable_source": wearable["source"],
        "safety_mode": marker_summary["safety_mode"],
        "wellbeing_moment": moment.id,
        "priority_order": moment.priority_order,
        "recommendation_lanes": [lane.model_dump() for lane in lanes],
        "retrieved_record_ids": [record.id for record in retrieved],
        "retrieved_record_paths": [record.path for record in retrieved],
        "retrieval_query": moment.retrieval_query,
        "customer": customer,
        "bloods": bloods,
        "wearable": wearable,
        "moment": moment.model_dump(),
        "bloods_summary": marker_summary,
    }
    return payload


def render_bloods_demo_json(plan: dict[str, Any]) -> str:
    public = {
        "customer_id": plan["customer_id"],
        "panel_id": plan["panel_id"],
        "safety_mode": plan["safety_mode"],
        "wellbeing_moment": plan["wellbeing_moment"],
        "priority_order": plan["priority_order"],
        "recommendation_lanes": plan["recommendation_lanes"],
        "retrieved_record_ids": plan["retrieved_record_ids"],
    }
    return json.dumps(public, indent=2)


def render_bloods_demo_debug(plan: dict[str, Any]) -> str:
    lines = [
        f"Loaded customer: {plan['customer_id']}",
        f"Loaded Bloods panel: {plan['panel_id']}",
        f"Loaded wearable context: {plan['wearable_source']}",
        f"Safety mode: {plan['safety_mode']}",
        f"Inferred moment: {plan['wellbeing_moment']}",
        "Priority order:",
    ]
    for index, item in enumerate(plan["priority_order"], start=1):
        lines.append(f"  {index}. {item}")
    lines.append("Lane support:")
    for lane in plan["recommendation_lanes"]:
        support = ", ".join(lane["retrieved_support"]) if lane["retrieved_support"] else "no retrieved declared route"
        status = "supported by" if lane["evidence_supported"] else "unsupported"
        lines.append(f"  {lane['id']}: {status} {support}")
    lines.append("Retrieved KB records:")
    for path in plan["retrieved_record_paths"]:
        lines.append(f"  {path}")
    return "\n".join(lines)


def render_bloods_demo_fallback(plan: dict[str, Any]) -> str:
    markers = {marker["marker"]: marker for marker in plan["bloods"]["markers"]}
    signals = {signal["signal"]: signal for signal in plan["wearable"]["signals"]}
    signal_summary = (
        "Hyrox in 12 weeks, deep sleep averaging "
        f"{signals['deep_sleep_avg']['value']} minutes, HRV below baseline, resting heart rate slightly up, "
        "low ferritin, low vitamin D and suboptimal magnesium."
    )
    return "\n\n".join(
        [
            "Your biology is doing the annoying but useful thing: telling on you.",
            signal_summary,
            "That is not a build-me-a-giant-stack moment. That is a stop leaking recovery moment.",
            "Here's the order I'd use:",
            "\n".join(
                [
                    "1. Ferritin first",
                    markers["ferritin"]["plain_language"],
                    "Get this followed up properly. It is not something to wellness your way around.",
                ]
            ),
            "\n".join(
                [
                    "2. Vitamin D next",
                    markers["vitamin_d"]["plain_language"],
                    "This belongs in the Bloods follow-up plan rather than a guessed social-media dose.",
                ]
            ),
            "\n".join(
                [
                    "3. Sleep support",
                    (
                        "Low deep sleep plus suboptimal magnesium makes magnesium glycinate the cleanest "
                        "category to compare first. Think sleep routine support, not magic."
                    ),
                ]
            ),
            "\n".join(
                [
                    "4. Training basics",
                    "For Hyrox, boring wins: electrolytes when you sweat, enough protein, creatine if it fits your routine.",
                ]
            ),
            (
                "I would not add five new things at once. Healf's value is curation, not chaos. "
                "Pick the bottleneck, track how you feel, and let the data be useful without letting it become your personality."
            ),
            "Useful next question: are you mostly struggling with morning energy, session recovery, or falling asleep?",
        ]
    )


def build_bloods_demo_prompt(plan: dict[str, Any]) -> str:
    return (
        "Produce a proactive Healf-Max check-in based on the customer's latest synthetic Bloods upload, "
        "wearable context and Hyrox goal.\n\n"
        "Do not wait for a user question.\n\n"
        "Use this answer shape:\n"
        "1. Punchy interpretation\n"
        "2. What the data is saying\n"
        "3. Priority order\n"
        "4. Product/category lanes worth comparing\n"
        "5. What not to overdo\n"
        "6. Follow-up boundary\n"
        "7. One useful next question\n\n"
        "Use Healf social/editorial tone, but keep biomarker safety plain and careful.\n"
        "Do not diagnose. Do not prescribe dosing. Do not claim products treat deficiencies, fatigue, inflammation, insomnia, or disease. "
        "Do not turn abnormal blood markers into a shopping list.\n\n"
        f"Structured context:\n{json.dumps(plan, indent=2)}"
    )


def _retrieve_trace_records(query: str, *, settings: Settings) -> list[KBRecord]:
    """Return search results plus a demo-curated trace superset for explainability."""
    searched = search_kb(query, kb_dir=settings.kb_dir, storage_dir=settings.storage_dir, limit=40)
    by_id = {record.id: record for record in _load_trace_catalog(settings)}
    output: list[KBRecord] = []
    seen: set[str] = set()
    for record in searched:
        if record.id not in seen:
            seen.add(record.id)
            output.append(record)
    for record_id in TRACE_RECORD_IDS:
        record = by_id.get(record_id)
        if record and record.id not in seen:
            seen.add(record.id)
            output.append(record)
    ordered = []
    for record_id in TRACE_RECORD_IDS:
        record = next((item for item in output if item.id == record_id), None)
        if record:
            ordered.append(record)
    ordered.extend(record for record in output if record.id not in {item.id for item in ordered})
    return ordered


def _load_trace_catalog(settings: Settings) -> list[KBRecord]:
    from healf_max.kb.index import load_index_records

    indexed = load_index_records(settings.storage_dir)
    if indexed:
        return indexed
    return load_kb_records(settings.kb_dir)


__all__ = [
    "build_bloods_demo_plan",
    "build_bloods_demo_prompt",
    "get_bloods_context",
    "get_latest_bloods_context",
    "render_bloods_demo_debug",
    "render_bloods_demo_fallback",
    "render_bloods_demo_json",
    "summarise_bloods_markers",
]
