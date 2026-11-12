import json
from pathlib import Path

import yaml

from mmo.cli import compact_ranges, main
from mmo.ingest.order import (
    HOW_INFERRED,
    HOW_MANUAL,
    HOW_PRINTED,
    HOW_UNKNOWN,
    book_markdown,
    ordered_records,
    printed_page_number,
    reading_order,
)


def test_page_number_at_the_foot_or_the_head() -> None:
    assert printed_page_number("NAZÍ V AI DOBĚ\n\nden ode dne silnější.\n\n15\n") == 15
    assert printed_page_number("\u2013 7 \u2013\n\nText of the page.") == 7
    assert printed_page_number("Text.\n\n**128**") == 128
    assert printed_page_number("Text.\n\n94 Mandaville a Williams, Meaning, 55.") is None, "a footnote is not a number"
    assert printed_page_number("Chapter one\n\nNo number on this page.") is None
    assert printed_page_number("") is None


def record(scan: int, text: str) -> dict:
    return {"source": "book", "page": scan, "image": f"IMG_{scan:03d}.jpg", "text": text, "backend": "fake"}


def test_photos_out_of_order_are_sorted_by_printed_page() -> None:
    records = [record(1, "a\n\n12"), record(2, "b\n\n10"), record(3, "c\n\n11"), record(4, "d\n\n14")]
    order = reading_order(records)
    assert [p.printed for p in order.pages] == [10, 11, 12, 14]
    assert [p.scan for p in order.pages] == [2, 3, 1, 4]
    assert order.gaps == [13] and order.duplicates == {}
    assert [r["page"] for r in ordered_records(records, order)] == [2, 3, 1, 4]


def test_a_page_without_a_number_between_two_pages_apart_is_inferred() -> None:
    order = reading_order([record(1, "a\n\n20"), record(2, "chapter opening"), record(3, "c\n\n22")])
    middle = next(p for p in order.pages if p.scan == 2)
    assert (middle.printed, middle.how) == (21, HOW_INFERRED)
    assert order.gaps == []


def test_a_number_that_disagrees_with_both_neighbours_is_corrected() -> None:
    order = reading_order([record(1, "a\n\n43"), record(2, "b\n\n66"), record(3, "c\n\n45")])
    middle = next(p for p in order.pages if p.scan == 2)
    assert (middle.printed, middle.how, middle.found) == (44, "corrected", 66)
    kept = reading_order([record(1, "a\n\n43"), record(2, "b\n\n66"), record(3, "c\n\n47")])
    assert next(p for p in kept.pages if p.scan == 2).printed == 66, "neighbours not two apart: nothing to go by"


def test_an_unknown_page_follows_the_page_photographed_before_it() -> None:
    records = [record(1, "a\n\n30"), record(2, "an image, no text"), record(3, "c\n\n5"), record(4, "d\n\n6")]
    order = reading_order(records)
    assert [(p.scan, p.how) for p in order.pages] == [
        (3, HOW_PRINTED),
        (4, HOW_PRINTED),
        (1, HOW_PRINTED),
        (2, HOW_UNKNOWN),
    ]
    assert [p.scan for p in order.unknown] == [2]


def test_retaken_pages_are_reported_and_manual_numbers_win() -> None:
    records = [record(1, "a\n\n8"), record(2, "a again\n\n8"), record(3, "no number")]
    order = reading_order(records, manual={"IMG_003.jpg": 9})
    assert order.duplicates == {8: ["IMG_001.jpg", "IMG_002.jpg"]}
    last = order.pages[-1]
    assert (last.scan, last.printed, last.how) == (3, 9, HOW_MANUAL)
    summary = order.to_dict("fabric")["summary"]
    assert summary["printed"] == 2 and summary["manual"] == 1 and summary["unknown"] == 0


def test_book_markdown_says_where_each_page_came_from() -> None:
    records = [record(1, "druhá\n\n2"), record(2, "první\n\n1")]
    text = book_markdown(records, reading_order(records), "Kniha")
    assert text.startswith("# Kniha\n")
    assert text.index("první") < text.index("druhá")
    assert "<!-- page 1 (printed) · scan 2 · IMG_002.jpg -->" in text


def test_compact_ranges() -> None:
    assert compact_ranges([3, 4, 5, 9, 11, 12]) == "3-5, 9, 11-12"
    assert compact_ranges([]) == ""


def test_order_and_book_commands(tmp_path: Path, capsys) -> None:
    assert main(["--topics", str(tmp_path), "topic", "new", "t1", "--title", "T"]) == 0
    topic = tmp_path / "t1"
    out = topic / "work" / "ocr" / "fabric" / "book"
    out.mkdir(parents=True)
    for rec in [record(1, "Konec odstavce\n\n2"), record(2, "Začátek odstavce,\n\n1"), record(3, "obrázek")]:
        (out / f"page-{rec['page']:04d}.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")

    assert main(["--topics", str(tmp_path), "ocr", "order", "t1", "book", "--variant", "fabric"]) == 0
    printed = capsys.readouterr().out
    assert "2 printed" in printed and "no page number: scan 3 IMG_003.jpg" in printed
    data = yaml.safe_load((topic / "work" / "order" / "fabric" / "book.yaml").read_text(encoding="utf-8"))
    order = [entry["scan"] for entry in data["order"]]
    assert order == [2, 3, 1], "the unknown page follows page 1, photographed before it"

    source = topic / "sources" / "book"
    source.mkdir(parents=True)
    (source / "source.yaml").write_text("id: book\ntitle: Kniha\nprinted_pages:\n  IMG_003.jpg: 3\n", encoding="utf-8")
    assert main(["--topics", str(tmp_path), "ocr", "book", "t1", "book", "--variant", "fabric"]) == 0
    book = (topic / "work" / "text" / "fabric" / "book.md").read_text(encoding="utf-8")
    assert book.startswith("# Kniha") and "page 3 (manual)" in book

    assert main(["--topics", str(tmp_path), "segment", "t1", "book", "--variant", "fabric"]) == 0
    lines = (topic / "work" / "segments" / "book.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["id"] == "book:p2:1", "segments follow the reading order, not the scan order"
