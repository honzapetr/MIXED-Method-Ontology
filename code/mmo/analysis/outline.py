"""The outline of a source and the coverage of its parts (T36, ADR 0014).

* The **outline** is read from the headings of `text.md`, without a model: each heading starts a part that runs to
  the next heading, with its pages and segments. The **chapters** are the researcher's: `outline.chapters` of
  `source.yaml` names each chapter (`id`, `title`) and its first part (`first`: a heading's text or a part id), and
  the chapter runs to the next one. Without them the outline has parts only. A part without a heading (notes, a
  bibliography, a chapter whose title page is missing) is the researcher's too: `outline.parts` gives its `id`,
  `title` and `at` - the exact words it starts with, found once in `text.md`; the part starts at their line. Parts
  from headings are numbered `part-01`, `part-02`, ... in the order of the headings, so a declared part does not
  renumber them.
* **Coverage** says how each part was read: `whole`, in `passages`, or only through a `map` - declared by the reader
  (`op: coverage`, with its author and run), and `quoted` where a coding or a memo quotes the part. `mmo` cannot see
  what a model read; the declaration is the reader's, kept with its author, and the critic can test it.

`mmo` records and shows; whether a part needs reading whole is the researcher's and the method's.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import yaml

from mmo.analysis.quote import FRONT_MATTER, quotations_in, read_final_text, text_sha256
from mmo.analysis.store import Author, Store, StoreError
from mmo.core.topic import ROLE_CONTEXT, Source, Topic

HEADING = re.compile(r"(?m)^(#{1,6})[ \t]+(.+?)[ \t#]*$")
HOW = ("whole", "passages", "map")
RANK = {"whole": 4, "passages": 3, "map": 2, "quoted": 1}  # a quotation shows a part was used, not how it was read
RANGE = re.compile(r"^(part-\d+)\.\.(part-\d+)$")


@dataclass
class Part:
    id: str
    level: int
    title: str
    start: int
    end: int
    segments: list[str] = field(default_factory=list)
    pages: list[int] = field(default_factory=list)
    chapter: str | None = None


@dataclass
class Chapter:
    id: str
    title: str
    parts: list[str]
    pages: list[int]


@dataclass
class Outline:
    source: str
    parts: list[Part]
    chapters: list[Chapter]
    problems: list[str]
    text_sha256: str

    def part(self, part_id: str) -> Part:
        for part in self.parts:
            if part.id == part_id:
                return part
        raise StoreError(f"{self.source} has no {part_id} (mmo outline)")

    def part_at(self, offset: int) -> Part | None:
        for part in self.parts:
            if part.start <= offset < part.end:
                return part
        return None


def pages_label(pages: list[int]) -> str:
    if not pages:
        return "pp. ?"
    return f"p. {pages[0]}" if pages[0] == pages[-1] else f"pp. {pages[0]}-{pages[-1]}"


def _segments(source: Source) -> list[dict[str, Any]]:
    if not source.segments_file.is_file():
        return []
    rows = []
    for line in source.segments_file.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def outline(topic: Topic, source_id: str) -> Outline:
    """The parts of `text.md` from its headings, with the researcher's chapters (`outline.chapters`)."""
    source = topic.source(source_id)
    text = read_final_text(source)
    match = FRONT_MATTER.match(text)
    body_start = match.end() if match else 0
    heads = [m for m in HEADING.finditer(text) if m.start() >= body_start]
    starts = [
        (head.start(), f"part-{n:02d}", len(head.group(1)), head.group(2).strip())
        for n, head in enumerate(heads, start=1)
    ]
    declared, problems = _declared_parts(source, text, body_start, {s[1] for s in starts})
    starts = sorted(starts + declared)
    parts = []
    for k, (start, part_id, level, title) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(text)
        parts.append(Part(part_id, level, title, start, end))
    segments = _segments(source)
    for part in parts:
        inside = [s for s in segments if part.start <= int(s.get("start", -1)) < part.end]
        part.segments = [str(s["id"]) for s in inside]
        part.pages = sorted({int(s["page"]) for s in inside if s.get("page") is not None})
    chapters, chapter_problems = _chapters(source, parts)
    return Outline(source_id, parts, chapters, problems + chapter_problems, text_sha256(text))


def _declared_parts(
    source: Source, text: str, body_start: int, taken: set[str]
) -> tuple[list[tuple[int, str, int, str]], list[str]]:
    """Parts without a heading that the researcher declared (`outline.parts`: id, title, at)."""
    declared = (source.metadata().get("outline") or {}).get("parts") or []
    if not isinstance(declared, list):
        return [], ["outline.parts: a list of {id, title, at}"]
    found: list[tuple[int, str, int, str]] = []
    problems: list[str] = []
    for n, item in enumerate(declared, start=1):
        if not isinstance(item, dict) or not item.get("id") or not item.get("at"):
            problems.append(f"outline.parts[{n}]: needs id, title and at (the exact words the part starts with)")
            continue
        part_id, words = str(item["id"]), str(item["at"])
        if part_id in taken or re.fullmatch(r"part-\d+", part_id):
            problems.append(f"outline.parts: {part_id} is taken (part-NN are the parts from headings)")
            continue
        hits = [m.start() for m in re.finditer(re.escape(words), text) if m.start() >= body_start]
        if len(hits) != 1:
            problems.append(f"outline.parts: {part_id} - {words!r} is found {len(hits)} times in text.md, not once")
            continue
        taken.add(part_id)
        line_start = text.rfind("\n", 0, hits[0]) + 1
        found.append((line_start, part_id, 0, str(item.get("title") or part_id)))
    return found, problems


def _chapters(source: Source, parts: list[Part]) -> tuple[list[Chapter], list[str]]:
    declared = (source.metadata().get("outline") or {}).get("chapters") or []
    problems: list[str] = []
    if not isinstance(declared, list):
        return [], ["outline.chapters: a list of {id, title, first}"]
    starts: list[tuple[int, str, str]] = []
    seen: set[str] = set()
    for n, item in enumerate(declared, start=1):
        if not isinstance(item, dict) or not item.get("id") or not item.get("first"):
            problems.append(f"outline.chapters[{n}]: needs id, title and first (a heading or a part id)")
            continue
        chapter_id, first = str(item["id"]), str(item["first"]).strip()
        if chapter_id in seen:
            problems.append(f"outline.chapters: {chapter_id} twice")
            continue
        seen.add(chapter_id)
        index = next((i for i, p in enumerate(parts) if first in (p.id, p.title)), None)
        if index is None:
            problems.append(f"outline.chapters: {chapter_id} starts at {first!r}, which is no heading of text.md")
            continue
        if starts and index <= starts[-1][0]:
            problems.append(f"outline.chapters: {chapter_id} starts before or with the chapter above it")
            continue
        starts.append((index, chapter_id, str(item.get("title") or chapter_id)))
    chapters = []
    for k, (index, chapter_id, title) in enumerate(starts):
        stop = starts[k + 1][0] if k + 1 < len(starts) else len(parts)
        members = parts[index:stop]
        for part in members:
            part.chapter = chapter_id
        pages = sorted({page for part in members for page in part.pages})
        chapters.append(Chapter(chapter_id, title, [p.id for p in members], pages))
    return chapters, problems


def resolve(found: Outline, refs: list[str]) -> list[str]:
    """Part ids from part ids, chapter ids and ranges `part-03..part-07`, in the order of the text."""
    ids: list[str] = []
    order = [p.id for p in found.parts]
    for ref in refs:
        chapter = next((c for c in found.chapters if c.id == ref), None)
        if chapter:
            ids += chapter.parts
        elif m := RANGE.match(ref):
            first, last = found.part(m.group(1)).id, found.part(m.group(2)).id
            if order.index(first) > order.index(last):
                raise StoreError(f"{ref}: the range runs backwards")
            ids += order[order.index(first) : order.index(last) + 1]
        else:
            ids.append(found.part(ref).id)
    return [p for p in order if p in set(ids)]


# ---------------------------------------------------------------- coverage


def add_coverage(
    store: Store, author: Author, source_id: str, refs: list[str], how: str, note: str | None = None
) -> dict[str, Any]:
    """The reader says how it read these parts (`op: coverage`)."""
    if how not in HOW:
        raise StoreError(f"--how is one of {', '.join(HOW)}")
    if not refs:
        raise StoreError("which parts? give --part (a part id, a chapter id or part-03..part-07; mmo outline)")
    found = outline(store.topic, source_id)
    parts = resolve(found, refs)
    return store.save(
        author,
        "coverage",
        source=source_id,
        parts=parts,
        how=how,
        text_sha256=found.text_sha256,
        **({"note": note} if note else {}),
    )


def _reader(record: dict[str, Any]) -> str:
    made = record.get("generated_by") or {}
    who = str(record.get("author") or "?")
    if made.get("run"):
        return f"{who} ({made.get('role') or 'run'} {made['run']})"
    return who


def _quoting_records(topic: Topic, store: Store) -> list[dict[str, Any]]:
    records = list(store.codings)
    for path in sorted((topic.root / "memos").glob("*.md")):
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if match:
            records.append(yaml.safe_load(match.group(1)) or {})
    return [r for r in records if r.get("status") not in ("rejected", "withdrawn")]


def coverage(topic: Topic, source_id: str, store: Store | None = None) -> tuple[Outline, dict[str, list[dict]]]:
    """Part id -> how it was read: `{how, by, at, stale}` from declarations and `quoted` from quotations."""
    store = store or Store(topic)
    found = outline(topic, source_id)
    by_part: dict[str, list[dict]] = {p.id: [] for p in found.parts}
    for event in store.history():
        if event.get("op") != "coverage" or event.get("source") != source_id:
            continue
        stale = event.get("text_sha256") != found.text_sha256
        for part_id in event.get("parts") or []:
            if part_id in by_part:
                by_part[part_id].append(
                    {"how": event["how"], "by": _reader(event), "at": str(event.get("at", ""))[:10], "stale": stale}
                )
    for record in _quoting_records(topic, store):
        quoted = set()
        for quotation in quotations_in(record):
            if quotation.get("source") == source_id and (part := found.part_at(int(quotation["start"]))):
                quoted.add(part.id)
        for part_id in quoted:
            entry = {"how": "quoted", "by": _reader(record), "at": "", "stale": False}
            if entry not in by_part[part_id]:
                by_part[part_id].append(entry)
    return found, by_part


def best(entries: list[dict]) -> str:
    fresh = [e for e in entries if not e["stale"]]
    return max((e["how"] for e in fresh), key=lambda h: RANK[h], default="nobody")


def summary(topic: Topic, store: Store | None = None) -> list[str]:
    """Lines for `mmo status`: the coverage of each studied source with a final text."""
    lines: list[str] = []
    store = store or Store(topic)
    for source in topic.sources():
        if source.metadata().get("role") == ROLE_CONTEXT or not source.final_text_file.is_file():
            continue
        found, by_part = coverage(topic, source.id, store)
        if not found.parts:
            lines.append(f"coverage of {source.id}: text.md has no headings, so no parts (mmo outline)")
            continue
        levels = {p.id: best(by_part[p.id]) for p in found.parts}
        counts = {h: sum(1 for v in levels.values() if v == h) for h in (*RANK, "nobody")}
        lines.append(
            f"coverage of {source.id} ({len(found.parts)} parts; quoted = only quoted, no reading declared): "
            + ", ".join(f"{h} {counts[h]}" for h in ("whole", "passages", "map", "quoted", "nobody"))
        )
        for chapter in found.chapters:
            got = [levels[p] for p in chapter.parts]
            weakest = min(got, key=lambda h: RANK.get(h, 0))
            lines.append(
                f"    {chapter.id} {chapter.title} ({pages_label(chapter.pages)}): "
                + ("read whole" if weakest == "whole" else f"weakest part {weakest}")
                + ("" if weakest == "whole" else f" - {sum(1 for g in got if g == 'whole')}/{len(got)} parts whole")
            )
        gaps = [p for p in found.parts if levels[p.id] in ("map", "nobody") and p.chapter is None]
        if gaps:
            shown = ", ".join(f"{p.id} {p.title} ({levels[p.id]})" for p in gaps[:8])
            lines.append(f"    parts known only through a map or by nobody: {shown}{' ...' if len(gaps) > 8 else ''}")
        stale = sorted({p for p, entries in by_part.items() if any(e["stale"] for e in entries)})
        if stale:
            lines.append(f"    declared on an earlier text.md (not counted): {', '.join(stale)}")
    return lines
