from mmo.ingest.segment import join_hyphenated, locations, paragraph_spans, segment_text, stale_segments

TEXT = """---
source: "kniha"
---

> Final text of `kniha`.

# Kniha

<!-- page 15 (printed) · scan 1 · IMG_1.jpg -->

Sebevražda je zjev společenský
a roste s moderní osvětou.

Rakousko-Uhersko má mnoho případů a

<!-- page ? (unknown) · scan 2 · IMG_2.jpg -->

pokračuje dál.
"""


def test_join_hyphenated_words_keeps_line_breaks() -> None:
    assert join_hyphenated("spo-\nlečenský a roste\ns osvětou") == "společenský a roste\ns osvětou"


def test_join_hyphenated_keeps_hyphen_before_capital_letter() -> None:
    assert join_hyphenated("Rakousko-\nUhersko") == "Rakousko-Uhersko"


def test_paragraph_spans_without_surrounding_whitespace() -> None:
    text = "  Jedna.\n\n\n  Dva\ntři.  \n"
    assert [text[a:b] for a, b in paragraph_spans(text)] == ["Jedna.", "Dva\ntři."]


def test_locations_read_page_scan_and_file() -> None:
    places = locations(TEXT + "<!-- file part-1.txt · scan 3 -->\n\nRozhovor.\n")
    assert [(p.scan, p.page, p.file) for p in places] == [(1, 15, None), (2, None, None), (3, None, "part-1.txt")]
    assert places[0].start > TEXT.index("# Kniha"), "header and title belong to no place"


def test_segments_point_into_the_final_text() -> None:
    segments = segment_text("kniha", TEXT)
    assert [s.id for s in segments] == ["kniha:s1:1", "kniha:s1:2", "kniha:s2:1"]
    assert all(TEXT[s.start : s.end] == s.text for s in segments), "text is exactly the slice of text.md"
    assert segments[0].text == "Sebevražda je zjev společenský\na roste s moderní osvětou."
    assert [s.page for s in segments] == [15, 15, None]
    assert [s.continues for s in segments] == [False, True, False], "no sentence end before a page break"


def test_text_without_location_comments_has_no_segments() -> None:
    assert segment_text("k", "# Jen nadpis\n\nA text bez místa.\n") == []


def test_stale_segments_after_the_text_changed() -> None:
    segments = [vars(s) for s in segment_text("kniha", TEXT)]
    assert stale_segments(TEXT, segments) == []
    changed = TEXT.replace("Sebevražda", "Sebevrazda [?]")
    assert stale_segments(changed, segments) == ["kniha:s1:1", "kniha:s1:2", "kniha:s2:1"]
