"""Printed page numbers read from the edges of each page image (`mmo ocr numbers`).

The OCR model leaves running headers and footers out of the page text (dots.ocr treats them as layout, not content),
and Tesseract cannot read a lone number from a phone photo, so the number is read separately: the top and the bottom
strip of the photo, stacked into one small image, go to a vision model with a one-field question. Results are kept per
image in `work/numbers/<source>.json`; a rerun reads only the images without a result.
"""

from __future__ import annotations

import io
import json
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Protocol

from PIL import Image, ImageOps

from mixed_method_ontology.topic import Source, sha256_file

TOP_SHARE = 0.12  # running header with the page number on some pages
BOTTOM_SHARE = 0.15  # footer; phone photos often show some background below the page
EDGE_MAX_SIDE_PX = 1200
JPEG_QUALITY = 90
INSTRUCTION = (
    "This is the top and the bottom edge of one photographed book page. Give the printed page number (a number alone "
    "in the header or footer). Do not use footnote numbers or years."
)
SCHEMA = {
    "type": "object",
    "required": ["page"],
    "properties": {
        "page": {
            "type": ["integer", "null"],
            "description": "the page number printed on the book page, null when none is visible",
        }
    },
}


class PageNumberReader(Protocol):
    name: str

    def read(self, edges: bytes) -> int | None: ...


def edge_strip(image: Path) -> bytes:
    """The top and the bottom strip of an upright page image, one above the other, as a small JPEG."""
    with Image.open(image) as opened:
        page = ImageOps.exif_transpose(opened).convert("RGB")
    width, height = page.size
    top, bottom = int(height * TOP_SHARE), int(height * (1 - BOTTOM_SHARE))
    strip = Image.new("RGB", (width, top + height - bottom), "white")
    strip.paste(page.crop((0, 0, width, top)), (0, 0))
    strip.paste(page.crop((0, bottom, width, height)), (0, top))
    strip.thumbnail((EDGE_MAX_SIDE_PX, EDGE_MAX_SIDE_PX))
    out = io.BytesIO()
    strip.save(out, format="JPEG", quality=JPEG_QUALITY)
    return out.getvalue()


def load_page_numbers(path: Path) -> dict[str, int | None]:
    """Image file name -> page number read from its edges (None = read, no number on the page)."""
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return {image: entry["page"] for image, entry in data.get("pages", {}).items()}


def read_page_numbers(
    source: Source,
    reader: PageNumberReader,
    path: Path,
    log: Callable[[str], None] = print,
    workers: int = 1,
) -> int:
    """Read the number of every image that has none yet; returns how many were read. Saved after each image."""
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"reader": reader.name, "pages": {}}
    todo = [page for page in source.pages() if page.image.name not in data["pages"]]
    lock = threading.Lock()
    failed: dict[str, str] = {}

    def one(image: Path) -> dict:
        started = time.monotonic()
        number = reader.read(edge_strip(image))
        return {"page": number, "sha256": sha256_file(image), "seconds": round(time.monotonic() - started, 2)}

    path.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {pool.submit(one, page.image): page for page in todo}
        for future in as_completed(futures):
            page = futures[future]
            try:
                entry = future.result()
            except Exception as err:  # one bad image must not lose the others; reported below
                failed[page.image.name] = str(err)
                log(f"page {page.number}: FAILED {err}")
                continue
            with lock:
                data["pages"][page.image.name] = entry
                data["pages"] = dict(sorted(data["pages"].items()))
                path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            log(f"page {page.number} ({page.image.name}): printed {entry['page']}")
    if failed:
        raise RuntimeError(f"{len(failed)} of {len(todo)} images failed; run again to retry only those")
    return len(todo)
