"""Move a topic from the layout by processing step (T1-T2a) to the source-centric layout (ADR 0006).

Old layout:  sources/<id>/{source.yaml with `pages`, images}, work/ocr/<variant>/<id>/page-NNNN.json,
work/numbers/<id>.json, work/order/<variant>/<id>.yaml, work/text/<variant>/<id>.md, work/segments/<id>.jsonl,
ground-truth/<id>/page-NNNN.txt.

Files are moved, not copied. OCR records only get the key `page` renamed to `scan`; their text, hashes, timing and
provenance stay as they were. Old segments are removed, not moved: segments are cut from `text.md` now (ADR
0012). Image hashes are taken from the old `source.yaml`, so the migration works where the
images are not present (they are git-ignored). Running it again changes nothing.
"""

from __future__ import annotations

import json
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from mmo.core.topic import NOTES_TEMPLATE, Source, Topic, read_yaml, write_yaml

OCR_RECORD = "page-*.json"


def rename_key(record: dict[str, Any], old: str, new: str) -> dict[str, Any]:
    """The same record with one key renamed in place (the order of keys is kept)."""
    return {new if key == old else key: value for key, value in record.items()}


def _move(src: Path, dst: Path, log: Callable[[str], None]) -> None:
    if dst.exists():
        raise FileExistsError(f"both the old and the new file exist, resolve by hand: {src} -> {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    log(f"moved {src} -> {dst}")


def _remove_if_empty(folder: Path) -> None:
    """Remove a folder of the old layout bottom-up when only empty folders and `.gitkeep` files are left."""
    if not folder.is_dir():
        return
    for child in sorted(folder.iterdir()):
        if child.is_dir():
            _remove_if_empty(child)
    if all(child.name == ".gitkeep" for child in folder.iterdir()):
        for child in folder.iterdir():
            child.unlink()
        folder.rmdir()


def _migrate_ocr_record(src: Path, dst_dir: Path, log: Callable[[str], None]) -> None:
    raw = src.read_text(encoding="utf-8")
    record = json.loads(raw)
    if "scan" not in record:
        record = rename_key(record, "page", "scan")
    dst = dst_dir / f"scan-{int(record['scan']):04d}.json"
    if dst.exists():
        raise FileExistsError(f"both the old and the new file exist, resolve by hand: {src} -> {dst}")
    dst_dir.mkdir(parents=True, exist_ok=True)
    indent = 2 if raw.lstrip().startswith("{\n") else None  # keep how the record was written
    dst.write_text(
        json.dumps(record, ensure_ascii=False, indent=indent) + ("\n" if raw.endswith("\n") else ""), "utf-8"
    )
    src.unlink()
    log(f"moved {src} -> {dst}")


def _drop_old_segments(src: Path, source: Source, log: Callable[[str], None]) -> None:
    """Old segments pointed into one scan's OCR text; segments are now cut from `text.md` (ADR 0012)."""
    src.unlink()
    log(f"removed {src}: old segments of an OCR variant; mmo source finalize cuts {source.segments_file}")


def _migrate_source(topic: Topic, source: Source, log: Callable[[str], None]) -> None:
    work = topic.root / "work"
    meta = source.metadata()
    # originals: every file directly in the source folder except what the researcher writes
    for path in sorted(source.root.iterdir()):
        if path.is_file() and path.name not in {"source.yaml", "notes.md", ".gitkeep"}:
            _move(path, source.files_dir / path.name, log)
    # image hashes: from source.yaml to ingest/files.yaml
    if "pages" in meta:
        files = [{"scan": e["page"], "file": e["file"], "sha256": e["sha256"]} for e in meta.pop("pages") or []]
        write_yaml(source.files_manifest, {"source": source.id, "files": files})
        write_yaml(source.metadata_file, meta)
        log(f"{len(files)} file hashes moved to {source.files_manifest}")
    if not source.notes_file.exists():
        source.notes_file.write_text(NOTES_TEMPLATE.format(title=meta.get("title") or source.id), encoding="utf-8")
    ocr = work / "ocr"
    if ocr.is_dir():
        for variant_dir in sorted(p for p in ocr.iterdir() if p.is_dir()):
            old = variant_dir / source.id
            for record in sorted(old.glob(OCR_RECORD)) if old.is_dir() else []:
                _migrate_ocr_record(record, source.ocr_dir(variant_dir.name), log)
    numbers = work / "numbers" / f"{source.id}.json"
    if numbers.is_file():
        _move(numbers, source.numbers_file, log)
    for kind, target in (("order", source.order_file), ("text", source.text_file)):
        base = work / kind
        suffix = ".yaml" if kind == "order" else ".md"
        if base.is_dir():
            for variant_dir in sorted(p for p in base.iterdir() if p.is_dir()):
                old = variant_dir / f"{source.id}{suffix}"
                if old.is_file():
                    _move(old, target(variant_dir.name), log)
    segments = work / "segments" / f"{source.id}.jsonl"
    if segments.is_file():
        _drop_old_segments(segments, source, log)
    truth = topic.root / "ground-truth" / source.id
    if truth.is_dir():
        for page in sorted(truth.glob("page-*.txt")):
            _move(page, source.ground_truth_dir / f"scan-{int(page.stem.split('-')[1]):04d}.txt", log)


def migrate_topic(topic: Topic, log: Callable[[str], None] = print) -> None:
    """Move every source of an old-layout topic into the source-centric layout; idempotent."""
    for source in topic.sources():
        _migrate_source(topic, source, log)
        topic.register_source(source.id)
    for old in ("work", "ground-truth"):
        try:
            _remove_if_empty(topic.root / old)
        except OSError as err:  # a synced drive (Google Drive) may keep a just-emptied folder a while
            log(f"could not remove the empty folder {topic.root / old}: {err}")
    leftovers = _old_files(topic)
    if leftovers:
        log(f"left in place (not part of a known source): {', '.join(str(p) for p in leftovers)}")
    for folder in ("memos", "graph", "sources"):
        (topic.root / folder).mkdir(exist_ok=True)
        if not any((topic.root / folder).iterdir()):
            (topic.root / folder / ".gitkeep").touch()


def _old_files(topic: Topic) -> list[Path]:
    """Files still in the folders of the old layout (`.gitkeep` and empty folders do not count)."""
    found: list[Path] = []
    for old in ("work", "ground-truth"):
        folder = topic.root / old
        if folder.is_dir():
            found.extend(p for p in folder.rglob("*") if p.is_file() and p.name != ".gitkeep")
    return sorted(found)


def needs_migration(topic: Topic) -> bool:
    if _old_files(topic):
        return True
    return any("pages" in read_yaml(s.metadata_file) for s in topic.sources())
