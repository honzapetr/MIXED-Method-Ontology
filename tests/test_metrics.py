import pytest

from mixed_method_ontology.metrics import cer, levenshtein, normalize


def test_levenshtein() -> None:
    assert levenshtein("kitten", "sitting") == 3
    assert levenshtein("", "abc") == 3


def test_normalize_ignores_line_breaks_and_unicode_form() -> None:
    assert normalize("pří-\n  liš\n") == normalize("pří- liš")
    assert normalize("č") == "č"


def test_cer() -> None:
    assert cer("abcd", "abcd") == 0.0
    assert cer("abcd", "abxd") == pytest.approx(0.25)
    assert cer("", "") == 0.0
    assert cer("", "x") == 1.0
