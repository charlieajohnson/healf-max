from __future__ import annotations

from collections.abc import Iterator
import json
from typing import Any

from openai import OpenAI

from healf_max.config import Settings, load_settings
from healf_max.domain.planner import build_turn_plan
from healf_max.domain.safety import SafetyCheck, classify_safety
from healf_max.prompts import SYSTEM_PROMPT, build_user_prompt
from healf_max.streaming import chunk_text
from healf_max.tools.registry import TOOL_SCHEMAS, build_context_bundle, execute_tool_call


def complete_turn(user_message: str, *, debug: bool = False) -> str:
    settings = load_settings()
    safety = classify_safety(user_message)
    plan = build_turn_plan(user_message, safety)

    if not settings.openai_api_key:
        context = build_context_bundle(user_message, safety=safety, plan=plan, settings=settings, debug=debug)
        return offline_turn(user_message, safety=safety, context=context, debug=debug)

    client = OpenAI(api_key=settings.openai_api_key)
    response = _complete_with_tools(
        client,
        settings=settings,
        user_message=user_message,
        safety=safety,
        plan=plan,
        debug=debug,
    )
    return _response_text(response)


def stream_turn(user_message: str, *, debug: bool = False) -> Iterator[str]:
    settings = load_settings()
    if not settings.openai_api_key:
        yield from chunk_text(complete_turn(user_message, debug=debug))
        return

    safety = classify_safety(user_message)
    plan = build_turn_plan(user_message, safety)
    client = OpenAI(api_key=settings.openai_api_key)

    try:
        if not settings.stream:
            yield from chunk_text(
                _response_text(
                    _complete_with_tools(
                        client,
                        settings=settings,
                        user_message=user_message,
                        safety=safety,
                        plan=plan,
                        debug=debug,
                    )
                )
            )
            return
        input_list, first_response = _run_tool_selection(
            client,
            settings=settings,
            user_message=user_message,
            safety=safety,
            plan=plan,
            debug=debug,
        )
        if first_response is not None:
            yield from chunk_text(_response_text(first_response))
            return
        stream = client.responses.create(
            model=settings.model,
            instructions=SYSTEM_PROMPT,
            input=input_list,
            stream=True,
        )
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
    except Exception as exc:  # pragma: no cover - network/provider failure depends on local account state.
        context = build_context_bundle(user_message, safety=safety, plan=plan, settings=settings, debug=debug)
        yield from chunk_text(
            offline_turn(
                user_message,
                safety=safety,
                context=context,
                debug=debug,
                prefix=f"Live model call failed ({exc.__class__.__name__}). ",
            )
        )


def offline_turn(
    user_message: str,
    *,
    safety: SafetyCheck,
    context: str,
    debug: bool,
    prefix: str = "OpenAI API key not configured. ",
) -> str:
    text = user_message.lower()
    if safety.category == "urgent_symptoms":
        answer = (
            "This is not something to wellness your way around. Chest pain, breathlessness, fainting or severe symptoms need urgent medical help. "
            "Skip product decisions for now and get assessed."
        )
    elif safety.category in {
        "biomarker_followup",
        "medication_interaction",
        "pregnancy_or_child",
        "diagnosis_or_prescription_request",
    }:
        if _looks_like_plant_based_endurance_biomarker_context(text):
            answer = (
                "Start with the boundary, not the basket. For a plant-based Hyrox or endurance block with tiredness, low deep sleep, low ferritin and borderline B12, "
                "the first read is ferritin and B12 plus recovery pressure, not a missing stimulant. This is not a bigger-stack moment. "
                "Get the flagged markers reviewed, especially before iron. Keep the useful lanes narrow: bloods or practitioner follow-up, B12 context because of the diet, "
                "protein and electrolytes for training consistency, and magnesium only as a modest sleep-support lane if it fits your context."
            )
        else:
            answer = (
                "Start with the boundary, not the basket. This needs practitioner or pharmacist review before supplement choices. "
                "The useful next move is to clarify the flagged marker, medication context, pregnancy or diagnosis question, then decide what belongs in a routine."
            )
    elif "hyrox" in text or "deep sleep" in text or "tired" in text or "energy" in text:
        answer = (
            "Your body is sending a pretty clear group chat: training load, low deep sleep and tired most days. "
            "This is not a bigger-stack moment. It is a stop leaking recovery moment. Start with the bottleneck: training load, sleep pressure, enough protein, hydration, and any flagged blood markers. "
            "If ferritin or B12 is low, route that to follow-up before treating it like a supplement shopping list. If bloods are fine, look at boring wins: electrolytes around hard sessions, protein consistency, and a simple sleep-support lane such as magnesium if it fits you."
        )
    else:
        answer = (
            "First read: make one clear wellbeing decision before adding products. Pick the current bottleneck, check whether any biomarker or medication boundary changes the advice, then choose a category only if it supports the routine."
        )

    if debug:
        answer += "\n\nDebug context\n" + context
    return prefix + answer


def _looks_like_plant_based_endurance_biomarker_context(text: str) -> bool:
    diet = "plant based" in text or "plant-based" in text or "vegan" in text or "vegetarian" in text
    training = "hyrox" in text or "endurance" in text or "race" in text
    markers = "ferritin" in text and ("b12" in text or "b 12" in text)
    return diet and training and markers


def _complete_with_tools(
    client: OpenAI,
    *,
    settings: Settings,
    user_message: str,
    safety: SafetyCheck,
    plan: Any,
    debug: bool,
) -> Any:
    input_list, first_response = _run_tool_selection(
        client,
        settings=settings,
        user_message=user_message,
        safety=safety,
        plan=plan,
        debug=debug,
    )
    if first_response is not None:
        return first_response
    return client.responses.create(
        model=settings.model,
        instructions=SYSTEM_PROMPT,
        input=input_list,
    )


def _run_tool_selection(
    client: OpenAI,
    *,
    settings: Settings,
    user_message: str,
    safety: SafetyCheck,
    plan: Any,
    debug: bool,
    max_rounds: int = 3,
) -> tuple[list[Any], Any | None]:
    input_list: list[Any] = [
        {
            "role": "user",
            "content": _live_user_prompt(user_message, safety=safety, plan=plan, debug=debug),
        }
    ]
    for _ in range(max_rounds):
        response = client.responses.create(
            model=settings.model,
            instructions=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            input=input_list,
        )
        function_calls = [item for item in response.output if item.type == "function_call"]
        if not function_calls:
            return input_list, response
        input_list += response.output
        for item in function_calls:
            arguments = json.loads(item.arguments or "{}")
            result = execute_tool_call(item.name, arguments)
            input_list.append(
                {
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )
    input_list.append(
        {
            "role": "user",
            "content": "Use the tool results already provided. Do not call another tool. Give the final answer now.",
        }
    )
    return input_list, None


def _live_user_prompt(user_message: str, *, safety: SafetyCheck, plan: Any, debug: bool) -> str:
    context = {
        "customer_message": user_message,
        "deterministic_safety": safety.model_dump(),
        "deterministic_turn_plan": plan.model_dump(),
        "tool_guidance": (
            "Use tools only when external customer, bloods, wearable, knowledge or product context materially improves the answer. "
            "For generic low-risk questions, answer directly inside the safety boundaries."
        ),
        "debug": debug,
    }
    return build_user_prompt(user_message, json.dumps(context, indent=2), debug=debug)


def _response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return str(output_text)

    parts: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            text = getattr(content, "text", None)
            if text:
                parts.append(str(text))
    return "\n".join(parts).strip()
