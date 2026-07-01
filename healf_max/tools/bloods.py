from __future__ import annotations

from typing import Any

from healf_max.config import load_settings
from healf_max.tools.customer import _load_yaml


def get_bloods_context() -> dict[str, Any]:
    settings = load_settings()
    return _load_yaml(settings.project_root / "data" / "synthetic_bloods_results.yaml")


def get_wearable_context() -> dict[str, Any]:
    settings = load_settings()
    return _load_yaml(settings.project_root / "data" / "wearable_context.yaml")
