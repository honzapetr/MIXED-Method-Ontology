"""Quotations: the exact words of a passage of `text.md` with their place (ADR 0012, docs/source-pipeline.md step 7).

A quotation is created only from words that are in the final text: the analyst gives the words (and a hint where),
the program finds them and fills the offsets, pages and scans. The words are compared on a *view* of the text in
which location comments are left out and every run of whitespace counts as one space, so a quotation may run over a
page break and a line break may be quoted as a space; letters, punctuation and `[?]` are compared exactly.

A quotation keeps a little of the words around it (`prefix`, `suffix`, W3C TextQuoteSelector), so when `text.md` is
rebuilt and the words move, they are found again in the right place; words that are gone are reported, never
silently dropped or moved.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from mmo.core.topic import Source, Topic
from mmo.ingest.segment import LOCATION, Location, locations, segment_text

CONTEXT = 32  # characters of the view kept before and after the words (prefix, suffix)
WHITESPACE = re.compile(r"\s+")
FRONT_MATTER = re.compile(r"\A---[ \t]*\n(.*?\n)---[ \t]*(\n|\Z)", re.DOTALL)
SKIPPED_DIRS = {"sources", "work", ".git"}  # not analytic files: the sources' own data, machine work
ANALYTIC_SUFFIXES = {".yaml", ".yml", ".json", ".jsonl", ".md"}

OK, MOVED, GONE, AMBIGUOUS, NO_TEXT = "ok", "moved", "gone", "ambiguous", "no text"


class QuoteError(ValueError):
    """The words cannot become a quotation (not in the text, or not only once)."""


def normalize(words: str) -> str:
    return WHITESPACE.sub(" ", words).strip()


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class Quotation:
    """One quotation; field names are the slots of the ontology class `Quotation`."""

    source: str
    start: int  # offsets into text.md (read with `\n` line ends), as for segments
    end: int
    pages: list[int]  # printed pages the words run over, for citing
    scans: list[int]  # the originals (photos, files) the words run over
    exact: str  # the words, whitespace as one space, location comments left out
    prefix: str  # words before and after in the same view, to find the quotation again
    suffix: str
    text_sha256: str  # which text.md it was taken from

    def record(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "start": self.start,
            "end": self.end,
            "pages": self.pages,
            "scans": self.scans,
            "exact": self.exact,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "text_sha256": self.text_sha256,
        }


@dataclass
class View:
    """The places of `text.md` as one string for comparing words, with the offset in `text.md` of each character."""

    text: str
    places: list[Location]
    chars: str
    offsets: list[int]


def view_of(text: str) -> View:
    places = locations(text)
    spans = [(p.start, p.end) for p in places] or [(0, len(text))]
    chars: list[str] = []
    offsets: list[int] = []
    for start, end in spans:
        for i in range(start, end):
            c = text[i]
            if c.isspace():
                if chars and chars[-1] != " ":
                    chars.append(" ")
                    offsets.append(i)
            else:
                chars.append(c)
                offsets.append(i)
        if chars and chars[-1] != " ":  # a place ends: the comment between places counts as a space
            chars.append(" ")
            offsets.append(end)
    return View(text=text, places=places, chars="".join(chars), offsets=offsets)


def words_at(text: str, start: int, end: int) -> str:
    """The words of `text.md` between two offsets, as the view sees them."""
    return normalize(LOCATION.sub(" ", text[start:end]))


def occurrences(view: View, words: str) -> list[int]:
    """Positions in the view where `words` (normalized) begin."""
    found, at = [], view.chars.find(words)
    while at != -1:
        found.append(at)
        at = view.chars.find(words, at + 1)
    return found


def _place(view: View, start: int, end: int) -> tuple[list[int], list[int]]:
    crossed = [p for p in view.places if p.start < end and p.end > start]
    pages = list(dict.fromkeys(p.page for p in crossed if p.page is not None))
    scans = list(dict.fromkeys(p.scan for p in crossed))
    return pages, scans


def quotation_at(view: View, source: str, at: int, words: str) -> Quotation:
    start = view.offsets[at]
    end = view.offsets[at + len(words) - 1] + 1
    pages, scans = _place(view, start, end)
    return Quotation(
        source=source,
        start=start,
        end=end,
        pages=pages,
        scans=scans,
        exact=words,
        prefix=view.chars[max(0, at - CONTEXT) : at],
        suffix=view.chars[at + len(words) : at + len(words) + CONTEXT],
        text_sha256=text_sha256(view.text),
    )


def find_quotation(
    source_id: str, text: str, words: str, page: int | None = None, segment: str | None = None
) -> Quotation:
    """The quotation of `words` in `text`; refused when they are not there, or there more than once without a hint."""
    exact = normalize(words)
    if not exact:
        raise QuoteError("no words given")
    view = view_of(text)
    hits = [quotation_at(view, source_id, at, exact) for at in occurrences(view, exact)]
    if not hits:
        raise QuoteError(f"not in the final text of {source_id}: {exact!r} (copy the words from text.md)")
    everywhere = hits
    if page is not None:
        hits = [q for q in hits if page in q.pages]
    if segment is not None:
        spans = {s.id: (s.start, s.end) for s in segment_text(source_id, text)}
        if segment not in spans:
            raise QuoteError(f"no segment {segment} in {source_id} (see segments.jsonl)")
        s_start, s_end = spans[segment]
        hits = [q for q in hits if q.start < s_end and q.end > s_start]
    if not hits:
        raise QuoteError(f"found {len(everywhere)} times, but not at the place given: pages {_pages_of(everywhere)}")
    if len(hits) > 1:
        raise QuoteError(f"found {len(hits)} times (pages {_pages_of(hits)}): give --page or --segment, or more words")
    return hits[0]


def _pages_of(hits: list[Quotation], shown: int = 12) -> str:
    places = list(dict.fromkeys("/".join(str(p) for p in q.pages) or f"scan {q.scans[0]}" for q in hits))
    more = f" and {len(places) - shown} more" if len(places) > shown else ""
    return ", ".join(places[:shown]) + more


def quote(source: Source, words: str, page: int | None = None, segment: str | None = None) -> Quotation:
    return find_quotation(source.id, read_final_text(source), words, page, segment)


def read_final_text(source: Source) -> str:
    if not source.final_text_file.is_file():
        raise FileNotFoundError(f"no final text yet: {source.final_text_file}")
    return source.final_text_file.read_text(encoding="utf-8")


# ---------------------------------------------------------------- checking stored quotations


@dataclass
class Checked:
    path: Path
    record: dict[str, Any]
    status: str
    new: Quotation | None = None  # where the words are now, for a moved quotation
    note: str = ""


def check_record(record: dict[str, Any], text: str) -> Checked:
    exact = normalize(str(record.get("exact", "")))
    start, end = record.get("start"), record.get("end")
    found = Checked(path=Path(), record=record, status=OK)
    if isinstance(start, int) and isinstance(end, int) and exact and words_at(text, start, end) == exact:
        return found
    view = view_of(text)
    hits = occurrences(view, exact) if exact else []
    if len(hits) > 1:  # the words around them decide; if they changed too, the researcher does
        prefix, suffix = str(record.get("prefix", "")), str(record.get("suffix", ""))
        hits = [
            at for at in hits if view.chars[:at].endswith(prefix) and view.chars[at + len(exact) :].startswith(suffix)
        ] or hits
    if not hits:
        found.status, found.note = GONE, "the words are no longer in text.md"
    elif len(hits) > 1:
        found.status, found.note = AMBIGUOUS, f"the words are in text.md {len(hits)} times"
    else:
        found.status = MOVED
        found.new = quotation_at(view, str(record.get("source")), hits[0], exact)
    return found


def is_quotation(value: Any) -> bool:
    return isinstance(value, dict) and "source" in value and "exact" in value and "start" in value


def quotations_in(data: Any) -> Iterator[dict[str, Any]]:
    """Every quotation record anywhere in loaded YAML or JSON data (a mapping with source, exact, start)."""
    if is_quotation(data):
        yield data
    elif isinstance(data, dict):
        for value in data.values():
            yield from quotations_in(value)
    elif isinstance(data, list):
        for value in data:
            yield from quotations_in(value)


@dataclass
class AnalyticFile:
    """An analytic file of a study, loaded so that its quotations can be updated in place and written back."""

    path: Path
    kind: str  # yaml, json, jsonl, md (YAML front matter)
    data: Any
    body: str = ""  # Markdown after the front matter
    quotations: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> AnalyticFile | None:
        text = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()
        if suffix in (".yaml", ".yml"):
            item = cls(path, "yaml", yaml.safe_load(text))
        elif suffix == ".json":
            item = cls(path, "json", json.loads(text))
        elif suffix == ".jsonl":
            item = cls(path, "jsonl", [json.loads(line) for line in text.splitlines() if line.strip()])
        else:
            match = FRONT_MATTER.match(text)
            if not match:
                return None
            item = cls(path, "md", yaml.safe_load(match.group(1)), body=text[match.end() :])
        item.quotations = list(quotations_in(item.data))
        return item

    def write(self) -> None:
        if self.kind == "yaml":
            out = yaml.safe_dump(self.data, allow_unicode=True, sort_keys=False)
        elif self.kind == "json":
            out = json.dumps(self.data, ensure_ascii=False, indent=2) + "\n"
        elif self.kind == "jsonl":
            out = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in self.data)
        else:
            out = "---\n" + yaml.safe_dump(self.data, allow_unicode=True, sort_keys=False) + "---\n" + self.body
        self.path.write_text(out, encoding="utf-8", newline="\n")


def analytic_files(root: Path) -> Iterator[Path]:
    """Files of a study that may hold quotations: everything but the sources' own data and machine work."""
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).parts
        if (rel and rel[0] in SKIPPED_DIRS) or path.name == "topic.yaml":
            continue
        if not path.is_file() or path.suffix.lower() not in ANALYTIC_SUFFIXES:
            continue
        yield path


def check_study(topic: Topic, update: bool = False) -> list[Checked]:
    """Check every quotation in the analytic files of a study; with `update`, write the new place of moved ones."""
    texts: dict[str, str | None] = {}
    results: list[Checked] = []
    for path in analytic_files(topic.root):
        try:
            item = AnalyticFile.load(path)
        except (yaml.YAMLError, json.JSONDecodeError) as err:
            results.append(Checked(path, {}, GONE, note=f"cannot be read: {err}"))
            continue
        if item is None or not item.quotations:
            continue
        changed = False
        for record in item.quotations:
            source_id = str(record.get("source"))
            if source_id not in texts:
                file = topic.source(source_id).final_text_file
                texts[source_id] = file.read_text(encoding="utf-8") if file.is_file() else None
            text = texts[source_id]
            if text is None:
                results.append(Checked(path, record, NO_TEXT, note=f"no text.md for the source {source_id}"))
                continue
            checked = check_record(record, text)
            checked.path = path
            if checked.status == OK and record.get("text_sha256") != text_sha256(text) and update:
                record["text_sha256"] = text_sha256(text)
                changed = True
            if checked.status == MOVED and update and checked.new is not None:
                record.update(checked.new.record())
                changed = True
            results.append(checked)
        if changed:
            item.write()
    return results
