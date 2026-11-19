"""Page furniture: running heads and printed page numbers are not content (T25, docs/source-pipeline.md step 4).

A book repeats its title or the chapter's title at the top of a page (running head) and prints the page number at
the head or foot. Read page by page, both end up in the text: they become segments of their own and stand before
the first paragraph of a page. When the final text is written they are left out; the page number stays in the
location comment, and every line left out is listed in `ingest/furniture/<variant>.yaml` for review.

Rules, on the text of each page (photos and scanned pages only; text files have no furniture):
- **page number** - the first or the last non-empty line is only a number (`PAGE_NUMBER_LINE`) equal to the page's
  printed number in the reading order; a page without a known number keeps such a line;
- **running head** - the first non-empty line, not a Markdown heading, at most `MAX_HEAD` characters, that is the
  first line of at least `MIN_REPEATS` pages of the variant, or nearly the same as such a line (a misreading,
  `SIMILAR`). A real chapter title occurs once and stays.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

import yaml

from mmo.ingest.order import HOW_TEXT, PAGE_NUMBER_LINE, ReadingOrder

MIN_REPEATS = 3
MAX_HEAD = 80
SIMILAR = 0.9
RUNNING_HEAD, PAGE_NUMBER = "running head", "page number"


@dataclass
class Furniture:
    scan: int
    page: int | None
    kind: str
    line: str


def _nonempty(text: str) -> list[int]:
    return [i for i, line in enumerate(text.split("\n")) if line.strip()]


def _first_line(text: str) -> str | None:
    lines = text.split("\n")
    found = _nonempty(text)
    return lines[found[0]].strip() if found else None


def running_heads(texts: list[str]) -> set[str]:
    """Lines that open at least MIN_REPEATS pages: the running heads of the variant."""
    counts = Counter(line for t in texts if (line := _first_line(t)) and _head_candidate(line))
    return {line for line, n in counts.items() if n >= MIN_REPEATS}


def _head_candidate(line: str) -> bool:
    return not line.startswith("#") and len(line) <= MAX_HEAD


def _is_head(line: str, heads: set[str]) -> bool:
    if not _head_candidate(line):
        return False
    return line in heads or any(SequenceMatcher(None, line, head).ratio() >= SIMILAR for head in heads)


def _is_number(line: str, printed: int | None) -> bool:
    match = PAGE_NUMBER_LINE.match(line)
    return printed is not None and match is not None and int(match.group(1)) == printed


def strip_page(text: str, scan: int, printed: int | None, heads: set[str]) -> tuple[str, list[Furniture]]:
    """The page's text without its furniture, and what was left out."""
    lines = text.split("\n")
    removed: list[Furniture] = []
    drop: set[int] = set()
    found = _nonempty(text)
    if not found:
        return text, removed
    first, last = found[0], found[-1]
    if _is_number(lines[first].strip(), printed):
        drop.add(first)
        removed.append(Furniture(scan, printed, PAGE_NUMBER, lines[first].strip()))
        rest = [i for i in found if i != first]
        first = rest[0] if rest else None
    if first is not None and _is_head(lines[first].strip(), heads):
        drop.add(first)
        removed.append(Furniture(scan, printed, RUNNING_HEAD, lines[first].strip()))
    if last not in drop and _is_number(lines[last].strip(), printed):
        drop.add(last)
        removed.append(Furniture(scan, printed, PAGE_NUMBER, lines[last].strip()))
    kept = [line for i, line in enumerate(lines) if i not in drop]
    return "\n".join(kept).strip("\n"), removed


def strip_furniture(records: list[dict], order: ReadingOrder) -> tuple[list[dict], list[Furniture]]:
    """Records of the pages in `order` without furniture, and every line left out, in reading order."""
    by_scan = {record["scan"]: record for record in records}
    pages = [page for page in order.pages if page.how != HOW_TEXT]
    heads = running_heads([by_scan[page.scan]["text"] for page in pages])
    printed = {page.scan: page.printed for page in pages}
    out, removed = [], []
    for record in records:
        if record["scan"] not in printed:
            out.append(record)
            continue
        text, left_out = strip_page(record["text"], record["scan"], printed[record["scan"]], heads)
        out.append({**record, "text": text})
        removed.extend(left_out)
    position = {page.scan: i for i, page in enumerate(order.pages)}
    removed.sort(key=lambda f: position.get(f.scan, 0))
    return out, removed


def write_furniture(removed: list[Furniture], variant: str, path: Path) -> None:
    """The list for review: what was left out of the final text, page by page."""
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = Counter(f.kind for f in removed)
    data = {
        "variant": variant,
        "summary": {RUNNING_HEAD: summary[RUNNING_HEAD], PAGE_NUMBER: summary[PAGE_NUMBER]},
        "left_out": [asdict(f) for f in removed],
    }
    path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n")
