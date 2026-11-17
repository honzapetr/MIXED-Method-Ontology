"""Bringing one source to its final text (docs/source-pipeline.md, ADR 0012).

`mmo ingest` runs the conversion in one call: files, OCR, page numbers, reading order, the text of the variant.
Every step is resumable - OCR and page numbers read only what is missing, the rest is cheap to redo - so an
interrupted run is simply started again. Text files (`.txt`, `.md`) are taken as they are, as the variant `original`.
`mmo source finalize` then writes `text.md` from the variant the researcher chose and cuts it into segments.
"""

from __future__ import annotations

import json
from collections import Counter
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
    reading_order,
    write_order,
)
from mmo.ingest.page_numbers import PageNumberReader, load_page_numbers, read_page_numbers
from mmo.ingest.segment import join_hyphenated, segment_text, write_jsonl

TEXT_VARIANT = "original"
UNCLEAR = "[?]"  # a word the reader could not read


@dataclass
class IngestReport:
    source: str
    variants: list[str] = field(default_factory=list)
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
    retakes = source.retakes()  # second photos of a page: left out of the order, so out of the text and segments
    kept = [r for r in records if str(r.get("image") or "") not in retakes]
    return reading_order(kept, source.manual_page_numbers(), load_page_numbers(source.numbers_file))


def write_text(source: Source, variant: str, records: list[dict], order: ReadingOrder) -> None:
    target = source.text_file(variant)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(book_markdown(records, order, source.title), encoding="utf-8")


def compact_ranges(numbers: list[int]) -> str:
    """[3, 4, 5, 9] -> "3-5, 9"."""
    spans: list[list[int]] = []
    for n in numbers:
        if spans and n == spans[-1][1] + 1:
            spans[-1][1] = n
        else:
            spans.append([n, n])
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in spans)


def final_text_markdown(source: Source, variant: str, records: list[dict], order: ReadingOrder) -> str:
    """The final text: a header saying what it is and what it lacks, then the variant's text in reading order.

    Words hyphenated across a line end are joined here, so the final text and its segments read as plain text.
    """
    records = [{**record, "text": join_hyphenated(record["text"])} for record in records]
    by_scan = {record["scan"]: record for record in records}
    placed = [by_scan[page.scan] for page in order.pages]
    printed = [page.printed for page in order.pages if page.printed is not None]
    models = Counter(str(record.get("model") or record.get("backend") or "unknown") for record in placed)
    header = {
        "source": source.id,
        "title": source.title,
        "status": "final - the text for the analysis",
        "variant": variant,
        "built": datetime.now(UTC).date().isoformat(),
        "pages": len(order.pages),
    }
    if printed:
        header["printed_pages"] = f"{min(printed)}-{max(printed)}"
        before = [f"1-{min(printed) - 1}"] if min(printed) > 1 else []
        missing = before + ([compact_ranges(order.gaps)] if order.gaps else [])
        header["missing_pages"] = ", ".join(missing) or "none"
    header["pages_without_number"] = [f"scan {page.scan} {page.image}" for page in order.unknown]
    header["unclear_words"] = sum(record["text"].count(UNCLEAR) for record in placed)
    header["read_by"] = dict(sorted(models.items()))
    lines = ["---"] + [f"{key}: {json.dumps(value, ensure_ascii=False)}" for key, value in header.items()] + ["---"]
    note = (
        f"> Final text of `{source.id}` for the analysis. Do not edit by hand: built by `mmo source finalize` from "
        f"the OCR variant `{variant}` (`text` in `source.yaml`). Each page sits under a comment with its printed page, "
        f"scan and image, so every quote can be traced to the photo. `{UNCLEAR}` marks a word nobody could read."
    )
    return "\n".join(lines) + "\n\n" + note + "\n\n" + book_markdown(records, order, source.title)


def write_final_text(source: Source) -> tuple[str, ReadingOrder, int]:
    """Write `text.md` from the variant named in `text` of `source.yaml`, then its segments; return the count."""
    variant = source.final_variant()
    if variant is None:
        raise ValueError(
            f"choose the final variant first: add `text: {{variant: <variant>}}` to {source.metadata_file}"
        )
    records = load_variant(source, variant)
    order = order_of(source, records, variant)
    text = final_text_markdown(source, variant, records, order)
    source.final_text_file.write_text(text, encoding="utf-8", newline="\n")
    return variant, order, write_segments(source)


def write_segments(source: Source) -> int:
    """Cut `text.md` into segments (`segments.jsonl`); they follow its reading order."""
    if not source.final_text_file.is_file():
        raise FileNotFoundError(
            f"no final text yet: {source.final_text_file} (mmo source finalize {source.topic.slug} {source.id})"
        )
    text = source.final_text_file.read_text(encoding="utf-8")
    segments = segment_text(source.id, text)
    write_jsonl(segments, source.segments_file)
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
    if report.variants:
        report.review.append(
            "choose the variant for the analysis (text: {variant: <variant>} in source.yaml), then "
            f"mmo source finalize {source.topic.slug} {source.id} - it writes text.md and its segments"
        )
    return report
