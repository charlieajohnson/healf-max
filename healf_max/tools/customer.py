from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from healf_max.config import load_settings


def get_customer_context(path: str | None = None) -> dict[str, Any]:
    settings = load_settings()
    profile_path = Path(path) if path else settings.project_root / "data" / "synthetic_customer_profile.yaml"
    return _load_yaml(profile_path)


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {"items": data}
