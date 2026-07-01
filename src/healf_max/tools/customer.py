from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from healf_max.config import load_settings


def get_customer_context() -> dict[str, Any]:
    settings = load_settings()
    return _load_yaml(settings.project_root / "data" / "synthetic_customer_profile.yaml")


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {"items": data}
