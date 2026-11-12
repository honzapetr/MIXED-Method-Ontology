"""The whole ingest of one source in one call (`mmo ingest`): files, OCR, page numbers, reading order, text, segments.

Every step is resumable - OCR and page numbers read only what is missing, the rest is cheap to redo - so an
interrupted run is simply started again. Text files (`.txt`, `.md`) are taken as they are, as the variant `original`.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from mmo.core.topic import Source, sha256_file
from mmo.ingest.ocr import OcrBackend, load_pages, run_ocr, scan_file
from mmo.ingest.order import (
    HOW_TEXT,
    PlacedPage,
    ReadingOrder,
    book_markdown,
    ordered_records,
    reading_order,
    write_order,
)
from mmo.ingest.page_numbers import PageNumberReader, load_page_numbers, read_page_numbers
from mmo.ingest.segment import segment_records, write_jsonl

TEXT_VARIANT = "original"


@dataclass
class IngestReport:
    source: str
    variants: list[str] = field(default_factory=list)
    segments: dict[str, int] = field(default_factory=dict)
    review: list[str] = field(default_factory=list)  # what the researcher should look at


def load_variant(source: Source, variant: str) -> list[dict]:
    records = load_pages(source.ocr_dir(variant))
    if not records:
        raise FileNotFoundError(f"no OCR results for variant {variant!r} and source {source.id!r}")
    return records


def order_of(source: Source, records: list[dict], variant: str | None = None) -> ReadingOrder:
    """Reading order: text files in file-name order; page images by hand-set, edge-read or in-text page numbers."""
    if variant == TEXT_VARIANT:
        return ReadingOrder(pages=[PlacedPage(r["scan"], str(r.get("image") or ""), None, HOW_TEXT) for r in records])
    return reading_order(records, source.manual_page_numbers(), load_page_numbers(source.numbers_file))


def write_text(source: Source, variant: str, records: list[dict], order: ReadingOrder) -> None:
    target = source.text_file(variant)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(book_markdown(records, order, source.title), encoding="utf-8")


def write_segments(source: Source, variant: str, records: list[dict], order: ReadingOrder) -> int:
    """Segments in reading order, so a paragraph that runs over a page break is followed by its continuation."""
    printed = {page.scan: page.printed for page in order.pages}
    segments = segment_records(ordered_records(records, order), printed)
    write_jsonl(segments, source.segments_file(variant))
    return len(segments)


def take_texts(source: Source, log: Callable[[str], None] = print) -> int:
    """Store every text file as a record of the variant `original`; a file is redone only when it changed."""
    out_dir = source.ocr_dir(TEXT_VARIANT)
    out_dir.mkdir(parents=True, exist_ok=True)
    taken = 0
    for page in source.text_pages():
        target = scan_file(out_dir, page.scan)
        digest = sha256_file(page.image)
        if target.is_file():
            old = json.loads(target.read_text(encoding="utf-8"))
            if old.get("image") == page.image.name and old.get("image_sha256") == digest:
                continue
        record = {
            "source": source.id,
            "scan": page.scan,
            "image": page.image.name,
            "image_sha256": digest,
            "backend": TEXT_VARIANT,
            "model": None,
            "prompt_version": None,
            "confidence": None,
            "quality": "original",
            "warnings": [],
            "seconds": 0.0,
            "created": datetime.now(UTC).isoformat(timespec="seconds"),
            "text": page.image.read_text(encoding="utf-8"),
        }
        target.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        taken += 1
        log(f"text {page.scan}: {page.image.name}")
    for stale in sorted(out_dir.glob("scan-*.json")):  # a text file that was removed or renamed
        if int(stale.stem.split("-")[1]) > len(source.text_pages()):
            stale.unlink()
    return taken


def ingest_source(
    source: Source,
    backend: OcrBackend | None,
    variant: str,
    numbers: PageNumberReader | None = None,
    workers: int = 1,
    log: Callable[[str], None] = print,
) -> IngestReport:
    """Run every ingest step for the original files of a source and say what to review."""
    report = IngestReport(source=source.id)
    manifest = source.write_manifest()
    log(f"{len(manifest['files'])} files recorded in {source.files_manifest}")
    if not manifest["files"]:
        report.review.append(f"no files yet: put the originals into {source.files_dir}")
        return report

    if source.texts():
        take_texts(source, log)
        records = load_variant(source, TEXT_VARIANT)
        order = order_of(source, records, TEXT_VARIANT)
        write_text(source, TEXT_VARIANT, records, order)
        report.variants.append(TEXT_VARIANT)
        report.segments[TEXT_VARIANT] = write_segments(source, TEXT_VARIANT, records, order)

    if source.images():
        if backend is None:
            raise ValueError("the source has page images: choose an OCR backend (--backend)")
        run_ocr(source, backend, source.ocr_dir(variant), log=log, workers=workers)
        if numbers is not None:
            read_page_numbers(source, numbers, source.numbers_file, log=log, workers=workers)
        records = load_variant(source, variant)
        order = order_of(source, records, variant)
        write_order(order, variant, source.order_file(variant))
        write_text(source, variant, records, order)
        report.variants.append(variant)
        report.segments[variant] = write_segments(source, variant, records, order)
        if order.gaps:
            report.review.append(f"{len(order.gaps)} printed pages missing between the first and the last")
        if order.duplicates:
            report.review.append(f"{len(order.duplicates)} page numbers found twice (a retake or a misread number)")
        if order.unknown:
            report.review.append(f"{len(order.unknown)} pages without a number")
        if order.gaps or order.duplicates or order.unknown:
            report.review.append(
                f"details in {source.order_file(variant)}; fix with printed_pages in source.yaml and run again"
            )
    for variant_name in report.variants:
        report.review.append(f"read {source.text_file(variant_name)} and compare a few pages with the originals")
    return report
