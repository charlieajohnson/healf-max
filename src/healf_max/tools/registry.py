from __future__ import annotations

import json
from typing import Any, Callable

from healf_max.config import Settings
from healf_max.domain.models import TurnPlan
from healf_max.domain.safety import SafetyCheck
from healf_max.kb.search import search_kb
from healf_max.tools.bloods import get_bloods_context, get_wearable_context
from healf_max.tools.customer import get_customer_context
from healf_max.tools.products import search_products

ToolFn = Callable[..., Any]


TOOL_REGISTRY: dict[str, ToolFn] = {
    "get_customer_context": get_customer_context,
    "search_knowledge": lambda query, limit=6: _search_knowledge(query, limit=limit),
    "search_products": search_products,
    "get_bloods_context": get_bloods_context,
    "get_wearable_context": get_wearable_context,
}

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "name": "get_customer_context",
        "description": "Load the synthetic customer profile for the current demo customer.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_knowledge",
        "description": "Search the local markdown knowledge base across moments, evidence, biomarkers, editorial, tone and trust records.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search phrase."},
                "limit": {"type": "integer", "description": "Maximum records to return."},
            },
            "required": ["query", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "search_products",
        "description": "Search local product and category records. Prefer category fit over product certainty.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search phrase."},
                "limit": {"type": "integer", "description": "Maximum records to return."},
            },
            "required": ["query", "limit"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_bloods_context",
        "description": "Load the synthetic latest bloods panel for the demo customer.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_wearable_context",
        "description": "Load Oura-like synthetic wearable context for the demo customer.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def execute_tool_call(name: str, arguments: dict[str, Any]) -> Any:
    if name == "get_customer_context":
        return get_customer_context()
    if name == "search_knowledge":
        return _search_knowledge(str(arguments["query"]), limit=int(arguments["limit"]))
    if name == "search_products":
        return search_products(str(arguments["query"]), limit=int(arguments["limit"]))
    if name == "get_bloods_context":
        return get_bloods_context()
    if name == "get_wearable_context":
        return get_wearable_context()
    raise ValueError(f"Unknown tool: {name}")


def build_context_bundle(
    user_message: str,
    *,
    safety: SafetyCheck,
    plan: TurnPlan,
    settings: Settings,
    debug: bool,
    include_bloods: bool = False,
) -> str:
    knowledge = search_kb(
        user_message,
        kb_dir=settings.kb_dir,
        storage_dir=settings.storage_dir,
        limit=8,
    )
    products = search_kb(
        user_message,
        kb_dir=settings.kb_dir,
        storage_dir=settings.storage_dir,
        limit=4,
        kinds={"products"},
    )
    bundle = {
        "safety_classification": safety.model_dump(),
        "turn_plan": plan.model_dump(),
        "customer_context": get_customer_context(),
        "retrieved_moments": [record.model_dump() for record in knowledge if record.kind == "moments"],
        "retrieved_biomarkers": [record.model_dump() for record in knowledge if record.kind == "biomarkers"],
        "retrieved_evidence": [record.model_dump() for record in knowledge if record.kind == "evidence"],
        "retrieved_products": [record.model_dump() for record in products],
        "retrieved_editorial_trust_tone": [
            record.model_dump()
            for record in knowledge
            if record.kind in {"editorial", "trust", "tone"}
        ],
    }
    if include_bloods or "blood" in user_message.lower() or "ferritin" in user_message.lower():
        bundle["bloods_context"] = get_bloods_context()
        bundle["wearable_context"] = get_wearable_context()
    if not debug:
        return json.dumps(bundle, indent=2)
    return _format_debug_bundle(bundle)


def _search_knowledge(query: str, *, limit: int = 6) -> list[dict[str, object]]:
    from healf_max.tools.knowledge import search_knowledge

    return search_knowledge(query, limit=limit)


def _format_debug_bundle(bundle: dict[str, Any]) -> str:
    lines: list[str] = []
    safety = bundle["safety_classification"]
    plan = bundle["turn_plan"]
    lines.append(f"- safety classification: {safety['category']} ({safety['rationale']})")
    lines.append(f"- turn plan: {', '.join(plan['user_intent'])}; shape={plan['answer_shape']}")
    for label, key in [
        ("retrieved moments", "retrieved_moments"),
        ("retrieved biomarkers", "retrieved_biomarkers"),
        ("retrieved evidence", "retrieved_evidence"),
        ("retrieved products", "retrieved_products"),
        ("retrieved editorial/trust/tone signals", "retrieved_editorial_trust_tone"),
    ]:
        records = bundle.get(key, [])
        if records:
            lines.append(f"- {label}: " + ", ".join(str(record["id"]) for record in records))
        else:
            lines.append(f"- {label}: none")
    if "bloods_context" in bundle:
        lines.append("- bloods context: synthetic demo profile loaded")
    if "wearable_context" in bundle:
        lines.append("- wearable context: synthetic Oura-like context loaded")
    return "\n".join(lines)
