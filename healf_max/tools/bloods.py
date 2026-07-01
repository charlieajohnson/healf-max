from __future__ import annotations

from pathlib import Path
from typing import Any

from healf_max.config import load_settings
from healf_max.demo.wearable import get_wearable_context
from healf_max.tools.customer import _load_yaml

REQUIRED_MARKER_FIELDS = ("marker", "value", "status", "plain_language", "action_mode")
FOLLOW_UP_ACTIONS = {
    "clinician_follow_up",
    "practitioner_review",
    "practitioner_review_if_symptomatic",
    "contextual_follow_up",
}


def get_latest_bloods_context(profile_path: str | None = None) -> dict[str, Any]:
    """Load and validate the synthetic latest Bloods upload."""
    settings = load_settings()
    path = Path(profile_path) if profile_path else settings.project_root / "data" / "synthetic_bloods_results.yaml"
    bloods = _load_yaml(path)
    _validate_bloods_panel(bloods, source=path)
    return bloods


def get_bloods_context() -> dict[str, Any]:
    """Compatibility wrapper for the tool registry."""
    return get_latest_bloods_context()


def summarise_bloods_markers(bloods: dict[str, Any]) -> dict[str, Any]:
    """Return marker statuses, action modes and safety boundaries."""
    _validate_bloods_panel(bloods, source=None)
    markers = list(bloods["markers"])
    boundaries = _dedupe(
        boundary
        for marker in markers
        for boundary in _as_list(marker.get("safety_boundary"))
    )
    followup = [
        marker
        for marker in markers
        if marker.get("action_mode") in FOLLOW_UP_ACTIONS
        or marker.get("status") in {"low", "high"}
        or "abnormal_bloods_need_follow_up" in _as_list(marker.get("safety_boundary"))
    ]
    return {
        "panel_id": bloods.get("panel_id"),
        "customer_id": bloods.get("customer_id"),
        "safety_mode": "biomarker_followup" if followup else "wellness_ok",
        "markers": [
            {
                "marker": marker["marker"],
                "status": marker["status"],
                "action_mode": marker["action_mode"],
                "safety_boundary": _as_list(marker.get("safety_boundary")),
            }
            for marker in markers
        ],
        "markers_needing_followup": followup,
        "safety_boundaries": boundaries,
    }


def _validate_bloods_panel(bloods: dict[str, Any], *, source: Path | None) -> None:
    markers = bloods.get("markers")
    if not isinstance(markers, list) or not markers:
        location = f" in {source}" if source else ""
        raise ValueError(f"Bloods panel{location} must include a non-empty markers list")
    for index, marker in enumerate(markers):
        if not isinstance(marker, dict):
            raise ValueError(f"Bloods marker {index} must be a mapping")
        missing = [field for field in REQUIRED_MARKER_FIELDS if field not in marker]
        if missing:
            name = marker.get("marker", index)
            raise ValueError(f"Bloods marker {name!r} missing required field(s): {', '.join(missing)}")


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def _dedupe(values: Any) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        item = str(value)
        if item not in seen:
            seen.add(item)
            output.append(item)
    return output
