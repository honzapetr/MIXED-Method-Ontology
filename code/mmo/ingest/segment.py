"""Segments of the final text `text.md`: its paragraphs, with their place (ADR 0012, docs/source-pipeline.md).

A segment is one paragraph of one place of `text.md` - a place is what follows one location comment such as
`<!-- page 15 (printed) · scan 1 · IMG_1.jpg -->` (a page of a book) or `<!-- file part-1.txt · scan 1 -->` (a text
file). `start`/`end` are character offsets into `text.md` as read with `\\n` line ends, so `text` is exactly
`text.md[start:end]`. Segments are a rebuildable index for reading and counting; what the analysis points to is a
quotation (exact words with their offsets in `text.md`), which may be shorter than a segment or run over several.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n\s*")
# a letter, a hyphen at the end of a line, a letter at the start of the next one: "slo-\nvo" -> "slovo"
HYPHENATED = re.compile(r"([^\W\d_])-[ \t]*\n[ \t]*([^\W\d_])")
SENTENCE_END = re.compile(r"[.!?…:\"“”»)]\s*$")
LOCATION = re.compile(r"^<!-- (?P<body>.+?) -->[ \t]*$", re.MULTILINE)
PAGE = re.compile(r"^page (?P<page>\d+|\?)(?: \((?P<how>[^)]*)\))?$")
SCAN = re.compile(r"^scan (?P<scan>\d+)$")
FILE = re.compile(r"^file (?P<file>.+)$")


@dataclass
class Location:
    """One location comment of `text.md` and the span of text it heads."""

    scan: int  # position of the original file (photo, text file) in file-name order
    page: int | None  # printed page number, None when unknown or the original has no pages
    file: str | None  # the original file, when the comment names it
    start: int  # where the place's text starts in text.md (after the comment)
    end: int  # where it ends (the next comment or the end of the text)


@dataclass
class Segment:
    id: str
    source: str
    scan: int
    page: int | None
    index: int  # paragraph number within the place, from 1
    start: int  # offsets into text.md
    end: int
    text: str  # exactly text.md[start:end]
    continues: bool = False  # the paragraph probably continues in the next place (a page break)


def join_hyphenated(text: str) -> str:
    """Join words hyphenated across a line end; keep the hyphen before a capital ("Rakousko-\\nUhersko")."""

    def join(match: re.Match[str]) -> str:
        left, right = match.group(1), match.group(2)
        return left + right if right.islower() else f"{left}-{right}"

    return HYPHENATED.sub(join, text)


def paragraph_spans(text: str) -> list[tuple[int, int]]:
    """Spans of the paragraphs of `text` (separated by a blank line), without surrounding whitespace."""
    spans: list[tuple[int, int]] = []
    position = 0
    for match in PARAGRAPH_BREAK.finditer(text):
        spans.append((position, match.start()))
        position = match.end()
    spans.append((position, len(text)))
    result = []
    for start, end in spans:
        chunk = text[start:end]
        if not chunk.strip():
            continue
        lead = len(chunk) - len(chunk.lstrip())
        trail = len(chunk) - len(chunk.rstrip())
        result.append((start + lead, end - trail))
    return result


def locations(text: str) -> list[Location]:
    """The places of `text.md` in order; text before the first location comment (header, title) belongs to none."""
    found = list(LOCATION.finditer(text))
    places = []
    for number, match in enumerate(found, start=1):
        scan, page, file = number, None, None
        for part in (p.strip() for p in match.group("body").split("·")):
            if m := SCAN.match(part):
                scan = int(m.group("scan"))
            elif m := PAGE.match(part):
                page = None if m.group("page") == "?" else int(m.group("page"))
            elif m := FILE.match(part):
                file = m.group("file")
        end = found[number].start() if number < len(found) else len(text)
        places.append(Location(scan=scan, page=page, file=file, start=match.end(), end=end))
    return places


def segment_text(source: str, text: str) -> list[Segment]:
    """Segments of a final text: the paragraphs of each place, offsets into `text`."""
    segments: list[Segment] = []
    for place in locations(text):
        body = text[place.start : place.end]
        spans = paragraph_spans(body)
        for index, (start, end) in enumerate(spans, start=1):
            segments.append(
                Segment(
                    id=f"{source}:s{place.scan}:{index}",
                    source=source,
                    scan=place.scan,
                    page=place.page,
                    index=index,
                    start=place.start + start,
                    end=place.start + end,
                    text=body[start:end],
                )
            )
        if spans and not SENTENCE_END.search(segments[-1].text):
            segments[-1].continues = True
    return segments


def stale_segments(text: str, segments: list[dict]) -> list[str]:
    """Ids of segments whose words are no longer at their offsets in `text` (text.md changed after segmenting)."""
    return [s["id"] for s in segments if text[s["start"] : s["end"]] != s["text"]]


def read_segments(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(segments: list[Segment], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for segment in segments:
            handle.write(json.dumps(asdict(segment), ensure_ascii=False) + "\n")
