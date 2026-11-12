"""Reading order of a source from the printed page numbers in its OCR text.

Photos of a book are often taken out of order (a page retaken, a chapter photographed later). The scan number (`scan`
in OCR records = file-name order) stays the identity of an image; this module adds the printed page number and sorts by
it. A number comes from the page itself (`printed`: read from its edges by `mmo ocr numbers`, else found in the OCR
text), from both scan neighbours when they are two pages apart (`inferred`; a different number there is `corrected` -
a footnote number read instead), or from the owner (`manual`: `printed_pages` in `source.yaml`); pages without one
stay `unknown` and keep their place after the page photographed before them.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

# a line that is only a page number, maybe with dashes (also en and em dashes) or markdown around it: "15", "**15**"
PAGE_NUMBER_LINE = re.compile(r"^[\s\-\u2013\u2014|*_#>]*(\d{1,4})[\s\-\u2013\u2014|*_]*$")
EDGE_LINES = 3  # page numbers sit in the first or last lines of a page
HOW_PRINTED, HOW_INFERRED, HOW_MANUAL, HOW_UNKNOWN = "printed", "inferred", "manual", "unknown"
HOW_TEXT = "text"  # a text file, in file-name order: it has no printed page number
HOW_CORRECTED = "corrected"  # a number between two neighbours two apart that disagreed with them (a footnote misread)
HOWS = (HOW_PRINTED, HOW_INFERRED, HOW_CORRECTED, HOW_MANUAL)


def printed_page_number(text: str) -> int | None:
    """The page number printed on the page, looked for at the foot first, then at the head."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in [*reversed(lines[-EDGE_LINES:]), *lines[:EDGE_LINES]]:
        match = PAGE_NUMBER_LINE.match(line)
        if match:
            return int(match.group(1))
    return None


@dataclass
class PlacedPage:
    scan: int  # position in file-name order, the id of the OCR record
    image: str
    printed: int | None
    how: str
    found: int | None = None  # the number read before a correction


@dataclass
class ReadingOrder:
    pages: list[PlacedPage]  # in reading order
    gaps: list[int] = field(default_factory=list)  # printed numbers missing between the first and the last
    duplicates: dict[int, list[str]] = field(default_factory=dict)  # printed number -> images (retake or misread)

    @property
    def unknown(self) -> list[PlacedPage]:
        return [p for p in self.pages if p.how == HOW_UNKNOWN]

    def to_dict(self, variant: str) -> dict[str, Any]:
        return {
            "variant": variant,
            "summary": {
                "pages": len(self.pages),
                **{how: sum(p.how == how for p in self.pages) for how in HOWS},
                HOW_UNKNOWN: len(self.unknown),
                "gaps": self.gaps,
                "duplicates": self.duplicates,
            },
            "order": [asdict(p) for p in self.pages],
        }


def _numbered(records: list[dict], manual: Mapping[str, int], read: Mapping[str, int | None]) -> list[PlacedPage]:
    """Every record in scan order with its number and where the number came from."""
    placed = []
    for record in records:
        image = str(record.get("image") or "")
        if image in manual:
            placed.append(PlacedPage(record["scan"], image, int(manual[image]), HOW_MANUAL))
            continue
        number = read.get(image) or printed_page_number(record["text"])
        placed.append(PlacedPage(record["scan"], image, number, HOW_UNKNOWN if number is None else HOW_PRINTED))
    for before, page, after in zip(placed, placed[1:], placed[2:], strict=False):
        if before.printed is None or after.printed != before.printed + 2 or page.how == HOW_MANUAL:
            continue
        if page.printed is None:
            page.printed, page.how = before.printed + 1, HOW_INFERRED
        elif page.printed != before.printed + 1:
            page.found, page.printed, page.how = page.printed, before.printed + 1, HOW_CORRECTED
    return placed


def reading_order(
    records: Iterable[dict], manual: Mapping[str, int] | None = None, read: Mapping[str, int | None] | None = None
) -> ReadingOrder:
    """Sort OCR records (one per image) by printed page.

    `manual` = image file name -> page number set by the owner; `read` = numbers read from the page edges
    (`mmo ocr numbers`), used before the number found in the OCR text.
    """
    placed = _numbered(sorted(records, key=lambda r: r["scan"]), manual or {}, read or {})
    keys: dict[int, tuple[float, int]] = {}
    anchor = 0.0  # an unknown page follows the last numbered page photographed before it
    for page in placed:
        if page.printed is not None:
            anchor = float(page.printed)
            keys[page.scan] = (anchor, page.scan)
        else:
            keys[page.scan] = (anchor + 0.5, page.scan)
    ordered = sorted(placed, key=lambda p: keys[p.scan])
    numbers = Counter(p.printed for p in placed if p.printed is not None)
    gaps = [n for n in range(min(numbers), max(numbers) + 1) if n not in numbers] if numbers else []
    duplicates = {n: [p.image for p in ordered if p.printed == n] for n, count in sorted(numbers.items()) if count > 1}
    return ReadingOrder(pages=ordered, gaps=gaps, duplicates=duplicates)


def write_order(order: ReadingOrder, variant: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(order.to_dict(variant), sort_keys=False, allow_unicode=True), encoding="utf-8")


def ordered_records(records: list[dict], order: ReadingOrder) -> list[dict]:
    """The OCR records in the order's sequence."""
    by_scan = {record["scan"]: record for record in records}
    return [by_scan[page.scan] for page in order.pages]


def book_markdown(records: list[dict], order: ReadingOrder, title: str) -> str:
    """The whole text in reading order, each page under a comment that says where it came from."""
    by_scan = {record["scan"]: record for record in records}
    parts = [f"# {title}\n"]
    for page in order.pages:
        text = by_scan[page.scan]["text"].strip()
        if page.how == HOW_TEXT:
            parts.append(f"<!-- file {page.image} · scan {page.scan} -->\n\n{text}\n")
            continue
        printed = f"page {page.printed} ({page.how})" if page.printed is not None else "page ? (unknown)"
        parts.append(f"<!-- {printed} · scan {page.scan} · {page.image} -->\n\n{text}\n")
    return "\n".join(parts)
