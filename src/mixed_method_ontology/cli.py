"""`mmo` - command line of the project (topics, OCR, segmentation)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from mixed_method_ontology.config import Settings
from mixed_method_ontology.metrics import cer
from mixed_method_ontology.ocr import BACKENDS, load_pages, make_backend, run_ocr
from mixed_method_ontology.segment import segment_records, write_jsonl
from mixed_method_ontology.topic import Topic


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
    backend = make_backend(args.backend, settings, model=model)
    out_dir = topic.ocr_dir(ocr_backend_dir(args.backend, model), source.id)
    written = run_ocr(source, backend, out_dir, pages=parse_pages(args.pages), force=args.force)
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


def cmd_segment(args: argparse.Namespace) -> int:
    topic = Topic.load(args.topics / args.topic)
    records = load_pages(topic.root / "work" / "ocr" / args.variant / args.source)
    if not records:
        print(f"no OCR results for variant {args.variant!r} and source {args.source!r}", file=sys.stderr)
        return 1
    segments = segment_records(records)
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
    run.add_argument("--pages", help="only these pages, e.g. 1-5,9")
    run.add_argument("--force", action="store_true", help="redo pages that already have a result")
    run.set_defaults(func=cmd_ocr_run)
    compare = ocr.add_parser("compare", help="character error rate of OCR variants")
    compare.add_argument("topic")
    compare.add_argument("source")
    compare.add_argument("variants", nargs="*", help="variant folders under work/ocr (default: all)")
    compare.add_argument("--json", type=Path, help="also write the report as JSON")
    compare.set_defaults(func=cmd_ocr_compare)

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
