"""`mmo` - command line of the project (topics, sources, OCR, segmentation)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from mmo.config import Settings
from mmo.core.check import check_source
from mmo.core.migrate import migrate_topic, needs_migration
from mmo.core.topic import ROLES, SOURCE_KINDS, Topic, sha256_file
from mmo.ingest.clean import clean_record, import_record, merge_variants
from mmo.ingest.compare import cer
from mmo.ingest.ocr import BACKENDS, load_pages, make_backend, run_ocr, scan_file
from mmo.ingest.order import write_order
from mmo.ingest.page_numbers import read_page_numbers
from mmo.ingest.pipeline import TEXT_VARIANT, ingest_source, load_variant, order_of, write_segments, write_text


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


def cmd_source_add(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    source = topic.add_source(
        args.source, args.kind, title=args.title, role=args.role, about=args.about, language=args.language
    )
    print(f"created {source.root}")
    print(f"next: put the original files into {source.files_dir}, fill in {source.metadata_file} and")
    print(f"{source.notes_file}, then run: mmo ingest {topic.slug} {source.id}")
    return 0


def cmd_source_scan(args: argparse.Namespace) -> int:
    source = load_topic(args).source(args.source)
    manifest = source.write_manifest()
    print(f"{source.files_manifest}: {len(manifest['files'])} files")
    return 0


def cmd_source_check(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    sources = [topic.source(args.source)] if args.source else topic.sources()
    for source in sources:
        findings = check_source(source)
        role = source.metadata().get("role", "primary")
        print(f"{source.id} ({role}): {'complete' if not findings else f'{len(findings)} to fill in or review'}")
        for finding in findings:
            print(f"  - {finding}")
    if not sources:
        print(f"no sources yet: mmo source add {topic.slug} <id> --kind ...")
    return 0


def ocr_variant(args: argparse.Namespace, settings: Settings) -> tuple[str, str | None]:
    """Variant folder name and the model of the openai backend, from --backend, --model and --mode."""
    model = args.model or (settings.ocr_model if args.backend == "openai" else None)
    detail = (
        model if args.backend == "openai" else (args.mode if args.backend == "fabric" and args.mode != "auto" else None)
    )
    return ocr_backend_dir(args.backend, detail), model


def cmd_ingest(args: argparse.Namespace) -> int:
    """All ingest steps for one source; resumable; ends with what to review."""
    settings = Settings.load()
    source = load_topic(args).source(args.source)
    if not source.metadata_file.is_file():
        raise FileNotFoundError(f"no such source: {source.root} (create it with mmo source add)")
    variant, model = ocr_variant(args, settings)
    backend = make_backend(args.backend, settings, model=model, mode=args.mode) if source.images() else None
    numbers = None
    if backend is not None and args.backend == "fabric" and not args.no_numbers:
        from mmo.ingest.ocr.fabric import FabricPageNumbers, connect_client  # needs the service's client

        numbers = FabricPageNumbers(connect_client(settings.fabric_ocr_url, settings.fabric_ocr_token))
    report = ingest_source(source, backend, variant, numbers=numbers, workers=args.workers)
    for name in report.variants:
        print(f"{name}: {report.segments[name]} segments -> {source.segments_file(name)}")
    if report.review:
        print("to review:")
        for line in report.review:
            print(f"  - {line}")
    print(f"what the source still lacks: mmo source check {args.topic} {source.id}")
    return 0


def cmd_ocr_run(args: argparse.Namespace) -> int:
    settings = Settings.load()
    source = load_topic(args).source(args.source)
    if not source.pages():
        print(f"no page images in {source.files_dir}", file=sys.stderr)
        return 1
    variant, model = ocr_variant(args, settings)
    backend = make_backend(args.backend, settings, model=model, mode=args.mode)
    out_dir = source.ocr_dir(variant)
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
    order = order_of(source, load_variant(source, args.variant), args.variant)
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
    order = order_of(source, records, args.variant)
    write_text(source, args.variant, records, order)
    print(f"{len(order.pages)} pages in reading order written to {source.text_file(args.variant)}")
    return 0


def cmd_ocr_clean(args: argparse.Namespace) -> int:
    """Rule-based clean-up into <variant>-clean; stuck pages take the fallback variant's text when it has them."""
    source = load_topic(args).source(args.source)
    records = load_pages(source.ocr_dir(args.variant))
    if not records:
        print(f"no OCR records in {source.ocr_dir(args.variant)}", file=sys.stderr)
        return 1
    fallback = {r["scan"]: r for r in load_pages(source.ocr_dir(args.fallback))} if args.fallback else {}
    out_dir = source.ocr_dir(f"{args.variant}-clean")
    out_dir.mkdir(parents=True, exist_ok=True)
    removed = replaced = 0
    left: list[str] = []
    for record in records:
        cleaned = clean_record(record, args.variant, fallback.get(record["scan"]), args.fallback)
        scan_file(out_dir, record["scan"]).write_text(
            json.dumps(cleaned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        info = cleaned["cleaning"]
        removed += len(info["removed"])
        if info.get("replaced_from"):
            replaced += 1
        elif info["stuck"]:
            left.append(f"scan {record['scan']} {record['image']}: {', '.join(info['stuck'])}")
    summary = f"{len(records)} scans, {removed} lines removed or shortened"
    print(f"{summary}, {replaced} scans replaced from {args.fallback} -> {out_dir}")
    if left:
        print(f"{len(left)} stuck scans without a replacement (read them again):")
        for line in left:
            print(f"  - {line}")
    return 0


def cmd_ocr_import(args: argparse.Namespace) -> int:
    """Transcriptions scan-NNNN.txt made outside the OCR backends, stored as an OCR variant with provenance."""
    source = load_topic(args).source(args.source)
    pages = {page.scan: page for page in source.pages()}
    out_dir = source.ocr_dir(args.variant)
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(args.folder.glob("scan-*.txt")):
        scan = int(path.stem.split("-")[1])
        if scan not in pages:
            raise ValueError(f"{path.name}: {source.id} has no scan {scan}")
        image = pages[scan].image
        text = path.read_text(encoding="utf-8")
        record = import_record(source.id, scan, image, sha256_file(image), text, args.model, args.prompt_version)
        scan_file(out_dir, scan).write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        count += 1
    print(f"{count} transcriptions imported -> {out_dir}")
    return 0 if count else 1


def cmd_ocr_merge(args: argparse.Namespace) -> int:
    """Several variants into one: each scan from the first variant listed that has it (provenance kept per page)."""
    source = load_topic(args).source(args.source)
    merged = merge_variants({name: load_variant(source, name) for name in args.variants})
    out_dir = source.ocr_dir(args.into)
    out_dir.mkdir(parents=True, exist_ok=True)
    for record in merged:
        path = scan_file(out_dir, record["scan"])
        path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    taken = Counter(record["merged_from"] for record in merged)
    missing = sorted({page.scan for page in source.pages()} - {record["scan"] for record in merged})
    print(f"{len(merged)} scans -> {out_dir} ({', '.join(f'{taken[v]} from {v}' for v in args.variants)})")
    if missing:
        print(f"scans in no variant: {compact_ranges(missing)}")
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
    count = write_segments(source, args.variant, records, order_of(source, records, args.variant))
    print(f"{count} segments from {len(records)} scans written to {source.segments_file(args.variant)}")
    return 0


def add_backend_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--backend", choices=BACKENDS, default="tesseract")
    parser.add_argument("--model", help="model name for the openai backend (default: MMO_OCR_MODEL)")
    parser.add_argument(
        "--mode",
        choices=("auto", "accurate", "fast"),
        default="auto",
        help="fabric backend: auto (OCR model for photos), accurate (always the model), fast (CPU Tesseract only)",
    )


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
    add = source.add_parser("add", help="create a source: source.yaml, notes.md and files/, listed in topic.yaml")
    add.add_argument("topic")
    add.add_argument("source", help="id: lowercase letters, digits and dashes")
    add.add_argument("--kind", required=True, choices=SOURCE_KINDS)
    add.add_argument("--title", help="human-readable title")
    add.add_argument(
        "--role", choices=ROLES, default="primary", help="context = supplementary material about other sources"
    )
    add.add_argument("--about", action="append", help="for --role context: id of the source it is about (repeatable)")
    add.add_argument("--language", help="ISO 639-3, e.g. ces")
    add.set_defaults(func=cmd_source_add)
    scan = source.add_parser("scan", help="record the original files and their hashes in ingest/files.yaml")
    scan.add_argument("topic")
    scan.add_argument("source")
    scan.set_defaults(func=cmd_source_scan)
    check = source.add_parser("check", help="what a source still lacks: metadata, links, ingest, review")
    check.add_argument("topic")
    check.add_argument("source", nargs="?", help="one source (default: all)")
    check.set_defaults(func=cmd_source_check)

    ingest = sub.add_parser("ingest", help=f"all ingest steps for a source (text files: variant {TEXT_VARIANT})")
    ingest.add_argument("topic")
    ingest.add_argument("source")
    add_backend_options(ingest)
    ingest.add_argument("--workers", type=int, default=2, help="images read at the same time")
    ingest.add_argument("--no-numbers", action="store_true", help="fabric: skip reading page numbers from the edges")
    ingest.set_defaults(func=cmd_ingest)

    variant_help = "OCR variant folder under ingest/ocr"
    ocr = sub.add_parser("ocr", help="OCR of page images").add_subparsers(dest="action", required=True)
    run = ocr.add_parser("run", help="OCR the page images of a source with one backend")
    run.add_argument("topic")
    run.add_argument("source")
    add_backend_options(run)
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
    clean = ocr.add_parser("clean", help="remove OCR junk by rules into <variant>-clean; find stuck pages")
    clean.add_argument("topic")
    clean.add_argument("source")
    clean.add_argument("--variant", required=True, help=variant_help)
    clean.add_argument("--fallback", help="variant with new readings; each scan it has replaces the cleaned text")
    clean.set_defaults(func=cmd_ocr_clean)
    imp = ocr.add_parser("import", help="store transcriptions scan-NNNN.txt from a folder as an OCR variant")
    imp.add_argument("topic")
    imp.add_argument("source")
    imp.add_argument("folder", type=Path)
    imp.add_argument("--variant", required=True, help="new variant folder under ingest/ocr")
    imp.add_argument("--model", required=True, help="who or what transcribed it, e.g. a model id or 'manual'")
    imp.add_argument("--prompt-version", required=True, help="version of the instructions used")
    imp.set_defaults(func=cmd_ocr_import)

    merge = ocr.add_parser("merge", help="several variants into one, each scan from the first variant that has it")
    merge.add_argument("topic")
    merge.add_argument("source")
    merge.add_argument("--variants", nargs="+", required=True, help="variants in order of preference")
    merge.add_argument("--into", required=True, help="new variant folder under ingest/ocr")
    merge.set_defaults(func=cmd_ocr_merge)

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
