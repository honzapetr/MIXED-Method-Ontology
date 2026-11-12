"""The contract every OCR backend implements."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class OcrResult:
    text: str
    model: str
    prompt_version: str | None = None
    confidence: float | None = None  # 0-100 when the backend reports it
    quality: str | None = None  # the backend's own verdict when it has one (fabric: full / basic / suspect)
    warnings: list[str] = field(default_factory=list)


class OcrBackend(Protocol):
    name: str

    def recognize(self, image: Path) -> OcrResult: ...
