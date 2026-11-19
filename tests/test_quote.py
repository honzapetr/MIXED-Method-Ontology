"""Quotations: made only from words of text.md, checked, found again after a rebuild (T26, ADR 0012)."""

import json
from pathlib import Path

import pytest
import yaml

from mmo.analysis.quote import (
    AMBIGUOUS,
    GONE,
    MOVED,
    NO_TEXT,
    OK,
    QuoteError,
    check_record,
    check_study,
    find_quotation,
    text_sha256,
)
from mmo.cli import main
from mmo.core.topic import Topic

TEXT = """---
source: "k"
title: "Kniha"
---

> Final text of `k`.

# Kniha o nahotě

<!-- page 15 (printed) · scan 1 · a.jpg -->

Mohl jsem rozvést téma nahoty, kterou vnímám jako upřímný stav.

Opakovaná věta. Text pokračuje přes
konec strany

<!-- page 16 (printed) · scan 2 · b.jpg -->

a dál na další straně.

Opakovaná věta. Konec.
"""


def test_words_become_a_quotation_with_their_place() -> None:
    q = find_quotation("k", TEXT, "téma nahoty, kterou vnímám")
    assert TEXT[q.start : q.end] == "téma nahoty, kterou vnímám"
    assert (q.source, q.pages, q.scans) == ("k", [15], [1])
    assert q.prefix.endswith("Mohl jsem rozvést ") and q.suffix.startswith(" jako upřímný")
    assert q.text_sha256 == text_sha256(TEXT)


def test_a_quotation_runs_over_a_page_break_and_a_line_break() -> None:
    q = find_quotation("k", TEXT, "Text pokračuje přes konec strany a dál na další")
    assert q.pages == [15, 16] and q.scans == [1, 2]
    assert "<!-- page 16" in TEXT[q.start : q.end], "the comment lies inside the span"
    assert q.exact == "Text pokračuje přes konec strany a dál na další", "but is not part of the words"
    assert TEXT[q.start : q.end].startswith("Text pokračuje") and TEXT[q.start : q.end].endswith("na další")


def test_words_not_in_the_text_are_refused() -> None:
    with pytest.raises(QuoteError, match="not in the final text"):
        find_quotation("k", TEXT, "téma nahoty, kterou vnimam")  # a missing accent is a different word
    with pytest.raises(QuoteError, match="not in the final text"):  # the header and title are not the source's text
        find_quotation("k", TEXT, "Kniha o nahotě")
    with pytest.raises(QuoteError, match="no words"):
        find_quotation("k", TEXT, "  \n ")


def test_words_found_more_than_once_need_a_hint() -> None:
    with pytest.raises(QuoteError, match="found 2 times"):
        find_quotation("k", TEXT, "Opakovaná věta.")
    assert find_quotation("k", TEXT, "Opakovaná věta.", page=16).pages == [16]
    assert find_quotation("k", TEXT, "Opakovaná věta.", segment="k:s1:2").pages == [15]
    with pytest.raises(QuoteError, match="not at the place given"):
        find_quotation("k", TEXT, "Opakovaná věta.", page=99)
    with pytest.raises(QuoteError, match="no segment"):
        find_quotation("k", TEXT, "Opakovaná věta.", segment="k:s9:9")


def test_check_finds_moved_words_again_and_reports_gone_ones() -> None:
    record = find_quotation("k", TEXT, "rozvést téma nahoty").record()
    assert check_record(record, TEXT).status == OK

    rebuilt = TEXT.replace("Mohl jsem", "Nový odstavec.\n\nMohl jsem")  # a page read again
    moved = check_record(record, rebuilt)
    assert moved.status == MOVED and moved.new is not None
    assert rebuilt[moved.new.start : moved.new.end] == "rozvést téma nahoty"

    assert check_record(record, TEXT.replace("rozvést", "rozvinout")).status == GONE

    twice = find_quotation("k", TEXT, "Opakovaná věta.", page=16).record()
    shifted = TEXT.replace("Mohl jsem", "Vložené.\n\nMohl jsem")
    found = check_record(twice, shifted)
    assert found.status == MOVED and found.new is not None and found.new.pages == [16], "prefix and suffix decide"
    twice["prefix"], twice["suffix"] = "x", "y"
    assert check_record(twice, shifted).status == AMBIGUOUS


def _study(tmp_path: Path) -> Topic:
    topic = Topic.create(tmp_path, "st", "S")
    text = topic.source("kn").final_text_file
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(TEXT, encoding="utf-8", newline="\n")
    return topic


def test_check_study_reads_analytic_files_and_updates_moved(tmp_path: Path) -> None:
    topic = _study(tmp_path)
    q = find_quotation("kn", TEXT, "rozvést téma nahoty").record()
    codes = topic.root / "analysis" / "codes.yaml"
    codes.parent.mkdir(parents=True)
    codes.write_text(
        yaml.safe_dump({"codes": [{"name": "nahota", "quotations": [q]}]}, allow_unicode=True), encoding="utf-8"
    )
    memo = topic.root / "memos" / "2026-11-19-a.md"
    memo.parent.mkdir(parents=True, exist_ok=True)
    front = yaml.safe_dump({"quotation": q}, allow_unicode=True)
    memo.write_text(f"---\n{front}---\n\n# Memo\n\nText.\n", encoding="utf-8")
    rows = topic.root / "analysis" / "codings.jsonl"
    rows.write_text(json.dumps({"code": "x", "quotation": {**q, "source": "missing"}}) + "\n", encoding="utf-8")
    (topic.root / "work").mkdir()
    (topic.root / "work" / "scratch.yaml").write_text(yaml.safe_dump({"q": q}), encoding="utf-8")

    statuses = sorted(r.status for r in check_study(topic))
    assert statuses == [NO_TEXT, OK, OK], "work/ is not analytic; a source without text.md is reported"

    topic.source("kn").final_text_file.write_text(
        TEXT.replace("Mohl jsem", "Nový.\n\nMohl jsem"), encoding="utf-8", newline="\n"
    )
    assert sorted(r.status for r in check_study(topic)) == [MOVED, MOVED, NO_TEXT]
    check_study(topic, update=True)
    assert sorted(r.status for r in check_study(topic)) == [NO_TEXT, OK, OK]
    stored = yaml.safe_load(codes.read_text(encoding="utf-8"))["codes"][0]["quotations"][0]
    assert stored["start"] == q["start"] + len("Nový.\n\n")
    assert memo.read_text(encoding="utf-8").endswith("# Memo\n\nText.\n"), "the memo's text is kept"


def test_cli_find_and_check(tmp_path: Path, capsys) -> None:
    _study(tmp_path)
    base = ["--topics", str(tmp_path), "quote"]
    assert main([*base, "find", "st", "kn", "téma nahoty"]) == 0
    printed = yaml.safe_load(capsys.readouterr().out)["quotation"]
    assert printed["exact"] == "téma nahoty" and printed["pages"] == [15]
    assert main([*base, "find", "st", "kn", "Opakovaná věta."]) == 1
    assert "found 2 times" in capsys.readouterr().err
    assert main([*base, "find", "st", "kn", "Opakovaná věta.", "--page", "16", "--format", "json"]) == 0
    assert json.loads(capsys.readouterr().out)["pages"] == [16]
    assert main([*base, "check", "st"]) == 0
    assert "no quotations" in capsys.readouterr().out
