from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openai_api_key: str | None
    model: str
    embedding_model: str
    kb_dir: Path
    storage_dir: Path
    stream: bool
    project_root: Path


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_settings() -> Settings:
    project_root = get_project_root()
    if os.getenv("HEALF_MAX_DISABLE_DOTENV") != "1":
        env_file = Path(os.getenv("HEALF_MAX_ENV_FILE", project_root / ".env"))
        load_dotenv(env_file, override=False)

    kb_dir = Path(os.getenv("HEALF_MAX_KB_DIR", "kb"))
    storage_dir = Path(os.getenv("HEALF_MAX_STORAGE_DIR", ".storage"))
    if not kb_dir.is_absolute():
        kb_dir = project_root / kb_dir
    if not storage_dir.is_absolute():
        storage_dir = project_root / storage_dir

    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        model=os.getenv("HEALF_MAX_MODEL", "gpt-4.1-mini"),
        embedding_model=os.getenv("HEALF_MAX_EMBEDDING_MODEL", "text-embedding-3-small"),
        kb_dir=kb_dir,
        storage_dir=storage_dir,
        stream=os.getenv("HEALF_MAX_STREAM", "true").lower() in {"1", "true", "yes", "on"},
        project_root=project_root,
    )
