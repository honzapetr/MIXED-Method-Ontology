"""The outline of a source, the researcher's chapters and declared parts, and the coverage of each part (T36)."""

from pathlib import Path

import pytest

from mmo.analysis.method import SettingsError, study_settings
from mmo.analysis.outline import add_coverage, coverage, outline, resolve
from mmo.analysis.quote import quote
from mmo.analysis.status import study_status
from mmo.analysis.store import Store, StoreError, author_of, write_memo
from mmo.cli import main
from mmo.core.topic import Topic, write_yaml
from mmo.ingest.pipeline import write_segments

MODEL = "# {m} – model profile\n\n> Status: confirmed\n"  # noqa: RUF001 - profiles use the en dash
READER = """---
name: chapter-reader
description: Reads one part of a source whole.
version: "2026-11-24"
writes: memo
---
"""
POSITION = "---\nanalyst: {m}\nstatus: confirmed\nprofile_version: '1'\nroles:\n  - chapter-reader\n---\n\n# P\n"
TEXT = """---
source: "kniha"
---

> Final text.

# Kniha

<!-- page 1 (printed) · scan 1 · a.jpg -->

Úvod říká, o čem kniha je.

<!-- page 2 (printed) · scan 2 · b.jpg -->

## KONTROLA

Chceme mít kontrolu nad vším.

<!-- page 3 (printed) · scan 3 · c.jpg -->

## PARADOX

Kontrola se obrací proti nám.

<!-- page 4 (printed) · scan 4 · d.jpg -->

## SMYSL

Více smyslu, méně kontroly.

<!-- page 5 (printed) · scan 5 · e.jpg -->

1 Poznámka k první kapitole.
"""


@pytest.fixture
def topic(tmp_path: Path) -> Topic:
    env = tmp_path / "env"
    (env / "analysts").mkdir(parents=True)
    (env / ".agents" / "roles").mkdir(parents=True)
    (env / ".agents" / "roles" / "chapter-reader.md").write_text(READER, encoding="utf-8")
    topic = Topic.create(env / "topics", "st", "S")
    (topic.root / "positions").mkdir()
    (env / "analysts" / "lead.md").write_text(MODEL.format(m="lead"), encoding="utf-8")
    (topic.root / "positions" / "lead.md").write_text(POSITION.format(m="lead"), encoding="utf-8")
    (topic.root / "positions" / "owner.md").write_text("# owner\n", encoding="utf-8")
    source = topic.add_source("kniha", "book", "Kniha")
    source.final_text_file.write_text(TEXT, encoding="utf-8", newline="\n")
    write_segments(source)
    topic.add_source("recenze", "article", "Recenze", role="context", about=["kniha"])
    return topic


def lead(topic: Topic):
    return author_of(topic, "lead", "skad/context-analysis@1")


def declare(topic: Topic, **outline_data) -> None:
    source = topic.source("kniha")
    meta = source.metadata()
    meta["outline"] = outline_data
    write_yaml(source.metadata_file, meta)


def test_the_outline_comes_from_the_headings(topic: Topic) -> None:
    found = outline(topic, "kniha")
    assert [(p.id, p.level, p.title) for p in found.parts] == [
        ("part-01", 1, "Kniha"),
        ("part-02", 2, "KONTROLA"),
        ("part-03", 2, "PARADOX"),
        ("part-04", 2, "SMYSL"),
    ]
    assert found.parts[0].pages == [1] and found.parts[3].pages == [4, 5]
    assert found.parts[1].segments == ["kniha:s2:1", "kniha:s2:2"] and found.chapters == [] and found.problems == []
    text = topic.source("kniha").final_text_file.read_text(encoding="utf-8")
    assert text[found.parts[2].start :].startswith("## PARADOX") and found.parts[2].end == found.parts[3].start


def test_chapters_and_parts_without_a_heading_are_the_researchers(topic: Topic) -> None:
    declare(
        topic,
        chapters=[
            {"id": "intro", "title": "Úvod", "first": "Kniha"},
            {"id": "ch1", "title": "I Kontrola", "first": "KONTROLA"},
            {"id": "notes", "title": "Poznámky", "first": "notes"},
        ],
        parts=[{"id": "notes", "title": "Poznámky", "at": "1 Poznámka k první"}],
    )
    found = outline(topic, "kniha")
    assert [p.id for p in found.parts] == ["part-01", "part-02", "part-03", "part-04", "notes"], "no renumbering"
    assert found.parts[3].pages == [4] and found.parts[4].pages == [5] and found.parts[4].level == 0
    assert [(c.id, c.parts) for c in found.chapters] == [
        ("intro", ["part-01"]),
        ("ch1", ["part-02", "part-03", "part-04"]),
        ("notes", ["notes"]),
    ]
    assert resolve(found, ["ch1"]) == ["part-02", "part-03", "part-04"]
    assert resolve(found, ["part-03..part-04", "part-02"]) == ["part-02", "part-03", "part-04"]
    with pytest.raises(StoreError, match="has no part-09"):
        resolve(found, ["part-09"])
    declare(
        topic,
        chapters=[{"id": "a", "first": "PARADOX"}, {"id": "b", "first": "KONTROLA"}, {"id": "c", "first": "Nic"}],
        parts=[{"id": "part-07", "at": "x"}, {"id": "n", "at": "kontrol"}],
    )
    problems = outline(topic, "kniha").problems
    assert any("part-07 is taken" in p for p in problems)
    assert any("'kontrol' is found 2 times" in p for p in problems)
    assert any("b starts before or with the chapter above it" in p for p in problems)
    assert any("c starts at 'Nic', which is no heading" in p for p in problems)


def test_coverage_is_declared_by_the_reader_and_seen_in_quotations(topic: Topic) -> None:
    declare(topic, chapters=[{"id": "intro", "first": "Kniha"}, {"id": "ch1", "title": "I", "first": "KONTROLA"}])
    store = Store(topic)
    add_coverage(store, lead(topic), "kniha", ["intro", "ch1"], "map", "read for the map")
    event = add_coverage(store, lead(topic), "kniha", ["part-02"], "whole")
    assert event["op"] == "coverage" and event["parts"] == ["part-02"] and event["text_sha256"]
    run = store.start_run(lead(topic), "lead", "chapter-reader", ["kniha ch1"])["run"]
    reader = author_of(topic, "lead", run=run)
    add_coverage(store, reader, "kniha", ["part-03"], "whole")
    write_memo(topic, lead(topic), "analytic", "Smysl", "x", quotations=[quote(topic.source("kniha"), "méně kontroly")])
    with pytest.raises(StoreError, match="--how is one of"):
        add_coverage(store, lead(topic), "kniha", ["part-02"], "skimmed")
    _, by_part = coverage(topic, "kniha")
    assert {e["how"] for e in by_part["part-02"]} == {"map", "whole"}
    assert by_part["part-03"][-1]["by"] == f"lead (chapter-reader {run})"
    assert {e["how"] for e in by_part["part-04"]} == {"map", "quoted"}
    status = "\n".join(study_status(topic))
    assert "coverage of kniha (4 parts" in status and "whole 2, passages 0, map 2, quoted 0, nobody 0" in status
    assert "ch1 I (pp. 2-5): weakest part map - 2/3 parts whole" in status
    assert "recenze" not in status.split("coverage of")[1].split("\n")[0], "context sources are not counted"


def test_a_declaration_on_an_earlier_text_does_not_count(topic: Topic) -> None:
    add_coverage(Store(topic), lead(topic), "kniha", ["part-02"], "whole")
    path = topic.source("kniha").final_text_file
    path.write_text(path.read_text(encoding="utf-8").replace("vším", "vším, říká autor"), encoding="utf-8")
    _, by_part = coverage(topic, "kniha")
    assert by_part["part-02"][0]["stale"]
    status = "\n".join(study_status(topic))
    assert "nobody 4" in status and "declared on an earlier text.md (not counted): part-02" in status


def test_passage_keys_first_impressions_and_the_cli(topic: Topic, capsys) -> None:
    assert study_settings(topic)["passage_keys"] == {
        "first": ["structural", "questions"],
        "later": ["reception", "contrast"],
    }
    topic.data["analysis"] = {"passage_keys": {"first": "structural"}}
    with pytest.raises(SettingsError, match="passage_keys"):
        study_settings(topic)
    topic.data["analysis"] = {"passage_keys": {"first": ["questions"]}}
    topic.save()
    write_memo(topic, author_of(topic, "owner"), "first-impression", "Moje první čtení", "Kniha o kontrole.")
    write_memo(topic, author_of(topic, "owner"), "passage-choice", "Pasáže pro jemnou analýzu", "PARADOX: ...")
    root = str(topic.root)
    assert main(["status", root]) == 0
    out = capsys.readouterr().out
    assert "first impressions: owner 1" in out
    assert "keys for choosing passages: first questions; later reception, contrast; chosen in 1" in out
    assert main(["outline", root, "kniha"]) == 0
    assert "part-03  ## PARADOX  p. 3  kniha:s3:1 .. kniha:s3:2 (2)" in capsys.readouterr().out
    by = ["--by", "lead", "--prompt-version", "p@1"]
    assert main(["coverage", "add", root, "kniha", "--part", "part-02..part-03", "--how", "passages", *by]) == 0
    assert "part-02, part-03 read passages by lead" in capsys.readouterr().out
    assert main(["outline", root, "kniha", "--coverage"]) == 0
    assert "passages: lead" in capsys.readouterr().out
    assert main(["coverage", "list", root]) == 0
    assert "passages 2" in capsys.readouterr().out
