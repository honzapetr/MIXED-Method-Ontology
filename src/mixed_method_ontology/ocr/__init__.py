"""OCR of page images with interchangeable backends; results of each backend are kept side by side."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from mixed_method_ontology.config import Settings
from mixed_method_ontology.ocr.base import OcrBackend, OcrResult
from mixed_method_ontology.ocr.openai_compat import OpenAICompatBackend
from mixed_method_ontology.ocr.tesseract import TesseractBackend
from mixed_method_ontology.topic import Page, Source, sha256_file

__all__ = ["BACKENDS", "OcrBackend", "OcrResult", "load_pages", "make_backend", "page_file", "run_ocr"]

BACKENDS = ("tesseract", "openai", "fabric")


def make_backend(name: str, settings: Settings, model: str | None = None, mode: str = "auto") -> OcrBackend:
    """`model` chooses the openai backend's model, `mode` the fabric service's route (auto / accurate / fast)."""
    if name == "tesseract":
        return TesseractBackend(cmd=settings.tesseract_cmd, lang=settings.tesseract_lang)
    if name == "openai":
        return OpenAICompatBackend(
            base_url=settings.openai_base_url,
            model=model or settings.ocr_model,
            api_key=settings.openai_api_key,
            timeout=settings.openai_timeout,
        )
    if name == "fabric":
        from mixed_method_ontology.ocr.fabric import connect_backend  # needs the service's client library

        return connect_backend(settings.fabric_ocr_url, settings.fabric_ocr_token, mode=mode)
    raise ValueError(f"unknown OCR backend {name!r}; known: {', '.join(BACKENDS)}")


def page_file(out_dir: Path, page: int) -> Path:
    return out_dir / f"page-{page:04d}.json"


def ocr_page(source: Source, backend: OcrBackend, page: Page) -> dict:
    """One page through the backend, as the record `run_ocr` stores."""
    started = time.monotonic()
    result = backend.recognize(page.image)
    return {
        "source": source.id,
        "page": page.number,
        "image": page.image.name,
        "image_sha256": sha256_file(page.image),
        "backend": backend.name,
        "model": result.model,
        "prompt_version": result.prompt_version,
        "confidence": result.confidence,
        "quality": result.quality,
        "warnings": result.warnings,
        "seconds": round(time.monotonic() - started, 2),
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "text": result.text,
    }


def run_ocr(
    source: Source,
    backend: OcrBackend,
    out_dir: Path,
    pages: set[int] | None = None,
    force: bool = False,
    log: Callable[[str], None] = print,
    workers: int = 1,
) -> list[Path]:
    """OCR every page (or the selected ones) of a source; existing results are kept unless `force`.

    `workers` pages are read at the same time (a remote service with several slots). A failed page does not stop the
    others: the run ends with an error naming the failed pages, and a rerun reads only the pages without a result.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    todo: list[Page] = []
    for page in source.pages():
        if pages and page.number not in pages:
            continue
        if page_file(out_dir, page.number).exists() and not force:
            log(f"skip page {page.number} (exists)")
            continue
        todo.append(page)
    written: list[Path] = []
    failed: dict[int, str] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(ocr_page, source, backend, page): page for page in todo}
        for future in as_completed(futures):
            page = futures[future]
            try:
                record = future.result()
            except Exception as err:  # one bad page must not lose the others; reported below
                failed[page.number] = str(err)
                log(f"page {page.number}: FAILED {err}")
                continue
            target = page_file(out_dir, page.number)
            target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            written.append(target)
            note = f", quality {record['quality']}" if record["quality"] not in (None, "full") else ""
            log(f"page {page.number}: {len(record['text'])} chars in {record['seconds']} s{note}")
    if failed:
        numbers = ", ".join(str(n) for n in sorted(failed))
        raise RuntimeError(f"{len(failed)} of {len(todo)} pages failed ({numbers}); run again to retry only those")
    return sorted(written)


def load_pages(out_dir: Path) -> list[dict]:
    """OCR records of one backend for one source, ordered by page."""
    records = [json.loads(p.read_text(encoding="utf-8")) for p in out_dir.glob("page-*.json")]
    return sorted(records, key=lambda r: r["page"])
