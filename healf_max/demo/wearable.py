from __future__ import annotations

from pathlib import Path
from typing import Any

from healf_max.config import load_settings
from healf_max.tools.customer import _load_yaml


def get_wearable_context(path: str | None = None) -> dict[str, Any]:
    """Load synthetic Oura-like wearable context."""
    settings = load_settings()
    wearable_path = Path(path) if path else settings.project_root / "data" / "wearable_context.yaml"
    data = _load_yaml(wearable_path)
    signals = data.get("signals")
    if not isinstance(signals, list) or not signals:
        raise ValueError("Wearable context must include a non-empty signals list")
    for index, signal in enumerate(signals):
        if not isinstance(signal, dict):
            raise ValueError(f"Wearable signal {index} must be a mapping")
        missing = [field for field in ("signal", "value", "status", "plain_language") if field not in signal]
        if missing:
            name = signal.get("signal", index)
            raise ValueError(f"Wearable signal {name!r} missing required field(s): {', '.join(missing)}")
    return data
