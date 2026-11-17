"""Page furniture: running heads and printed page numbers left out of the final text (samples from `kniha`)."""

from pathlib import Path

import yaml

from mmo.ingest.furniture import PAGE_NUMBER, RUNNING_HEAD, running_heads, strip_furniture, strip_page, write_furniture
from mmo.ingest.order import HOW_PRINTED, HOW_TEXT, HOW_UNKNOWN, PlacedPage, ReadingOrder

HEADS = {"NAZÍ V AI DOBĚ", "TANEC SLUNCI"}


def test_running_heads_are_lines_that_open_many_pages() -> None:
    texts = ["NAZÍ V AI DOBĚ\ntext"] * 3 + ["TANEC SLUNCI\ntext"] * 2 + ["## KAPITOLA\ntext"] * 4 + ["ÚVOD\ntext"]
    assert running_heads(texts) == {"NAZÍ V AI DOBĚ"}, "rare lines and Markdown headings are not running heads"


def test_head_glued_to_the_first_paragraph_and_number_at_the_foot() -> None:
    page = "NAZÍ V AI DOBĚ\nden ode dne silnější. Do jejího vývoje tečou data.\n\nDalší odstavec.\n\n16"
    text, removed = strip_page(page, 2, 16, HEADS)
    assert text == "den ode dne silnější. Do jejího vývoje tečou data.\n\nDalší odstavec."
    assert [(f.kind, f.line) for f in removed] == [(RUNNING_HEAD, "NAZÍ V AI DOBĚ"), (PAGE_NUMBER, "16")]


def test_a_misread_running_head_is_recognised() -> None:
    text, removed = strip_page("TANEC SLUNCÍ\nPodle Hegela jsme na cestě růstu.\n\n42", 27, 42, HEADS)
    assert text == "Podle Hegela jsme na cestě růstu." and len(removed) == 2


def test_chapter_opening_keeps_its_headings() -> None:
    page = "KAPITOLA II.\n## MĚSTO NA AI PAHORKU\n„My Američané jsme zvláštní, vyvolený národ.“\n\n57"
    text, removed = strip_page(page, 41, 57, HEADS)
    assert text.startswith("KAPITOLA II.\n## MĚSTO NA AI PAHORKU") and [f.kind for f in removed] == [PAGE_NUMBER]


def test_a_number_that_is_not_the_page_number_stays() -> None:
    assert strip_page("Text.\n\n31", 5, 30, HEADS)[0] == "Text.\n\n31", "not this page's number (e.g. a footnote)"
    assert strip_page("Text.\n\n31", 5, None, HEADS)[0] == "Text.\n\n31", "the page's number is unknown"


def test_page_number_at_the_head_before_the_running_head() -> None:
    text, removed = strip_page("20\nNAZÍ V AI DOBĚ\nText strany.", 3, 20, HEADS)
    assert text == "Text strany." and [f.kind for f in removed] == [PAGE_NUMBER, RUNNING_HEAD]


def test_text_files_keep_everything(tmp_path: Path) -> None:
    records = [{"scan": i, "text": f"NAZÍ V AI DOBĚ\nČást {i}.\n\n{i}"} for i in (1, 2, 3)]
    order = ReadingOrder(pages=[PlacedPage(i, f"part-{i}.md", None, HOW_TEXT) for i in (1, 2, 3)])
    out, removed = strip_furniture(records, order)
    assert out == records and removed == []


def test_strip_furniture_lists_in_reading_order(tmp_path: Path) -> None:
    records = [
        {"scan": 1, "text": "NAZÍ V AI DOBĚ\nTřetí.\n\n17"},
        {"scan": 2, "text": "NAZÍ V AI DOBĚ\nPrvní.\n\n15"},
        {"scan": 3, "text": "NAZÍ V AI DOBĚ\nDruhá."},
        {"scan": 4, "text": "Bez čísla.\n\n99"},
    ]
    order = ReadingOrder(
        pages=[
            PlacedPage(2, "b.jpg", 15, HOW_PRINTED),
            PlacedPage(3, "c.jpg", 16, HOW_PRINTED),
            PlacedPage(1, "a.jpg", 17, HOW_PRINTED),
            PlacedPage(4, "d.jpg", None, HOW_UNKNOWN),
        ]
    )
    out, removed = strip_furniture(records, order)
    assert [r["text"] for r in out] == ["Třetí.", "První.", "Druhá.", "Bez čísla.\n\n99"]
    assert [(f.scan, f.kind) for f in removed][:3] == [(2, RUNNING_HEAD), (2, PAGE_NUMBER), (3, RUNNING_HEAD)]

    path = tmp_path / "ingest" / "furniture" / "book.yaml"
    write_furniture(removed, "book", path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["summary"] == {RUNNING_HEAD: 3, PAGE_NUMBER: 2}
    assert data["left_out"][0] == {"scan": 2, "page": 15, "kind": RUNNING_HEAD, "line": "NAZÍ V AI DOBĚ"}
