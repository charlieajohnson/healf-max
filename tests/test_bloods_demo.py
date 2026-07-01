import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from healf_max.cli import app
from healf_max.domain import planner, recommendations
from healf_max.kb.search import search_kb
from healf_max.tools import bloods as bloods_tools
from healf_max.tools.customer import get_customer_context


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
KB_DIR = ROOT / "kb"
BANNED_CLAIMS = (
    "fixes fatigue",
    "treats anaemia",
    "cures insomnia",
    "guaranteed",
    "clinically proven stack",
    "take 1000 mg",
    "take 10 mg",
)


def test_synthetic_bloods_yaml_loads_and_validates_markers(monkeypatch) -> None:
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")

    assert hasattr(bloods_tools, "get_latest_bloods_context")
    bloods = bloods_tools.get_latest_bloods_context()
    summary = bloods_tools.summarise_bloods_markers(bloods)

    assert bloods["panel_id"] == "healf_bloods_demo_001"
    assert summary["safety_mode"] == "biomarker_followup"
    assert {item["marker"] for item in summary["markers_needing_followup"]} >= {"ferritin", "vitamin_d"}
    for marker in bloods["markers"]:
        assert {"marker", "value", "status", "plain_language", "action_mode"}.issubset(marker)


def test_bloods_marker_validation_rejects_malformed_markers(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")
    malformed = tmp_path / "bad_bloods.yaml"
    malformed.write_text(
        yaml.safe_dump(
            {
                "panel_id": "bad",
                "customer_id": "demo_customer_hyrox_29f",
                "markers": [{"marker": "ferritin", "value": 18, "status": "low"}],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="plain_language"):
        bloods_tools.get_latest_bloods_context(str(malformed))


def test_planner_infers_recovery_bottleneck_and_safety(monkeypatch) -> None:
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")
    customer = get_customer_context()
    bloods = bloods_tools.get_latest_bloods_context()
    wearable = bloods_tools.get_wearable_context()

    assert hasattr(planner, "infer_wellbeing_moment")
    moment = planner.infer_wellbeing_moment(customer, bloods, wearable)

    assert moment.id == "recovery_bottleneck_with_bloods"
    assert moment.primary_interpretation == "recovery_bottleneck"
    assert "biomarker_followup" in moment.safety_boundaries
    assert moment.priority_order[:4] == [
        "ferritin_follow_up",
        "vitamin_d_practitioner_guided",
        "sleep_support",
        "training_basics",
    ]


def test_recommendation_lanes_prioritise_followup_before_products(monkeypatch) -> None:
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")
    customer = get_customer_context()
    bloods = bloods_tools.get_latest_bloods_context()
    wearable = bloods_tools.get_wearable_context()
    assert hasattr(planner, "infer_wellbeing_moment")
    assert hasattr(recommendations, "build_recommendation_lanes")
    moment = planner.infer_wellbeing_moment(customer, bloods, wearable)
    retrieved = search_kb(moment.retrieval_query, kb_dir=KB_DIR, storage_dir=ROOT / ".storage", limit=24)

    lanes = recommendations.build_recommendation_lanes(moment, retrieved)
    lane_by_id = {lane.id: lane for lane in lanes}

    assert lanes[0].id == "ferritin_follow_up"
    assert lane_by_id["ferritin_follow_up"].mode == "follow_up_not_product"
    assert "not something to wellness your way around" in lane_by_id["ferritin_follow_up"].reason
    assert lane_by_id["magnesium_glycinate"].mode == "category_comparison"
    assert "omega_3" in lane_by_id
    assert "anti-inflammatory treatment" in lane_by_id["omega_3"].do_not_claim


def test_json_mode_returns_machine_readable_plan(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")

    result = CliRunner().invoke(app, ["bloods-demo", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["customer_id"] == "demo_customer_hyrox_29f"
    assert payload["panel_id"] == "healf_bloods_demo_001"
    assert payload["safety_mode"] == "biomarker_followup"
    assert payload["wellbeing_moment"] == "recovery_bottleneck_with_bloods"
    assert payload["priority_order"][:4] == [
        "ferritin_follow_up",
        "vitamin_d_practitioner_guided",
        "sleep_support",
        "training_basics",
    ]
    assert payload["recommendation_lanes"][0]["mode"] == "follow_up_not_product"
    assert "hyrox_recovery_bottleneck_with_bloods" in payload["retrieved_record_ids"]


def test_debug_mode_includes_mapping_and_retrieved_records(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")

    result = CliRunner().invoke(app, ["bloods-demo", "--debug"])

    assert result.exit_code == 0
    assert "Loaded customer: demo_customer_hyrox_29f" in result.output
    assert "Loaded Bloods panel: healf_bloods_demo_001" in result.output
    assert "Loaded wearable context: synthetic_oura_context" in result.output
    assert "Safety mode: biomarker_followup" in result.output
    assert "Inferred moment: recovery_bottleneck_with_bloods" in result.output
    assert "moments/hyrox_recovery_bottleneck_with_bloods.md" in result.output
    assert "products/magnesium_glycinate.md" in result.output
    assert "tone/group_chat_signal.md" in result.output


def test_profile_option_loads_custom_bloods_path(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")

    result = CliRunner().invoke(
        app,
        ["bloods-demo", "--json", "--profile", str(DATA_DIR / "synthetic_bloods_results.yaml")],
    )

    assert result.exit_code == 0
    assert json.loads(result.output)["panel_id"] == "healf_bloods_demo_001"


def test_fallback_output_mentions_bloods_wearable_hyrox_without_banned_claims(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")

    result = CliRunner().invoke(app, ["bloods-demo"])

    assert result.exit_code == 0
    output = result.output.lower()
    assert "hyrox" in output
    assert "deep sleep" in output
    assert "hrv" in output
    assert "low ferritin" in output
    assert "low vitamin d" in output
    assert "not something to wellness your way around" in output
    assert "magnesium glycinate" in output
    assert "electrolytes" in output
    assert "creatine" in output
    for claim in BANNED_CLAIMS:
        assert claim not in output


def test_expected_plan_fixture_matches_inferred_plan(monkeypatch) -> None:
    monkeypatch.setenv("HEALF_MAX_DISABLE_DOTENV", "1")
    expected = yaml.safe_load((DATA_DIR / "bloods_demo_expected_plan.yaml").read_text(encoding="utf-8"))
    assert hasattr(planner, "infer_wellbeing_moment")
    moment = planner.infer_wellbeing_moment(
        get_customer_context(),
        bloods_tools.get_latest_bloods_context(),
        bloods_tools.get_wearable_context(),
    )

    assert expected["wellbeing_moment"]["id"] == moment.id
    assert expected["wellbeing_moment"]["priority_order"] == moment.priority_order
