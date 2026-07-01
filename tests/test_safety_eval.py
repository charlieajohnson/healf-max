from __future__ import annotations

import importlib
from pathlib import Path

import yaml

from healf_max.domain.safety import SafetyCategory


ROOT = Path(__file__).resolve().parents[1]
CASES_PATH = ROOT / "evals" / "safety" / "cases.yaml"
THRESHOLDS_PATH = ROOT / "evals" / "safety" / "thresholds.yaml"
SAFETY_CRITICAL = {
    "urgent_symptoms",
    "medication_interaction",
    "pregnancy_or_child",
    "diagnosis_or_prescription_request",
    "biomarker_followup",
}


def _eval_module():
    return importlib.import_module("healf_max.evals.safety")


def _run_report():
    safety_eval = _eval_module()
    cases = safety_eval.load_cases(CASES_PATH)
    thresholds = safety_eval.load_thresholds(THRESHOLDS_PATH)
    return safety_eval.run_safety_eval(cases, thresholds=thresholds)


def test_dataset_integrity() -> None:
    raw_cases = yaml.safe_load(CASES_PATH.read_text(encoding="utf-8"))
    valid_categories = set(SafetyCategory.__args__)
    ids = [case["id"] for case in raw_cases]

    assert len(raw_cases) >= 50
    assert len(ids) == len(set(ids))
    assert all(case["expected_category"] in valid_categories for case in raw_cases)
    assert sum(1 for case in raw_cases if case["expected_category"] == "wellness_ok") >= 3
    assert sum(1 for case in raw_cases if "hard_negative" in case.get("tags", [])) >= 5
    for case in raw_cases:
        if case["expected_category"] != "wellness_ok":
            assert case["expected_allow_products"] is False


def test_no_critical_false_negatives() -> None:
    report = _run_report()
    leaks = "\n".join(f"{item.case_id}: {item.message}" for item in report.critical_false_negatives)

    assert report.critical_false_negatives == [], leaks


def test_macro_f1_meets_floor() -> None:
    report = _run_report()
    thresholds = _eval_module().load_thresholds(THRESHOLDS_PATH)

    assert report.macro_f1 >= thresholds.macro_f1_min


def test_safety_critical_recall_floors() -> None:
    report = _run_report()
    thresholds = _eval_module().load_thresholds(THRESHOLDS_PATH)

    for category, floor in thresholds.per_category_recall_min.items():
        assert category in SAFETY_CRITICAL
        assert report.per_category[category].recall >= floor


def test_safety_eval_report_markdown_and_json_are_inspectable(tmp_path) -> None:
    report = _run_report()
    safety_eval = _eval_module()
    safety_eval.write_report(report, tmp_path)

    markdown = (tmp_path / "report.md").read_text(encoding="utf-8")
    json_report = (tmp_path / "report.json").read_text(encoding="utf-8")

    assert "| Category | Precision | Recall | F1 | Support |" in markdown
    assert "## Critical False Negatives" in markdown
    assert "## Confusion Matrix" in markdown
    assert "\"macro_f1\"" in json_report
