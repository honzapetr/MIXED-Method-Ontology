"""Blind probe of a model's prior knowledge of a source (T45, ADR 0015)."""

from pathlib import Path

import pytest

from mmo.analysis.context import start_round
from mmo.analysis.probe import probes, start_probe, title_and_authors
from mmo.analysis.status import study_status
from mmo.analysis.store import Store, StoreError, author_of, write_memo
from mmo.cli import main
from mmo.core.topic import Topic, write_yaml

MODEL = "# {m} – model profile\n\n> Status: confirmed\n"  # noqa: RUF001 - profiles use the en dash
PROBE = """---
name: blind-probe
description: Says what a model knows of a source from training, given only its title and author.
version: "2026-11-24"
writes: memo
---
"""
POSITION = "---\nanalyst: {m}\nstatus: confirmed\nprofile_version: '1'\nroles:\n  - blind-probe\n---\n\n# P\n"
TEXT = '---\nsource: "kniha"\n---\n\n<!-- page 1 (printed) · scan 1 · a.jpg -->\n\nAI je nový prorok.\n'


@pytest.fixture
def topic(tmp_path: Path) -> Topic:
    env = tmp_path / "env"
    (env / "analysts").mkdir(parents=True)
    (env / ".agents" / "roles").mkdir(parents=True)
    (env / ".agents" / "roles" / "blind-probe.md").write_text(PROBE, encoding="utf-8")
    topic = Topic.create(env / "topics", "st", "S")
    (topic.root / "positions").mkdir()
    for model in ("lead", "critic"):
        (env / "analysts" / f"{model}.md").write_text(MODEL.format(m=model), encoding="utf-8")
        (topic.root / "positions" / f"{model}.md").write_text(POSITION.format(m=model), encoding="utf-8")
    (topic.root / "positions" / "owner.md").write_text("# owner\n", encoding="utf-8")
    source = topic.add_source("kniha", "book", "Kniha")
    meta = source.metadata()
    meta["citation"] = {"authors": ["Lukáš Sedláček"], "title": "Nazí v AI době", "year": 2025}
    write_yaml(source.metadata_file, meta)
    source.final_text_file.write_text(TEXT, encoding="utf-8", newline="\n")
    topic.add_source("recenze", "article", "Recenze", role="context", about=["kniha"])
    return topic


def lead(topic: Topic):
    return author_of(topic, "lead", "skad/context-analysis@1")


def test_the_probe_is_given_only_the_title_and_the_author(topic: Topic, capsys) -> None:
    assert title_and_authors(topic, "kniha") == ("Nazí v AI době", ["Lukáš Sedláček"])
    with pytest.raises(StoreError, match=r"citation.authors"):
        title_and_authors(topic, "recenze")
    assert (
        main(["probe", "start", str(topic.root), "--by", "lead", "--prompt-version", "p@1", "--source", "kniha"]) == 0
    )
    out = capsys.readouterr().out
    assert "run-0001: blind probe of lead on kniha" in out
    assert "title: Nazí v AI době; author: Lukáš Sedláček" in out
    assert "--by lead --run run-0001 --type reflexive --prior-knowledge source:kniha" in out
    event = Store(topic).history()[-1]
    assert event["role"] == "blind-probe" and event["input"][0] == "source:kniha"
    assert "AI je nový prorok" not in out, "nothing of the text"


def test_a_probe_memo_records_when_it_was_written(topic: Topic) -> None:
    store = Store(topic)
    run = start_probe(store, lead(topic), "kniha", "critic")["run"]
    root = str(topic.root)
    by_run = ["--by", "critic", "--run", run, "--title", "Prior knowledge of kniha", "--text", "Not known."]
    assert main(["memo", "add", root, *by_run, "--type", "analytic", "--prior-knowledge", "source:kniha"]) == 1
    assert main(["memo", "add", root, *by_run, "--type", "reflexive", "--prior-knowledge", "source:kniha"]) == 0
    [probe] = probes(topic)
    assert (probe["source"], probe["model"], probe["status"]) == ("kniha", "critic", "proposed")
    assert probe["before_search"] is True and probe["met_source_before"] is False and probe["compared_in"] == []
    memo = (topic.root / "memos" / f"{probe['memo']}.md").read_text(encoding="utf-8")
    assert "source:kniha" in memo and "role: blind-probe" in memo

    # the lead meets the source, the search begins, and only then is the lead probed
    write_memo(topic, lead(topic), "first-impression", "Opening", "...", about=["source:kniha"])
    plan = write_memo(topic, author_of(topic, "owner"), "search-plan", "Plan", "q1 ...").stem
    start_round(Store(topic), lead(topic), f"memo:{plan}", "first round")
    run = start_probe(Store(topic), lead(topic), "kniha", "lead")["run"]
    late = write_memo(
        topic,
        author_of(topic, "lead", run=run),
        "reflexive",
        "Prior knowledge of kniha",
        "Known.",
        prior_knowledge={"source": "kniha", "model": "lead", "before_search": False, "met_source_before": True},
    )
    assert late.is_file()
    assert main(["memo", "add", root, "--by", "lead", "--run", run, "--type", "reflexive", "--title", "P",
                 "--text", "x", "--prior-knowledge", "source:kniha"]) == 0  # fmt: skip
    newest = [p for p in probes(topic) if p["model"] == "lead"][-1]
    assert newest["before_search"] is False and newest["met_source_before"] is True


def test_context_memos_compare_the_probe_and_status_reminds_of_missing_probes(topic: Topic) -> None:
    status = "\n".join(study_status(topic))
    assert "no blind probe of critic on kniha" in status and "no blind probe of lead on kniha" in status
    assert "owner on kniha" not in status, "the researcher is not probed"
    assert "recenze" not in status.split("reminders")[1], "context sources are not probed"
    probe_run = start_probe(Store(topic), lead(topic), "kniha", "lead")
    assert probe_run["web"] is False, "a probe never opens the web (T48)"
    run = probe_run["run"]
    probe = write_memo(
        topic,
        author_of(topic, "lead", run=run),
        "reflexive",
        "Prior knowledge of kniha",
        "The author: a technology entrepreneur (vaguely familiar).",
        prior_knowledge={"source": "kniha", "model": "lead", "before_search": True, "met_source_before": False},
    ).stem
    status = "\n".join(study_status(topic))
    assert f"kniha by lead: {probe} (not compared yet)" in status
    assert "no blind probe of lead on kniha" not in status
    write_memo(
        topic, lead(topic), "context", "Context of kniha", "Confirmed: ...", about=["source:kniha", f"memo:{probe}"]
    )
    assert "(compared in 1 memos)" in "\n".join(study_status(topic))
