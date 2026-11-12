"""Split OCR page text into segments with exact positions.

A segment is one paragraph of one page. `start`/`end` are character offsets into that scan's OCR text (the record in
`sources/<source>/ingest/ocr/<variant>/scan-NNNN.json`), so every segment can be traced back to the image; `page` is the
printed page number from the reading order (for quoting), when known. `text` is
the paragraph cleaned for analysis: words hyphenated across line ends are joined and lines are joined with spaces.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

PARAGRAPH_BREAK = re.compile(r"\n[ \t]*\n\s*")
# a letter, a hyphen at the end of a line, a letter at the start of the next one: "slo-\nvo" -> "slovo"
HYPHENATED = re.compile(r"([^\W\d_])-[ \t]*\n[ \t]*([^\W\d_])")
SENTENCE_END = re.compile(r"[.!?…:\"“”»)]\s*$")


@dataclass
class Segment:
    id: str
    source: str
    scan: int  # the image the text was read from (file-name order)
    page: int | None  # printed page number, None when the reading order does not know it
    index: int  # paragraph number on the page, from 1
    start: int
    end: int
    text: str
    backend: str
    continues: bool = False  # the paragraph probably continues on the next page


def _join_hyphenated(match: re.Match[str]) -> str:
    left, right = match.group(1), match.group(2)
    # a lowercase continuation is a word split by hyphenation; otherwise keep the hyphen ("Rakousko-\nUhersko")
    return left + right if right.islower() else f"{left}-{right}"


def clean(paragraph: str) -> str:
    joined = HYPHENATED.sub(_join_hyphenated, paragraph)
    return re.sub(r"\s*\n\s*", " ", joined).strip()


def paragraph_spans(text: str) -> list[tuple[int, int]]:
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


def segment_page(source: str, scan: int, text: str, backend: str, page: int | None = None) -> list[Segment]:
    segments = []
    for index, (start, end) in enumerate(paragraph_spans(text), start=1):
        segments.append(
            Segment(
                id=f"{source}:s{scan}:{index}",
                source=source,
                scan=scan,
                page=page,
                index=index,
                start=start,
                end=end,
                text=clean(text[start:end]),
                backend=backend,
            )
        )
    if segments and not SENTENCE_END.search(segments[-1].text):
        segments[-1].continues = True
    return segments


def segment_records(records: Iterable[dict], printed: Mapping[int, int | None] | None = None) -> list[Segment]:
    """Segments of OCR records (one per scan, as written by `run_ocr`); `printed` = scan -> printed page number."""
    segments: list[Segment] = []
    for record in records:
        page = (printed or {}).get(record["scan"])
        segments.extend(segment_page(record["source"], record["scan"], record["text"], record["backend"], page))
    return segments


def write_jsonl(segments: list[Segment], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for segment in segments:
            handle.write(json.dumps(asdict(segment), ensure_ascii=False) + "\n")
