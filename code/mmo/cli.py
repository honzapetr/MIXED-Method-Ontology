"""`mmo` - command line of the project (topics, OCR, segmentation)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mmo.config import Settings
from mmo.core.topic import Source, Topic
from mmo.ingest.compare import cer
from mmo.ingest.ocr import BACKENDS, load_pages, make_backend, run_ocr
from mmo.ingest.order import ReadingOrder, book_markdown, ordered_records, reading_order, write_order
from mmo.ingest.page_numbers import load_page_numbers, read_page_numbers
from mmo.ingest.segment import segment_records, write_jsonl


def parse_pages(value: str | None) -> set[int] | None:
    """`1-3,7` -> {1, 2, 3, 7}."""
    if not value:
        return None
    pages: set[int] = set()
    for part in value.split(","):
        first, _, last = part.strip().partition("-")
        pages.update(range(int(first), int(last or first) + 1))
    return pages


def ocr_backend_dir(backend: str, model: str | None) -> str:
    """Folder name of one OCR variant: the backend, plus the model when one is chosen (`openai-qwen2.5-vl`)."""
    if not model:
        return backend
    safe = "".join(c if c.isalnum() or c in ".-_" else "-" for c in model)
    return f"{backend}-{safe}"


def cmd_topic_new(args: argparse.Namespace) -> int:
    topic = Topic.create(args.topics, args.slug, args.title)
    print(f"created {topic.root}")
    return 0


def cmd_source_scan(args: argparse.Namespace) -> int:
    source = Topic.load(args.topics / args.topic).source(args.source)
    meta = source.write_manifest()
    print(f"{source.root / 'source.yaml'}: {len(meta['pages'])} pages")
    return 0


def cmd_ocr_run(args: argparse.Namespace) -> int:
    settings = Settings.load()
    topic = Topic.load(args.topics / args.topic)
    source = topic.source(args.source)
    if not source.pages():
        print(f"no page images in {source.root}", file=sys.stderr)
        return 1
    model = args.model or (settings.ocr_model if args.backend == "openai" else None)
    backend = make_backend(args.backend, settings, model=model, mode=args.mode)
    variant = (
        model if args.backend == "openai" else (args.mode if args.backend == "fabric" and args.mode != "auto" else None)
    )
    out_dir = topic.ocr_dir(ocr_backend_dir(args.backend, variant), source.id)
    written = run_ocr(source, backend, out_dir, pages=parse_pages(args.pages), force=args.force, workers=args.workers)
    print(f"{len(written)} pages written to {out_dir}")
    return 0


def cmd_ocr_compare(args: argparse.Namespace) -> int:
    """CER per page: each variant against ground truth, or the other variants against the first one."""
    topic = Topic.load(args.topics / args.topic)
    base = topic.root / "work" / "ocr"
    variants = args.variants or sorted(p.name for p in base.iterdir() if (p / args.source).is_dir())
    texts = {v: {r["page"]: r["text"] for r in load_pages(base / v / args.source)} for v in variants}
    truth_dir = topic.ground_truth_dir(args.source)
    truth = {int(p.stem.split("-")[1]): p.read_text(encoding="utf-8") for p in truth_dir.glob("page-*.txt")}
    if truth:
        reference_name, reference = "ground-truth", truth
    elif len(variants) >= 2:
        reference_name, reference = variants[0], texts[variants[0]]
        variants = variants[1:]
    else:
        print("nothing to compare: add ground-truth pages or run at least two OCR variants", file=sys.stderr)
        return 1
    report: dict[str, dict] = {}
    for variant in variants:
        pages = {p: round(cer(reference[p], texts[variant][p]), 4) for p in sorted(reference) if p in texts[variant]}
        mean = round(sum(pages.values()) / len(pages), 4) if pages else None
        report[variant] = {"reference": reference_name, "mean_cer": mean, "pages": pages}
        print(f"{variant:40} vs {reference_name:20} mean CER {mean} over {len(pages)} pages")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


def load_variant(topic: Topic, variant: str, source_id: str) -> list[dict]:
    records = load_pages(topic.ocr_dir(variant, source_id))
    if not records:
        raise FileNotFoundError(f"no OCR results for variant {variant!r} and source {source_id!r}")
    return records


def order_of(topic: Topic, source: Source, records: list[dict]) -> ReadingOrder:
    """Reading order from hand-set numbers, numbers read from the page edges and numbers found in the text."""
    return reading_order(records, source.manual_page_numbers(), load_page_numbers(topic.numbers_file(source.id)))


def cmd_ocr_numbers(args: argparse.Namespace) -> int:
    """Printed page numbers read from the top and bottom edge of every image (the fabric service's Extract)."""
    from mmo.ingest.ocr.fabric import FabricPageNumbers, connect_client  # needs the service's client

    settings = Settings.load()
    topic = Topic.load(args.topics / args.topic)
    source = topic.source(args.source)
    reader = FabricPageNumbers(connect_client(settings.fabric_ocr_url, settings.fabric_ocr_token))
    target = topic.numbers_file(source.id)
    count = read_page_numbers(source, reader, target, workers=args.workers)
    print(f"{count} images read, numbers in {target}")
    return 0


def cmd_ocr_order(args: argparse.Namespace) -> int:
    """Reading order by printed page numbers: a report to review, gaps and duplicates on the console."""
    topic = Topic.load(args.topics / args.topic)
    source = topic.source(args.source)
    order = order_of(topic, source, load_variant(topic, args.variant, source.id))
    target = topic.order_file(args.variant, source.id)
    write_order(order, args.variant, target)
    summary = order.to_dict(args.variant)["summary"]
    print(
        f"{summary['pages']} pages: {summary['printed']} printed, {summary['inferred']} inferred, "
        f"{summary['corrected']} corrected, {summary['manual']} manual, {summary['unknown']} unknown -> {target}"
    )
    if order.gaps:
        print(f"missing pages: {compact_ranges(order.gaps)}")
    for number, images in order.duplicates.items():
        print(f"page {number} twice: {', '.join(images)}")
    for page in order.unknown:
        print(f"no page number: scan {page.scan} {page.image}")
    for page in order.pages:
        if page.how == "corrected":
            print(f"read {page.found}, between its neighbours -> {page.printed}: {page.image}")
    if order.unknown or order.duplicates:
        print("fix by hand: printed_pages: {<image>: <page>} in source.yaml, then run this again")
    return 0


def cmd_ocr_book(args: argparse.Namespace) -> int:
    """The whole text of one variant in reading order, as one Markdown file."""
    topic = Topic.load(args.topics / args.topic)
    source = topic.source(args.source)
    records = load_variant(topic, args.variant, source.id)
    order = order_of(topic, source, records)
    title = str(source.metadata().get("title") or source.id)
    target = topic.book_file(args.variant, source.id)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(book_markdown(records, order, title), encoding="utf-8")
    print(f"{len(records)} pages in reading order written to {target}")
    return 0


def compact_ranges(numbers: list[int]) -> str:
    """[3, 4, 5, 9] -> "3-5, 9"."""
    ranges: list[list[int]] = []
    for n in numbers:
        if ranges and n == ranges[-1][1] + 1:
            ranges[-1][1] = n
        else:
            ranges.append([n, n])
    return ", ".join(str(a) if a == b else f"{a}-{b}" for a, b in ranges)


def cmd_segment(args: argparse.Namespace) -> int:
    topic = Topic.load(args.topics / args.topic)
    source = topic.source(args.source)
    records = load_variant(topic, args.variant, source.id)
    # pages in reading order, so a paragraph that runs over a page break is followed by its continuation
    segments = segment_records(ordered_records(records, order_of(topic, source, records)))
    target = topic.segments_file(args.source)
    write_jsonl(segments, target)
    print(f"{len(segments)} segments from {len(records)} pages written to {target}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mmo", description=__doc__)
    parser.add_argument("--topics", type=Path, default=Path("topics"), help="folder with topics (default: topics)")
    sub = parser.add_subparsers(dest="command", required=True)

    topic = sub.add_parser("topic", help="topics").add_subparsers(dest="action", required=True)
    new = topic.add_parser("new", help="create a topic folder")
    new.add_argument("slug")
    new.add_argument("--title", required=True)
    new.set_defaults(func=cmd_topic_new)

    source = sub.add_parser("source", help="sources").add_subparsers(dest="action", required=True)
    scan = source.add_parser("scan", help="record page images and their hashes in source.yaml")
    scan.add_argument("topic")
    scan.add_argument("source")
    scan.set_defaults(func=cmd_source_scan)

    ocr = sub.add_parser("ocr", help="OCR of page images").add_subparsers(dest="action", required=True)
    run = ocr.add_parser("run", help="OCR the pages of a source with one backend")
    run.add_argument("topic")
    run.add_argument("source")
    run.add_argument("--backend", choices=BACKENDS, default="tesseract")
    run.add_argument("--model", help="model name for the openai backend (default: MMO_OCR_MODEL)")
    run.add_argument(
        "--mode",
        choices=("auto", "accurate", "fast"),
        default="auto",
        help="fabric backend: auto (OCR model for photos), accurate (always the model), fast (CPU Tesseract only)",
    )
    run.add_argument("--workers", type=int, default=1, help="pages read at the same time (fabric: 2)")
    run.add_argument("--pages", help="only these pages, e.g. 1-5,9")
    run.add_argument("--force", action="store_true", help="redo pages that already have a result")
    run.set_defaults(func=cmd_ocr_run)
    compare = ocr.add_parser("compare", help="character error rate of OCR variants")
    compare.add_argument("topic")
    compare.add_argument("source")
    compare.add_argument("variants", nargs="*", help="variant folders under work/ocr (default: all)")
    compare.add_argument("--json", type=Path, help="also write the report as JSON")
    compare.set_defaults(func=cmd_ocr_compare)
    order = ocr.add_parser("order", help="reading order by printed page numbers (gaps, duplicates, unknown pages)")
    order.add_argument("topic")
    order.add_argument("source")
    order.add_argument("--variant", default="tesseract", help="OCR variant folder under work/ocr")
    order.set_defaults(func=cmd_ocr_order)
    numbers = ocr.add_parser("numbers", help="read printed page numbers from the page edges (fabric service)")
    numbers.add_argument("topic")
    numbers.add_argument("source")
    numbers.add_argument("--workers", type=int, default=2, help="images read at the same time")
    numbers.set_defaults(func=cmd_ocr_numbers)
    book = ocr.add_parser("book", help="the whole text of one variant in reading order as Markdown")
    book.add_argument("topic")
    book.add_argument("source")
    book.add_argument("--variant", default="tesseract", help="OCR variant folder under work/ocr")
    book.set_defaults(func=cmd_ocr_book)

    seg = sub.add_parser("segment", help="split OCR text of one variant into segments")
    seg.add_argument("topic")
    seg.add_argument("source")
    seg.add_argument("--variant", default="tesseract", help="OCR variant folder under work/ocr")
    seg.set_defaults(func=cmd_segment)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
