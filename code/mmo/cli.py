"""`mmo` - command line of the project (topics, sources, OCR, final text and its segments)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import yaml

from mmo.analysis.method import check_method, study_methods
from mmo.analysis.quote import MOVED, OK, Quotation, QuoteError, check_study, quote
from mmo.analysis.review import decide, proposals
from mmo.analysis.roles import check_roles, roles_dir, runs
from mmo.analysis.roles import role as role_of
from mmo.analysis.status import own_type_reminder, study_status
from mmo.analysis.store import ACTIVE_STATUSES, Author, Store, author_of, check_store, write_memo
from mmo.config import Settings
from mmo.core.check import check_source
from mmo.core.migrate import migrate_topic, needs_migration
from mmo.core.topic import ROLES, SOURCE_KINDS, Topic, sha256_file
from mmo.ingest.clean import clean_record, import_record, merge_variants
from mmo.ingest.compare import cer
from mmo.ingest.images import prepare_images
from mmo.ingest.ocr import BACKENDS, load_pages, make_backend, run_ocr, scan_file
from mmo.ingest.order import write_order
from mmo.ingest.page_numbers import read_page_numbers
from mmo.ingest.pipeline import (
    TEXT_VARIANT,
    compact_ranges,
    ingest_source,
    load_variant,
    order_of,
    write_final_text,
    write_segments,
    write_text,
)


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


def topic_root(args: argparse.Namespace) -> Path:
    """A topic by slug under --topics, a study folder by path, or the study we are in by its name (ADR 0010)."""
    by_slug = args.topics / args.topic
    if (by_slug / "topic.yaml").is_file():
        return by_slug
    by_path = Path(args.topic)
    if (by_path / "topic.yaml").is_file():
        return by_path.resolve()
    here = Path.cwd()
    if here.name == args.topic and (here / "topic.yaml").is_file():
        return here
    return by_slug


def load_topic(args: argparse.Namespace) -> Topic:
    topic = Topic.load(topic_root(args))
    if needs_migration(topic):
        raise RuntimeError(f"{topic.root} is in the old layout; run: mmo topic migrate {args.topic}")
    return topic


def cmd_topic_new(args: argparse.Namespace) -> int:
    topic = Topic.create(args.topics, args.slug, args.title)
    print(f"created {topic.root}")
    return 0


def cmd_topic_migrate(args: argparse.Namespace) -> int:
    topic = Topic.load(topic_root(args))
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
    print(f"{source.notes_file}, then run: mmo ingest {args.topic} {source.id}")
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
        print(f"no sources yet: mmo source add {args.topic} <id> --kind ...")
    return 0


def cmd_source_finalize(args: argparse.Namespace) -> int:
    """`text.md`, the text the analysis reads, from the variant chosen in `source.yaml`."""
    source = load_topic(args).source(args.source)
    variant, order, count = write_final_text(source)
    print(f"{len(order.pages)} pages of variant {variant} -> {source.final_text_file}")
    print(f"{count} segments -> {source.segments_file}")
    if order.gaps:
        print(f"missing pages: {compact_ranges(order.gaps)}")
    for page in order.unknown:
        print(f"no page number: scan {page.scan} {page.image}")
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
        print(f"{name}: text -> {source.text_file(name)}")
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


def cmd_ocr_images(args: argparse.Namespace) -> int:
    """Page images for a vision model; `--missing-from` skips scans that these variants already have."""
    source = load_topic(args).source(args.source)
    skip = {record["scan"] for name in args.missing_from for record in load_pages(source.ocr_dir(name))}
    written = prepare_images(source, args.out, parse_scans(args.scans), skip, args.size)
    print(f"{len(written)} images -> {args.out}" + (f": scans {compact_ranges(written)}" if written else ""))
    return 0


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


def cmd_segment(args: argparse.Namespace) -> int:
    """Cut `text.md` into segments again (`mmo source finalize` does it too)."""
    source = load_topic(args).source(args.source)
    count = write_segments(source)
    print(f"{count} segments of {source.final_text_file} -> {source.segments_file}")
    return 0


def cmd_quote_find(args: argparse.Namespace) -> int:
    """Make a quotation from words of `text.md`; print it to paste into an analytic file."""
    source = load_topic(args).source(args.source)
    try:
        found = quote(source, args.words, page=args.page, segment=args.segment)
    except QuoteError as err:
        print(f"refused: {err}", file=sys.stderr)
        return 1
    if args.format == "json":
        print(json.dumps(found.record(), ensure_ascii=False))
    else:
        print(yaml.safe_dump({"quotation": found.record()}, allow_unicode=True, sort_keys=False), end="")
    return 0


def cmd_quote_check(args: argparse.Namespace) -> int:
    """Check every quotation of a study against the current `text.md` of its source."""
    topic = load_topic(args)
    results = check_study(topic, update=args.update)
    counts = Counter(r.status for r in results)
    for r in results:
        if r.status == OK:
            continue
        where = r.path.relative_to(topic.root).as_posix()
        words = str(r.record.get("exact", ""))[:60]
        if r.status == MOVED and r.new is not None:
            done = "updated" if args.update else "run with --update to store"
            print(
                f"{where}: moved {r.record.get('start')}-{r.record.get('end')} -> {r.new.start}-{r.new.end} "
                f"({done}): {words!r}"
            )
        else:
            print(f"{where}: {r.status} - {r.note}: {words!r}")
    print(
        f"{len(results)} quotations: " + ", ".join(f"{n} {s}" for s, n in sorted(counts.items()))
        if results
        else "no quotations in the analytic files yet"
    )
    unresolved = sum(n for s, n in counts.items() if s != OK and not (s == MOVED and args.update))
    moved_in_store = [r for r in results if r.status == MOVED and "analysis" in r.path.relative_to(topic.root).parts]
    if args.update and moved_in_store:  # the program changed the store: record it, so it is not taken for a hand edit
        Store(topic).save(None, "update-quotations", count=len(moved_in_store))
    return 1 if unresolved else 0


# ---------------------------------------------------------------- the free toolbox (T32, ADR 0013)


def _author(args: argparse.Namespace, topic: Topic) -> Author:
    return author_of(topic, args.by, args.prompt_version, getattr(args, "run", None))


def _quotation(topic: Topic, source: str, words: str, page: int | None = None, segment: str | None = None) -> Quotation:
    """A quotation; in `--quote`/`--evidence` the page may ride on the source: `kniha@57`."""
    if "@" in source and page is None:
        source, _, at = source.partition("@")
        page = int(at)
    return quote(topic.source(source), words, page=page, segment=segment)


def cmd_code_add(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    code = Store(topic).add_code(
        _author(args, topic), args.label, args.type, args.method, args.definition, args.broader
    )
    print(f"code {code['id']} ({code['status']})")
    if reminder := own_type_reminder(topic, "code", args.type):
        print(reminder)
    return 0


def cmd_code_apply(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    author = _author(args, topic)
    quotation = _quotation(topic, args.source, args.words, args.page, args.segment)
    coding = Store(topic).apply_code(author, args.code, quotation, args.method, args.note)
    pages = "/".join(str(p) for p in quotation.pages) or f"scan {quotation.scans[0]}"
    print(f"coding {coding['id']}: {coding['body']} <- {args.source} p. {pages} ({coding['status']})")
    return 0


def cmd_code_rename(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    code = Store(topic).rename_code(_author(args, topic), args.code, args.label)
    print(f"code {code['id']} is now {code['label']!r}")
    return 0


def cmd_code_merge(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    Store(topic).merge_codes(_author(args, topic), args.into, args.codes, args.reason)
    print(f"merged {', '.join(args.codes)} into {args.into}")
    return 0


def cmd_code_split(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    store = Store(topic)
    new = store.split_code(_author(args, topic), args.code, args.labels, args.reason)
    waiting = [c["id"] for c in store.codings if c["body"] == args.code and c["status"] in ACTIVE_STATUSES]
    print(f"split {args.code} into {', '.join(c['id'] for c in new)}")
    if waiting:
        print(f"{len(waiting)} codings to recode (mmo code recode): {', '.join(waiting)}")
    return 0


def cmd_code_recode(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    coding = Store(topic).recode(_author(args, topic), args.coding, args.code)
    print(f"coding {coding['id']} -> {coding['body']}")
    return 0


def cmd_code_withdraw(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    Store(topic).withdraw(_author(args, topic), args.ref, args.reason)
    print(f"{args.ref} withdrawn (kept in the files for the history)")
    return 0


def cmd_code_list(args: argparse.Namespace) -> int:
    store = Store(load_topic(args))
    counts = Counter(c["body"] for c in store.codings if c["status"] in ACTIVE_STATUSES)
    for code in sorted(store.codes, key=lambda c: c["label"].lower()):
        kind = f" [{code['code_type']}]" if code.get("code_type") else ""
        status = "" if code["status"] == "accepted" else f" ({code['status']})"
        print(f"{code['id']}: {code['label']}{kind} - {counts.get(code['id'], 0)} codings{status}")
    if not store.codes:
        print("no codes yet")
    return 0


def cmd_relation_add(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    author = _author(args, topic)
    evidence = [_quotation(topic, source, words) for source, words in args.evidence or []]
    relation = Store(topic).relate(author, args.subject, args.type, args.object, args.method, args.note, evidence)
    print(f"relation {relation['id']}: {relation['subject']} -{relation['relation_type']}-> {relation['object']}")
    if reminder := own_type_reminder(topic, "relation", args.type):
        print(reminder)
    return 0


def cmd_memo_add(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    author = _author(args, topic)
    body = Path(args.file).read_text(encoding="utf-8") if args.file else (args.text or "")
    quotations = [_quotation(topic, source, words) for source, words in args.quote or []]
    path = write_memo(
        topic, author, args.type, args.title, body, args.about, quotations, args.method, args.phase, args.alternative
    )
    print(f"memo {path.relative_to(topic.root).as_posix()}")
    return 0


def cmd_analysis_check(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    if args.record and not args.by:
        raise ValueError("who edited the files by hand? give --by <analyst id> with --record")
    findings = check_store(topic, record_hand_edits=args.record, by=args.by)
    for finding in findings:
        print(f"{finding.where}: {finding.problem}")
    print("analysis: no problems" if not findings else f"analysis: {len(findings)} to look at")
    return 1 if findings else 0


# ---------------------------------------------------------------- the method as orientation (T33)


def cmd_method_check(args: argparse.Namespace) -> int:
    """Check method folders against the schema of `method.yaml` (methods/README.md of the environment)."""
    base: Path = args.methods
    folders = [base / m for m in args.ids] if args.ids else sorted(p for p in base.iterdir() if p.is_dir())
    failed = 0
    for folder in folders:
        problems = check_method(folder)
        print(f"{folder.name}: {'ok' if not problems else f'{len(problems)} problems'}")
        for problem in problems:
            print(f"  - {problem}")
        failed += bool(problems)
    return 1 if failed else 0


def cmd_phase(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    methods = study_methods(topic)
    if args.method:
        chosen = [m for m in methods if m.id == args.method]
        if not chosen:
            raise ValueError(f"{args.method} is not a method of the study (topic.yaml methods)")
    else:
        chosen = [m for m in methods if args.phase in m.phase_ids]
        if len(chosen) != 1:
            names = ", ".join(m.id for m in chosen) or "none of the study's methods"
            raise ValueError(f"phase {args.phase!r} is in {names}: name the method with --method")
    store = Store(topic)
    event = store.set_phase(_author(args, topic), chosen[0], args.phase)
    previous = f" (was {event['previous']})" if event.get("previous") else ""
    print(f"{topic.slug}: {chosen[0].id} at {args.phase}{previous}")
    return 0


def cmd_review_list(args: argparse.Namespace) -> int:
    waiting = proposals(load_topic(args), args.kind)
    for item in waiting:
        print(f"{item.ref}  [{item.provenance}]  {item.summary}")
    print(f"{len(waiting)} proposals wait for the researcher" if waiting else "no proposals wait")
    return 0


def _review(args: argparse.Namespace, verdict: str, changes: dict[str, str] | None = None) -> int:
    topic = load_topic(args)
    author = _author(args, topic)
    for ref in args.refs:
        event = decide(
            topic, author, ref, verdict, reason=getattr(args, "reason", None), note=args.note, changes=changes
        )
        cascade = f" (with {', '.join(event['cascade'])})" if event.get("cascade") else ""
        print(f"{ref}: {event['verdict']}{cascade}")
    return 0


def cmd_review_accept(args: argparse.Namespace) -> int:
    return _review(args, "accept")


def cmd_review_reject(args: argparse.Namespace) -> int:
    return _review(args, "reject")


def cmd_review_edit(args: argparse.Namespace) -> int:
    kind = args.refs[0].split(":", 1)[0]
    type_field = {"code": "code_type", "relation": "relation_type"}.get(kind, "type")
    changes = {
        "label": args.label,
        type_field: args.type,
        "definition": args.definition,
        "broader": args.broader,
        "code": args.code,
        "description": args.description,
    }
    return _review(args, "edit", changes)


def cmd_run_start(args: argparse.Namespace) -> int:
    """The lead analyst hands one piece of work to a subagent (T43, ADR 0014)."""
    topic = load_topic(args)
    author = _author(args, topic)
    event = Store(topic).start_run(author, args.analyst or author.id, args.role, args.input, args.note)
    print(
        f"{event['run']}: {event['analyst']} as {event['role']} ({event['prompt_version']}) on "
        f"{'; '.join(event['input'])}"
    )
    print(f"the subagent writes with: --by {event['analyst']} --run {event['run']}")
    return 0


def cmd_run_list(args: argparse.Namespace) -> int:
    topic = load_topic(args)
    store = Store(topic)
    found = runs(store.history())
    for event in found:
        records = store.run_records(event["run"])
        print(
            f"{event['run']}  {event['at'][:16]}  {event['analyst']} as {event['role']} ({event['prompt_version']}), "
            f"started by {event.get('author', '?')}"
        )
        print(f"    input: {'; '.join(event.get('input') or [])}")
        print(f"    wrote: {', '.join(records) if records else 'nothing in the analysis'}")
    print(f"{len(found)} runs" if found else "no runs")
    return 0


def cmd_role_list(args: argparse.Namespace) -> int:
    """Roles of subagents in the environment (`.agents/roles/`), with the problems of their files."""
    problems = check_roles(args.env)
    if not problems:
        print(f"no roles in {roles_dir(args.env)}")
        return 0
    for name, found in problems.items():
        if found:
            print(f"{name}: {len(found)} problems")
            for problem in found:
                print(f"  - {problem}")
            continue
        r = role_of(args.env, name)
        print(f"{name} ({r.prompt_version}) writes {', '.join(sorted(r.writes)) or 'nothing in the analysis'}")
        print(f"    {r.description}")
    return 1 if any(problems.values()) else 0


def cmd_status(args: argparse.Namespace) -> int:
    print("\n".join(study_status(load_topic(args))))
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
    finalize = source.add_parser(
        "finalize", help="write text.md, the text for the analysis, from the variant chosen in source.yaml (text)"
    )
    finalize.add_argument("topic")
    finalize.add_argument("source")
    finalize.set_defaults(func=cmd_source_finalize)

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
    book = ocr.add_parser("book", help="the whole text of one variant in reading order, into ingest/text/<variant>.md")
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

    images = ocr.add_parser("images", help="page images for a vision model: upright, grayscale, scan-NNNN.jpg")
    images.add_argument("topic")
    images.add_argument("source")
    images.add_argument("--out", type=Path, required=True, help="folder for the images (e.g. scratch/T<n>/img)")
    images.add_argument("--scans", help="only these scans, e.g. 1-3,7")
    images.add_argument("--missing-from", nargs="*", default=[], help="skip scans these variants already have")
    images.add_argument("--size", type=int, default=1600, help="long side in pixels (default 1600)")
    images.set_defaults(func=cmd_ocr_images)
    merge = ocr.add_parser("merge", help="several variants into one, each scan from the first variant that has it")
    merge.add_argument("topic")
    merge.add_argument("source")
    merge.add_argument("--variants", nargs="+", required=True, help="variants in order of preference")
    merge.add_argument("--into", required=True, help="new variant folder under ingest/ocr")
    merge.set_defaults(func=cmd_ocr_merge)

    seg = sub.add_parser("segment", help="cut the final text text.md into segments (paragraphs) again")
    seg.add_argument("topic")
    seg.add_argument("source")
    seg.set_defaults(func=cmd_segment)

    quotes = sub.add_parser("quote", help="quotations: exact words of text.md with their place").add_subparsers(
        dest="action", required=True
    )
    find = quotes.add_parser("find", help="make a quotation from words of a source's text.md (refused if not there)")
    find.add_argument("topic")
    find.add_argument("source")
    find.add_argument("words", help="the exact words, copied from text.md; line breaks may be spaces")
    find.add_argument("--page", type=int, help="printed page the words are on, when they occur more than once")
    find.add_argument("--segment", help="segment id the words are in, when they occur more than once")
    find.add_argument("--format", choices=["yaml", "json"], default="yaml")
    find.set_defaults(func=cmd_quote_find)
    qcheck = quotes.add_parser("check", help="check every quotation of a study; find moved ones again")
    qcheck.add_argument("topic")
    qcheck.add_argument("--update", action="store_true", help="store the new place of moved quotations")
    qcheck.set_defaults(func=cmd_quote_check)

    who = argparse.ArgumentParser(add_help=False)
    who.add_argument("--by", help="who does it: the researcher's id or the exact model id (required to write)")
    who.add_argument("--prompt-version", help="for a model: the skill or prompt it works from and its version")
    who.add_argument("--run", help="a subagent: the run it works in (mmo run start); gives its role and prompt")
    where = argparse.ArgumentParser(add_help=False)
    where.add_argument("--page", type=int, help="printed page, when the words occur more than once")
    where.add_argument("--segment", help="segment id, when the words occur more than once")

    codes = sub.add_parser("code", help="codes and codings: any label, any type (ADR 0013)").add_subparsers(
        dest="action", required=True
    )
    c_add = codes.add_parser("add", parents=[who], help="add a code to the codebook")
    c_add.add_argument("topic")
    c_add.add_argument("label")
    c_add.add_argument("--type", help="any type; the method's vocabulary only orients")
    c_add.add_argument("--method")
    c_add.add_argument("--definition")
    c_add.add_argument("--broader", help="id of a broader code")
    c_add.set_defaults(func=cmd_code_add)
    c_apply = codes.add_parser("apply", parents=[who, where], help="code exact words of a source (a new label adds it)")
    c_apply.add_argument("topic")
    c_apply.add_argument("code", help="code id or label")
    c_apply.add_argument("source")
    c_apply.add_argument("words")
    c_apply.add_argument("--method")
    c_apply.add_argument("--note")
    c_apply.set_defaults(func=cmd_code_apply)
    c_rename = codes.add_parser("rename", parents=[who], help="give a code a new label (its id stays)")
    c_rename.add_argument("topic")
    c_rename.add_argument("code")
    c_rename.add_argument("label")
    c_rename.set_defaults(func=cmd_code_rename)
    c_merge = codes.add_parser("merge", parents=[who], help="merge codes into one; their codings move with them")
    c_merge.add_argument("topic")
    c_merge.add_argument("into")
    c_merge.add_argument("codes", nargs="+")
    c_merge.add_argument("--reason")
    c_merge.set_defaults(func=cmd_code_merge)
    c_split = codes.add_parser("split", parents=[who], help="split a code into new ones; its codings wait for recode")
    c_split.add_argument("topic")
    c_split.add_argument("code")
    c_split.add_argument("labels", nargs="+")
    c_split.add_argument("--reason")
    c_split.set_defaults(func=cmd_code_split)
    c_recode = codes.add_parser("recode", parents=[who], help="give a coding another code")
    c_recode.add_argument("topic")
    c_recode.add_argument("coding")
    c_recode.add_argument("code", help="code id or label (a new label adds it)")
    c_recode.set_defaults(func=cmd_code_recode)
    c_withdraw = codes.add_parser("withdraw", parents=[who], help="take back a coding, code or relation (kept)")
    c_withdraw.add_argument("topic")
    c_withdraw.add_argument("ref", help="coding:<id>, code:<id> or relation:<id>")
    c_withdraw.add_argument("--reason")
    c_withdraw.set_defaults(func=cmd_code_withdraw)
    c_list = codes.add_parser("list", help="the codebook with the number of codings")
    c_list.add_argument("topic")
    c_list.set_defaults(func=cmd_code_list)

    relations = sub.add_parser("relation", help="relations between any two items").add_subparsers(
        dest="action", required=True
    )
    r_add = relations.add_parser(
        "add", parents=[who], help="relate two items: code:, coding:, relation:, memo:, source:"
    )
    r_add.add_argument("topic")
    r_add.add_argument("subject")
    r_add.add_argument("type", help="any type; the method's types only orient")
    r_add.add_argument("object")
    r_add.add_argument("--method")
    r_add.add_argument("--note")
    r_add.add_argument("--evidence", nargs=2, action="append", metavar=("SOURCE[@PAGE]", "WORDS"))
    r_add.set_defaults(func=cmd_relation_add)

    memos = sub.add_parser("memo", help="memos of the study (memos/, format docs/memos.md)").add_subparsers(
        dest="action", required=True
    )
    m_add = memos.add_parser("add", parents=[who], help="write a memo about anything, with quotations as its basis")
    m_add.add_argument("topic")
    m_add.add_argument("--type", required=True, help="e.g. analytic, reflexive, methodological, first-impression")
    m_add.add_argument("--title", required=True)
    m_add.add_argument("--text", help="the memo's text")
    m_add.add_argument("--file", help="read the memo's text from a file")
    m_add.add_argument("--about", action="append", help="code:<id>, coding:<id>, relation:<id>, memo:<id>, source:<id>")
    m_add.add_argument(
        "--quote", nargs=2, action="append", metavar=("SOURCE[@PAGE]", "WORDS"), help="a quotation as basis"
    )
    m_add.add_argument("--method")
    m_add.add_argument("--phase")
    m_add.add_argument("--alternative", action="append", help="an alternative reading (a model offers them)")
    m_add.set_defaults(func=cmd_memo_add)

    analysis = sub.add_parser("analysis", help="the analysis store of a study").add_subparsers(
        dest="action", required=True
    )
    a_check = analysis.add_parser("check", help="integrity: authors, references, quotations, edits made by hand")
    a_check.add_argument("topic")
    a_check.add_argument("--record", action="store_true", help="record edits made by hand in the history")
    a_check.add_argument("--by", help="who made the edits by hand (with --record)")
    a_check.set_defaults(func=cmd_analysis_check)

    methods = sub.add_parser("method", help="method modules of the environment").add_subparsers(
        dest="action", required=True
    )
    m_check = methods.add_parser("check", help="check method.yaml against its schema (methods/README.md)")
    m_check.add_argument("ids", nargs="*", help="method ids (default: every folder)")
    m_check.add_argument("--methods", type=Path, default=Path("methods"), help="the methods folder (default: methods)")
    m_check.set_defaults(func=cmd_method_check)

    phase = sub.add_parser("phase", parents=[who], help="say where the study is in a method's phases (the researcher)")
    phase.add_argument("topic")
    phase.add_argument("phase")
    phase.add_argument("--method", help="needed when several methods of the study have this phase")
    phase.set_defaults(func=cmd_phase)

    run = sub.add_parser("run", help="work handed to a subagent in a role (ADR 0014)").add_subparsers(
        dest="action", required=True
    )
    run_start = run.add_parser("start", parents=[who], help="hand one piece of work to a subagent (the lead)")
    run_start.add_argument("topic")
    run_start.add_argument("--role", required=True, help="a role of .agents/roles/ (mmo role list)")
    run_start.add_argument(
        "--input", action="append", required=True, help="what it works on, e.g. 'kniha pp. 145-160' (repeatable)"
    )
    run_start.add_argument("--analyst", help="the model that does the run (default: --by)")
    run_start.add_argument("--note")
    run_start.set_defaults(func=cmd_run_start)
    run_list = run.add_parser("list", help="the runs of a study and what each wrote")
    run_list.add_argument("topic")
    run_list.set_defaults(func=cmd_run_list)

    roles = sub.add_parser("role", help="roles of subagents (.agents/roles/)").add_subparsers(
        dest="action", required=True
    )
    role_list = roles.add_parser("list", help="the roles, their prompt versions and what they write")
    role_list.add_argument("--env", type=Path, default=Path("."), help="the research environment (default: .)")
    role_list.set_defaults(func=cmd_role_list)

    status = sub.add_parser("status", help="the map of phases, where the study is, what was made, reminders")
    status.add_argument("topic")
    status.set_defaults(func=cmd_status)

    review = sub.add_parser("review", help="proposals of models: list, accept, edit, reject (the researcher)")
    review_sub = review.add_subparsers(dest="action", required=True)
    r_list = review_sub.add_parser("list", help="what waits for the researcher")
    r_list.add_argument("topic")
    r_list.add_argument("--kind", choices=["code", "coding", "relation", "memo"])
    r_list.set_defaults(func=cmd_review_list)
    r_accept = review_sub.add_parser("accept", parents=[who], help="accept proposals as they are")
    r_accept.add_argument("topic")
    r_accept.add_argument("refs", nargs="+", help="code:<id>, coding:<id>, relation:<id>, memo:<id>")
    r_accept.add_argument("--note")
    r_accept.set_defaults(func=cmd_review_accept)
    r_reject = review_sub.add_parser("reject", parents=[who], help="reject proposals, with a reason")
    r_reject.add_argument("topic")
    r_reject.add_argument("refs", nargs="+")
    r_reject.add_argument("--reason", required=True)
    r_reject.add_argument("--note")
    r_reject.set_defaults(func=cmd_review_reject)
    r_edit = review_sub.add_parser("edit", parents=[who], help="accept a proposal with changes (old values kept)")
    r_edit.add_argument("topic")
    r_edit.add_argument("refs", nargs=1, metavar="ref")
    r_edit.add_argument("--label", help="code: a new label")
    r_edit.add_argument("--type", help="code or relation: a new type")
    r_edit.add_argument("--definition", help="code: a definition")
    r_edit.add_argument("--broader", help="code: a broader code")
    r_edit.add_argument("--code", help="coding: another code (id or label)")
    r_edit.add_argument("--description", help="relation: a description")
    r_edit.add_argument("--note", help="what you changed (for a memo edited by hand: required)")
    r_edit.set_defaults(func=cmd_review_edit)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # quotations are pasted from here: never in the console's code page
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (FileNotFoundError, FileExistsError, ValueError, RuntimeError) as err:
        print(f"error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
