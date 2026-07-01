from __future__ import annotations


def confusion_matrix(pairs: list[tuple[str, str]]) -> dict[str, dict[str, int]]:
    labels = sorted({label for pair in pairs for label in pair})
    matrix = {true: {predicted: 0 for predicted in labels} for true in labels}
    for true, predicted in pairs:
        matrix.setdefault(true, {label: 0 for label in labels})
        matrix[true].setdefault(predicted, 0)
        matrix[true][predicted] += 1
    return matrix


def precision_recall_f1(cm: dict[str, dict[str, int]], label: str) -> tuple[float, float, float]:
    true_positive = cm.get(label, {}).get(label, 0)
    false_positive = sum(row.get(label, 0) for true, row in cm.items() if true != label)
    false_negative = sum(count for predicted, count in cm.get(label, {}).items() if predicted != label)
    precision = _divide(true_positive, true_positive + false_positive)
    recall = _divide(true_positive, true_positive + false_negative)
    f1 = _divide(2 * precision * recall, precision + recall)
    return precision, recall, f1


def macro_f1(cm: dict[str, dict[str, int]], labels: list[str]) -> float:
    if not labels:
        return 0.0
    return sum(precision_recall_f1(cm, label)[2] for label in labels) / len(labels)


def _divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
