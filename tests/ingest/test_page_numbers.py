import io
import json
from pathlib import Path

import httpx
import pytest
from fabric_ocr.client import OcrClient
from PIL import Image

from mmo.core.topic import Topic
from mmo.ingest.ocr.fabric import FabricPageNumbers
from mmo.ingest.order import HOW_MANUAL, HOW_PRINTED, reading_order
from mmo.ingest.page_numbers import edge_strip, load_page_numbers, read_page_numbers


def page_photo(path: Path) -> None:
    """A 1000 x 2000 page: red header band, blue footer band, green body."""
    image = Image.new("RGB", (1000, 2000), "green")
    image.paste(Image.new("RGB", (1000, 200), "red"), (0, 0))
    image.paste(Image.new("RGB", (1000, 250), "blue"), (0, 1750))
    image.save(path, format="JPEG")


def test_the_edge_strip_is_the_header_above_the_footer(tmp_path: Path) -> None:
    photo = tmp_path / "p.jpg"
    page_photo(photo)
    strip = Image.open(io.BytesIO(edge_strip(photo)))
    assert strip.size == (1000, 240 + 300) and max(strip.size) <= 1200
    top, bottom = strip.getpixel((500, 100)), strip.getpixel((500, 400))
    assert top[0] > 200 and top[2] < 60, "the header (red) on top"
    assert bottom[2] > 200 and bottom[0] < 60, "the footer (blue) below, no body (green) in between"


class FakeReader:
    name = "fake"

    def __init__(self, numbers: dict[int, int | None], broken: set[int] = frozenset()) -> None:
        self.numbers, self.broken, self.calls = numbers, broken, 0

    def read(self, edges: bytes) -> int | None:
        self.calls += 1
        size = Image.open(io.BytesIO(edges)).size[0]  # each test photo has its own width
        if size in self.broken:
            raise RuntimeError("service went away")
        return self.numbers[size]


def test_numbers_are_saved_per_image_and_a_rerun_reads_only_the_missing(tmp_path: Path) -> None:
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.source("book")
    source.root.mkdir()
    for i, width in enumerate((301, 302, 303), start=1):
        Image.new("RGB", (width, 600), "white").save(source.root / f"IMG_{i}.jpg", format="JPEG")
    target = topic.numbers_file("book")
    with pytest.raises(RuntimeError, match="1 of 3 images failed"):
        read_page_numbers(source, FakeReader({301: 15, 303: None}, broken={302}), target, log=lambda _: None)
    assert load_page_numbers(target) == {"IMG_1.jpg": 15, "IMG_3.jpg": None}
    again = FakeReader({302: 16})
    assert read_page_numbers(source, again, target, log=lambda _: None, workers=2) == 1 and again.calls == 1
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["reader"] == "fake" and len(data["pages"]["IMG_2.jpg"]["sha256"]) == 64


def test_numbers_from_the_edges_win_over_the_text_and_manual_wins_over_both() -> None:
    records = [
        {"page": 1, "image": "a.jpg", "text": "text\n\n99"},
        {"page": 2, "image": "b.jpg", "text": "text"},
        {"page": 3, "image": "c.jpg", "text": "text"},
    ]
    order = reading_order(records, manual={"c.jpg": 1}, read={"a.jpg": 3, "b.jpg": 2, "c.jpg": None})
    assert [(p.image, p.printed, p.how) for p in order.pages] == [
        ("c.jpg", 1, HOW_MANUAL),
        ("b.jpg", 2, HOW_PRINTED),
        ("a.jpg", 3, HOW_PRINTED),
    ]


def test_the_fabric_reader_asks_extract_for_one_number() -> None:
    seen: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        page = 55 if len(seen) == 1 else None
        return httpx.Response(200, json={"data": {"page": page}, "text": "", "warnings": []})

    reader = FabricPageNumbers(
        OcrClient(httpx.Client(base_url="http://ocr.test", transport=httpx.MockTransport(handler)))
    )
    assert reader.read(b"\xff\xd8edges") == 55
    assert reader.read(b"\xff\xd8edges") is None
    assert seen[0]["schema"]["required"] == ["page"] and "page number" in seen[0]["instruction"]
