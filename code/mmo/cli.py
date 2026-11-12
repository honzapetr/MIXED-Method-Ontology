"""`mmo` - command line of the project (topics, sources, OCR, segmentation)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mmo.config import Settings
from mmo.core.migrate import migrate_topic, needs_migration
from mmo.core.topic import Source, Topic
from mmo.ingest.compare import cer
from mmo.ingest.ocr import BACKENDS, load_pages, make_backend, run_ocr
from mmo.ingest.order import ReadingOrder, book_markdown, ordered_records, reading_order, write_order
from mmo.ingest.page_numbers import load_page_numbers, read_page_numbers
from mmo.ingest.segment import segment_records, write_jsonl


def parse_scans(value: str | None) -> set[int] | None:
    """`1-3,7` -> {1, 2, 3, 7}."""
    if not value:
        return None
    scans: set[int] = set()
    for part in value.split(","):
        first, _, last = part.strip().partition("-")
        scans.update(range(int(first), int(last or first) + 1))
    return scans


def ocr_backend_dir(backend: str, model: str | None) -> str:
    """Folder name of one OCR variant: the backend, plus the model when one is chosen (`openai-qwen2.5-vl`)."""
    if not model:
        return backend
    safe = "".join(c if c.isalnum() or c in ".-_" else "-" for c in model)
    return f"{backend}-{safe}"


def load_topic(args: argparse.Namespace) -> Topic:
    topic = Topic.load(args.topics / args.topic)
    if needs_migration(topic):
        raise RuntimeError(f"{topic.root} is in the old layout; run: mmo topic migrate {args.topic}")
    return topic


def cmd_topic_new(args: argparse.Namespace) -> int:
    topic = Topic.create(args.topics, args.slug, args.title)
    print(f"created {topic.root}")
    return 0


def cmd_topic_migrate(args: argparse.Namespace) -> int:
    topic = Topic.load(args.topics / args.topic)
    if not needs_migration(topic):
        print(f"{topic.root}: already in the source-centric layout")
        return 0
    migrate_topic(topic)
    print(f"{topic.root}: migrated to the source-centric layout (docs/adr/0006)")
    return 0


def cmd_source_scan(args: argparse.Namespace) -> int:
    source = load_topic(args).source(args.source)
    manifest = source.write_manifest()
    print(f"{source.files_manifest}: {len(manifest['files'])} files")
    return 0


def cmd_ocr_run(args: argparse.Namespace) -> int:
    settings = Settings.load()
    source = load_topic(args).source(args.source)
    if not source.pages():
        print(f"no page images in {source.files_dir}", file=sys.stderr)
        return 1
    model = args.model or (settings.ocr_model if args.backend == "openai" else None)
    backend = make_backend(args.backend, settings, model=model, mode=args.mode)
    variant = (
        model if args.backend == "openai" else (args.mode if args.backend == "fabric" and args.mode != "auto" else None)
    )
    out_dir = source.ocr_dir(ocr_backend_dir(args.backend, variant))
    written = run_ocr(source, backend, out_dir, scans=parse_scans(args.scans), force=args.force, workers=args.workers)
    print(f"{len(written)} scans written to {out_dir}")
    return 0


def cmd_ocr_compare(args: argparse.Namespace) -> int:
    """CER per scan: each variant against ground truth, or the other variants against the first one."""
    source = load_topic(args).source(args.source)
    variants = args.variants or source.ocr_variants()
    texts = {v: {r["scan"]: r["text"] for r in load_pages(source.ocr_dir(v))} for v in variants}
    truth = {
        int(p.stem.split("-")[1]): p.read_text(encoding="utf-8") for p in source.ground_truth_dir.glob("scan-*.txt")
    }
    if truth:
        reference_name, reference = "ground-truth", truth
    elif len(variants) >= 2:
        reference_name, reference = variants[0], texts[variants[0]]
        variants = variants[1:]
    else:
        print("nothing to compare: add ground-truth scans or run at least two OCR variants", file=sys.stderr)
        return 1
    report: dict[str, dict] = {}
    for variant in variants:
        scans = {s: round(cer(reference[s], texts[variant][s]), 4) for s in sorted(reference) if s in texts[variant]}
        mean = round(sum(scans.values()) / len(scans), 4) if scans else None
        report[variant] = {"reference": reference_name, "mean_cer": mean, "scans": scans}
        print(f"{variant:40} vs {reference_name:20} mean CER {mean} over {len(scans)} scans")
    if args.json:
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


def load_variant(source: Source, variant: str) -> list[dict]:
    records = load_pages(source.ocr_dir(variant))
    if not records:
        raise FileNotFoundError(f"no OCR results for variant {variant!r} and source {source.id!r}")
    return records


def order_of(source: Source, records: list[dict]) -> ReadingOrder:
    """Reading order from hand-set numbers, numbers read from the page edges and numbers found in the text."""
    return reading_order(records, source.manual_page_numbers(), load_page_numbers(source.numbers_file))


def cmd_ocr_numbers(args: argparse.Namespace) -> int:
    """Printed page numbers read from the top and bottom edge of every image (the fabric service's Extract)."""
    from mmo.ingest.ocr.fabric import FabricPageNumbers, connect_client  # needs the service's client

    settings = Settings.load()
    source = load_topic(args).source(args.source)
    reader = FabricPageNumbers(connect_client(settings.fabric_ocr_url, settings.fabric_ocr_token))
    count = read_page_numbers(source, reader, source.numbers_file, workers=args.workers)
    print(f"{count} images read, numbers in {source.numbers_file}")
    return 0


def cmd_ocr_order(args: argparse.Namespace) -> int:
    """Reading order by printed page numbers: a report to review, gaps and duplicates on the console."""
    source = load_topic(args).source(args.source)
    order = order_of(source, load_variant(source, args.variant))
    target = source.order_file(args.variant)
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
    source = load_topic(args).source(args.source)
    records = load_variant(source, args.variant)
    order = order_of(source, records)
    target = source.text_file(args.variant)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(book_markdown(records, order, source.title), encoding="utf-8")
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
    source = load_topic(args).source(args.source)
    records = load_variant(source, args.variant)
    order = order_of(source, records)
    # pages in reading order, so a paragraph that runs over a page break is followed by its continuation
    printed = {page.scan: page.printed for page in order.pages}
    segments = segment_records(ordered_records(records, order), printed)
    target = source.segments_file(args.variant)
    write_jsonl(segments, target)
    print(f"{len(segments)} segments from {len(records)} scans written to {target}")
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
    migrate = topic.add_parser("migrate", help="move a topic from the old layout by step to the layout by source")
    migrate.add_argument("topic")
    migrate.set_defaults(func=cmd_topic_migrate)

    source = sub.add_parser("source", help="sources").add_subparsers(dest="action", required=True)
    scan = source.add_parser("scan", help="record the original files and their hashes in ingest/files.yaml")
    scan.add_argument("topic")
    scan.add_argument("source")
    scan.set_defaults(func=cmd_source_scan)

    variant_help = "OCR variant folder under ingest/ocr"
    ocr = sub.add_parser("ocr", help="OCR of page images").add_subparsers(dest="action", required=True)
    run = ocr.add_parser("run", help="OCR the page images of a source with one backend")
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
    run.add_argument("--workers", type=int, default=1, help="images read at the same time (fabric: 2)")
    run.add_argument("--scans", "--pages", dest="scans", help="only these scans (file-name order), e.g. 1-5,9")
    run.add_argument("--force", action="store_true", help="redo scans that already have a result")
    run.set_defaults(func=cmd_ocr_run)
    compare = ocr.add_parser("compare", help="character error rate of OCR variants")
    compare.add_argument("topic")
    compare.add_argument("source")
    compare.add_argument("variants", nargs="*", help="variant folders under ingest/ocr (default: all)")
    compare.add_argument("--json", type=Path, help="also write the report as JSON")
    compare.set_defaults(func=cmd_ocr_compare)
    order = ocr.add_parser("order", help="reading order by printed page numbers (gaps, duplicates, unknown pages)")
    order.add_argument("topic")
    order.add_argument("source")
    order.add_argument("--variant", default="tesseract", help=variant_help)
    order.set_defaults(func=cmd_ocr_order)
    numbers = ocr.add_parser("numbers", help="read printed page numbers from the page edges (fabric service)")
    numbers.add_argument("topic")
    numbers.add_argument("source")
    numbers.add_argument("--workers", type=int, default=2, help="images read at the same time")
    numbers.set_defaults(func=cmd_ocr_numbers)
    book = ocr.add_parser("book", help="the whole text of one variant in reading order, into text/<variant>.md")
    book.add_argument("topic")
    book.add_argument("source")
    book.add_argument("--variant", default="tesseract", help=variant_help)
    book.set_defaults(func=cmd_ocr_book)

    seg = sub.add_parser("segment", help="split OCR text of one variant into segments")
    seg.add_argument("topic")
    seg.add_argument("source")
    seg.add_argument("--variant", default="tesseract", help=variant_help)
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
