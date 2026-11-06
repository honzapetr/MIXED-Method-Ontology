from mixed_method_ontology.segment import clean, paragraph_spans, segment_page, segment_records

PAGE = "Sebevražda je zjev spo-\nlečenský a roste\ns moderní osvětou.\n\n  Rakousko-\nUhersko má mnoho pří-\npadů a"


def test_clean_joins_hyphenated_words_and_lines() -> None:
    assert clean("spo-\nlečenský a roste\ns osvětou") == "společenský a roste s osvětou"


def test_clean_keeps_hyphen_before_capital_letter() -> None:
    assert clean("Rakousko-\nUhersko") == "Rakousko-Uhersko"


def test_paragraph_spans_point_into_the_page_text() -> None:
    spans = paragraph_spans(PAGE)
    assert len(spans) == 2
    first, second = (PAGE[start:end] for start, end in spans)
    assert first.startswith("Sebevražda") and first.endswith("osvětou.")
    assert second.startswith("Rakousko-") and second.endswith("a")


def test_segment_page_ids_offsets_and_continuation() -> None:
    segments = segment_page("kniha", 3, PAGE, "tesseract")
    assert [s.id for s in segments] == ["kniha:p3:1", "kniha:p3:2"]
    assert segments[0].text == "Sebevražda je zjev společenský a roste s moderní osvětou."
    assert segments[1].text == "Rakousko-Uhersko má mnoho případů a"
    assert not segments[0].continues
    assert segments[1].continues  # no sentence end: probably continues on the next page
    assert PAGE[segments[1].start : segments[1].end].startswith("Rakousko")


def test_segment_records_orders_by_record() -> None:
    records = [
        {"source": "k", "page": 1, "text": "Jedna.", "backend": "x"},
        {"source": "k", "page": 2, "text": "Dva.\n\nTři.", "backend": "x"},
    ]
    assert [s.id for s in segment_records(records)] == ["k:p1:1", "k:p2:1", "k:p2:2"]


def test_empty_page_has_no_segments() -> None:
    assert segment_page("k", 1, "  \n\n ", "x") == []
