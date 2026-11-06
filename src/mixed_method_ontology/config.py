"""Settings from the environment, with an optional `.env` file in the working directory.

Values already present in the environment win over `.env`. Nothing is hard-coded: homelab addresses and keys live
in the owner's `.env` only (template: `.env.example`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def load_dotenv(path: Path) -> dict[str, str]:
    """KEY=value lines; comments, blank lines and malformed lines are skipped. Quotes around values are removed."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        key, sep, value = stripped.partition("=")
        if sep and key.strip():
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


@dataclass(frozen=True)
class Settings:
    openai_base_url: str = ""
    openai_api_key: str = ""
    ocr_model: str = ""
    openai_timeout: float = 600.0
    tesseract_cmd: str = "tesseract"
    tesseract_lang: str = "ces"

    @classmethod
    def load(cls, env_file: Path | None = None, environ: dict[str, str] | None = None) -> Settings:
        merged = load_dotenv(env_file if env_file is not None else Path.cwd() / ".env")
        merged.update(environ if environ is not None else os.environ)

        def get(key: str, default: str) -> str:
            value = merged.get(key, "")
            return value if value else default

        return cls(
            openai_base_url=get("MMO_OPENAI_BASE_URL", ""),
            openai_api_key=get("MMO_OPENAI_API_KEY", ""),
            ocr_model=get("MMO_OCR_MODEL", ""),
            openai_timeout=float(get("MMO_OPENAI_TIMEOUT", "600")),
            tesseract_cmd=get("MMO_TESSERACT_CMD", "tesseract"),
            tesseract_lang=get("MMO_TESSERACT_LANG", "ces"),
        )
