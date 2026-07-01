from __future__ import annotations

import json
from pathlib import Path
from typing import Any, get_args

import yaml
from pydantic import BaseModel, Field, field_validator

from healf_max.domain.safety import SafetyCategory, classify_safety
from healf_max.evals.metrics import confusion_matrix, macro_f1, precision_recall_f1

SAFETY_CATEGORIES = tuple(get_args(SafetyCategory))
SAFETY_CRITICAL_CATEGORIES = {
    "urgent_symptoms",
    "medication_interaction",
    "pregnancy_or_child",
    "diagnosis_or_prescription_request",
    "biomarker_followup",
}


class SafetyCase(BaseModel):
    id: str
    message: str
    expected_category: SafetyCategory
    expected_allow_products: bool
    tags: list[str] = Field(default_factory=list)
    note: str = ""


class SafetyThresholds(BaseModel):
    critical_false_negatives_max: int = 0
    macro_f1_min: float = 0.0
    per_category_recall_min: dict[str, float] = Field(default_factory=dict)

    @field_validator("per_category_recall_min")
    @classmethod
    def validate_categories(cls, value: dict[str, float]) -> dict[str, float]:
        unknown = sorted(set(value) - set(SAFETY_CATEGORIES))
        if unknown:
            raise ValueError(f"Unknown safety categories: {', '.join(unknown)}")
        return value


class SafetyCaseResult(BaseModel):
    case_id: str
    message: str
    expected_category: str
    predicted_category: str
    expected_allow_products: bool
    actual_allow_products: bool
    tags: list[str] = Field(default_factory=list)
    note: str = ""


class CategoryMetrics(BaseModel):
    precision: float
    recall: float
    f1: float
    support: int


class SafetyEvalReport(BaseModel):
    total: int
    per_category: dict[str, CategoryMetrics]
    confusion_matrix: dict[str, dict[str, int]]
    critical_false_negatives: list[SafetyCaseResult]
    over_blocks: list[SafetyCaseResult]
    macro_f1: float
    passed: bool
    thresholds: SafetyThresholds

    def to_markdown(self) -> str:
        lines = [
            "# Safety Eval Report",
            "",
            f"- Total cases: {self.total}",
            f"- Passed: {str(self.passed).lower()}",
            f"- Macro F1: {self.macro_f1:.3f}",
            f"- Critical false negatives: {len(self.critical_false_negatives)}",
            f"- Over-blocks: {len(self.over_blocks)}",
            "",
            "## Critical False Negatives",
            "",
        ]
        if self.critical_false_negatives:
            for item in self.critical_false_negatives:
                lines.append(f"- `{item.case_id}` expected `{item.expected_category}` but predicted `{item.predicted_category}`: {item.message}")
        else:
            lines.append("None.")
        lines.extend(
            [
                "",
                "## Per-Category Metrics",
                "",
                "| Category | Precision | Recall | F1 | Support |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for category, metrics in sorted(self.per_category.items()):
            lines.append(
                f"| {category} | {metrics.precision:.3f} | {metrics.recall:.3f} | {metrics.f1:.3f} | {metrics.support} |"
            )
        labels = sorted(self.per_category)
        lines.extend(["", "## Confusion Matrix", "", "| True \\ Predicted | " + " | ".join(labels) + " |"])
        lines.append("|---" + "|---:" * len(labels) + "|")
        for true in labels:
            row = [str(self.confusion_matrix.get(true, {}).get(predicted, 0)) for predicted in labels]
            lines.append(f"| {true} | " + " | ".join(row) + " |")
        lines.extend(["", "## Over-Blocks", ""])
        if self.over_blocks:
            for item in self.over_blocks:
                lines.append(f"- `{item.case_id}` predicted `{item.predicted_category}`: {item.message}")
        else:
            lines.append("None.")
        return "\n".join(lines) + "\n"


def load_cases(path: str | Path) -> list[SafetyCase]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    if not isinstance(data, list):
        raise ValueError("Safety cases file must contain a list")
    return [SafetyCase.model_validate(item) for item in data]


def load_thresholds(path: str | Path) -> SafetyThresholds:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    return SafetyThresholds.model_validate(data)


def run_safety_eval(cases: list[SafetyCase], *, thresholds: SafetyThresholds) -> SafetyEvalReport:
    results: list[SafetyCaseResult] = []
    pairs: list[tuple[str, str]] = []
    critical_false_negatives: list[SafetyCaseResult] = []
    over_blocks: list[SafetyCaseResult] = []

    for case in cases:
        actual = classify_safety(case.message)
        result = SafetyCaseResult(
            case_id=case.id,
            message=case.message,
            expected_category=case.expected_category,
            predicted_category=actual.category,
            expected_allow_products=case.expected_allow_products,
            actual_allow_products=actual.allow_product_recommendations,
            tags=case.tags,
            note=case.note,
        )
        results.append(result)
        pairs.append((case.expected_category, actual.category))
        if case.expected_allow_products is False and actual.allow_product_recommendations is True:
            critical_false_negatives.append(result)
        if case.expected_allow_products is True and actual.allow_product_recommendations is False:
            over_blocks.append(result)

    cm = confusion_matrix(pairs)
    labels = sorted(set(SAFETY_CATEGORIES).intersection({case.expected_category for case in cases} | {result.predicted_category for result in results}))
    per_category: dict[str, CategoryMetrics] = {}
    for label in labels:
        precision, recall, f1 = precision_recall_f1(cm, label)
        support = sum(1 for case in cases if case.expected_category == label)
        per_category[label] = CategoryMetrics(precision=precision, recall=recall, f1=f1, support=support)
    macro = macro_f1(cm, labels)
    recall_floor_passed = all(
        per_category.get(category, CategoryMetrics(precision=0.0, recall=0.0, f1=0.0, support=0)).recall >= floor
        for category, floor in thresholds.per_category_recall_min.items()
    )
    passed = (
        len(critical_false_negatives) <= thresholds.critical_false_negatives_max
        and macro >= thresholds.macro_f1_min
        and recall_floor_passed
    )
    return SafetyEvalReport(
        total=len(cases),
        per_category=per_category,
        confusion_matrix=cm,
        critical_false_negatives=critical_false_negatives,
        over_blocks=over_blocks,
        macro_f1=macro,
        passed=passed,
        thresholds=thresholds,
    )


def write_report(report: SafetyEvalReport, report_dir: str | Path) -> None:
    destination = Path(report_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "report.json").write_text(
        json.dumps(report.model_dump(), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "report.md").write_text(report.to_markdown(), encoding="utf-8")


def default_paths(project_root: Path) -> tuple[Path, Path]:
    base = project_root / "evals" / "safety"
    return base / "cases.yaml", base / "thresholds.yaml"
