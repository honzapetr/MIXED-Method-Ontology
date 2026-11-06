"""OCR of page images with interchangeable backends; results of each backend are kept side by side."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from mixed_method_ontology.config import Settings
from mixed_method_ontology.ocr.base import OcrBackend, OcrResult
from mixed_method_ontology.ocr.openai_compat import OpenAICompatBackend
from mixed_method_ontology.ocr.tesseract import TesseractBackend
from mixed_method_ontology.topic import Source, sha256_file

__all__ = ["BACKENDS", "OcrBackend", "OcrResult", "load_pages", "make_backend", "page_file", "run_ocr"]

BACKENDS = ("tesseract", "openai")


def make_backend(name: str, settings: Settings, model: str | None = None) -> OcrBackend:
    if name == "tesseract":
        return TesseractBackend(cmd=settings.tesseract_cmd, lang=settings.tesseract_lang)
    if name == "openai":
        return OpenAICompatBackend(
            base_url=settings.openai_base_url,
            model=model or settings.ocr_model,
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout,
        )
    raise ValueError(f"unknown OCR backend {name!r}; known: {', '.join(BACKENDS)}")


def page_file(out_dir: Path, page: int) -> Path:
    return out_dir / f"page-{page:04d}.json"


def run_ocr(
    source: Source,
    backend: OcrBackend,
    out_dir: Path,
    pages: set[int] | None = None,
    force: bool = False,
    log: Callable[[str], None] = print,
) -> list[Path]:
    """OCR every page (or the selected ones) of a source; existing results are kept unless `force`."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for page in source.pages():
        if pages and page.number not in pages:
            continue
        target = page_file(out_dir, page.number)
        if target.exists() and not force:
            log(f"skip page {page.number} (exists)")
            continue
        started = time.monotonic()
        result = backend.recognize(page.image)
        record = {
            "source": source.id,
            "page": page.number,
            "image": page.image.name,
            "image_sha256": sha256_file(page.image),
            "backend": backend.name,
            "model": result.model,
            "prompt_version": result.prompt_version,
            "confidence": result.confidence,
            "seconds": round(time.monotonic() - started, 2),
            "created": datetime.now(UTC).isoformat(timespec="seconds"),
            "text": result.text,
        }
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(target)
        log(f"page {page.number}: {len(result.text)} chars in {record['seconds']} s")
    return written


def load_pages(out_dir: Path) -> list[dict]:
    """OCR records of one backend for one source, ordered by page."""
    records = [json.loads(p.read_text(encoding="utf-8")) for p in out_dir.glob("page-*.json")]
    return sorted(records, key=lambda r: r["page"])
