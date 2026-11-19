"""OCR of page images with interchangeable backends; results of each backend are kept side by side."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

from mmo.config import Settings
from mmo.core.topic import Page, Source, sha256_file
from mmo.ingest.ocr.base import OcrBackend, OcrResult
from mmo.ingest.ocr.openai_compat import OpenAICompatBackend
from mmo.ingest.ocr.tesseract import TesseractBackend

__all__ = ["BACKENDS", "OcrBackend", "OcrResult", "load_pages", "make_backend", "run_ocr", "scan_file"]

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
        from mmo.ingest.ocr.fabric import connect_backend  # needs the service's client library

        return connect_backend(settings.fabric_ocr_url, settings.fabric_ocr_token, mode=mode)
    raise ValueError(f"unknown OCR backend {name!r}; known: {', '.join(BACKENDS)}")


def scan_file(out_dir: Path, scan: int) -> Path:
    return out_dir / f"scan-{scan:04d}.json"


def ocr_page(source: Source, backend: OcrBackend, page: Page) -> dict:
    """One page through the backend, as the record `run_ocr` stores."""
    started = time.monotonic()
    result = backend.recognize(page.image)
    return {
        "source": source.id,
        "scan": page.scan,
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
    scans: set[int] | None = None,
    force: bool = False,
    log: Callable[[str], None] = print,
    workers: int = 1,
) -> list[Path]:
    """OCR every page image (or the selected scans) of a source; existing results are kept unless `force`.

    `workers` pages are read at the same time (a remote service with several slots). A failed page does not stop the
    others: the run ends with an error naming the failed pages, and a rerun reads only the pages without a result.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    todo: list[Page] = []
    for page in source.pages():
        if scans and page.scan not in scans:
            continue
        if scan_file(out_dir, page.scan).exists() and not force:
            log(f"skip scan {page.scan} (exists)")
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
                failed[page.scan] = str(err)
                log(f"scan {page.scan}: FAILED {err}")
                continue
            target = scan_file(out_dir, page.scan)
            target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            written.append(target)
            note = f", quality {record['quality']}" if record["quality"] not in (None, "full") else ""
            log(f"scan {page.scan}: {len(record['text'])} chars in {record['seconds']} s{note}")
    if failed:
        numbers = ", ".join(str(n) for n in sorted(failed))
        raise RuntimeError(f"{len(failed)} of {len(todo)} scans failed ({numbers}); run again to retry only those")
    return sorted(written)


def normalize_record(record: dict) -> dict:
    """An OCR record with `scan`; records written before ADR 0006 call it `page`."""
    if "scan" not in record and "page" in record:
        record = {("scan" if key == "page" else key): value for key, value in record.items()}
    return record


def load_pages(out_dir: Path) -> list[dict]:
    """OCR records of one variant of one source, ordered by scan."""
    if not out_dir.is_dir():
        return []
    paths = [*out_dir.glob("scan-*.json"), *out_dir.glob("page-*.json")]
    records = [normalize_record(json.loads(p.read_text(encoding="utf-8"))) for p in paths]
    return sorted(records, key=lambda r: r["scan"])
