"""Many decisions of the researcher at once (T47): by reference or filter, each its own decision, one batch."""

from pathlib import Path

import pytest
import yaml

from mmo.analysis.method import study_methods
from mmo.analysis.quote import find_quotation
from mmo.analysis.review import decide_many, phases_when_written, proposals, select
from mmo.analysis.store import Store, StoreError, author_of, write_memo
from mmo.cli import main
from mmo.core.topic import Topic, write_yaml

PHASE = {"goal": "g", "input": "i", "output": ["codes"], "memos": ["analytic"], "researcher_decides": "r"}
TOY = {
    "id": "toy",
    "name": "Toy",
    "status": "draft",
    "version": "1",
    "summary": "s",
    "research_design": {k: "x" for k in ("purpose", "questions", "prior_theory", "reasoning", "theory_output")},
    "relation_types": [{"id": "echoes", "description": "d"}],
    "phases": [
        {**PHASE, "id": "reading", "model_role": "impressions", "model_proposes": ["memo"]},
        {**PHASE, "id": "coding", "model_role": "codes", "model_proposes": ["code", "coding", "memo"]},
    ],
    "conclusions": "c",
}
READER = """---
name: chapter-reader
description: Reads one part whole.
version: "2026-11-24"
writes: coding, memo
---
"""
POSITION = "---\nanalyst: m\nstatus: confirmed\nprofile_version: '1'\nroles:\n  - chapter-reader\n---\n\n# P\n"
TEXT = (
    "---\nsource: kn\n---\n\n<!-- page 1 (printed) · scan 1 · a.jpg -->\n\n"
    "Motiv řeky nás rozdělil. Spása přichází z kódu. Kontrola se obrací proti nám.\n"
)


@pytest.fixture
def topic(tmp_path: Path) -> Topic:
    env = tmp_path / "env"
    (env / "methods" / "toy").mkdir(parents=True)
    (env / "methods" / "toy" / "method.yaml").write_text(yaml.safe_dump(TOY), encoding="utf-8")
    (env / "analysts").mkdir()
    for model in ("m", "n"):
        (env / "analysts" / f"{model}.md").write_text(f"# {model} – model profile\n", encoding="utf-8")  # noqa: RUF001
    (env / ".agents" / "roles").mkdir(parents=True)
    (env / ".agents" / "roles" / "chapter-reader.md").write_text(READER, encoding="utf-8")
    topic = Topic.create(env / "topics", "st", "S")
    topic.data["methods"] = ["toy"]
    write_yaml(topic.root / "topic.yaml", topic.data)
    (topic.root / "positions").mkdir()
    (topic.root / "positions" / "m.md").write_text(POSITION, encoding="utf-8")
    text = topic.source("kn").final_text_file
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(TEXT, encoding="utf-8", newline="\n")
    (text.parent / "source.yaml").write_text("title: K\n", encoding="utf-8")
    return Topic.load(topic.root)


def q(words: str):
    return find_quotation("kn", TEXT, words)


def owner(topic: Topic):
    return author_of(topic, "owner")


def phase(topic: Topic, name: str) -> None:
    Store(topic).set_phase(owner(topic), study_methods(topic)[0], name)


@pytest.fixture
def waiting(topic: Topic) -> dict[str, str]:
    """reading: a memo of m; coding: codings of m (lead), of m in a run (chapter reader), of n."""
    phase(topic, "reading")
    memo = write_memo(topic, author_of(topic, "m", "chat@1"), "first-impression", "Dojem", "x").stem
    phase(topic, "coding")
    store = Store(topic)
    lead = store.apply_code(author_of(topic, "m", "chat@1"), "řeka", q("Motiv řeky"))["id"]
    run = store.start_run(author_of(topic, "m", "chat@1"), "m", "chapter-reader", ["kn p. 1"])["run"]
    reader = Store(topic).apply_code(author_of(topic, "m", run=run), "řeka", q("Spása přichází"))["id"]
    other = Store(topic).apply_code(author_of(topic, "n", "chat@1"), "kontrola", q("Kontrola se obrací"))["id"]
    return {"memo": f"memo:{memo}", "lead": f"coding:{lead}", "reader": f"coding:{reader}", "other": f"coding:{other}",
            "run": run}  # fmt: skip


def test_select_by_kind_author_role_run_and_phase(topic: Topic, waiting: dict[str, str]) -> None:
    refs = lambda **f: {p.ref for p in select(topic, **f)}  # noqa: E731
    assert refs(kind="coding") == {waiting["lead"], waiting["reader"], waiting["other"]}
    assert refs(kind="coding", author="n") == {waiting["other"]}
    assert refs(role="chapter-reader") == {waiting["reader"]} == refs(run=waiting["run"])
    assert refs(phase="reading") == {waiting["memo"]}
    assert waiting["lead"] in refs(phase="coding") and waiting["memo"] not in refs(phase="coding")
    assert refs(refs=[waiting["lead"], waiting["other"]], author="m") == {waiting["lead"]}
    with pytest.raises(StoreError, match="not waiting for a decision: coding:cd-9999"):
        select(topic, refs=["coding:cd-9999"])
    assert phases_when_written(Store(topic).history())[waiting["memo"]] == {"reading"}


def test_each_is_its_own_decision_with_the_same_note_in_one_batch(topic: Topic, waiting: dict[str, str]) -> None:
    with pytest.raises(StoreError, match="only the researcher decides"):
        decide_many(topic, author_of(topic, "m", "chat@1"), [waiting["lead"]], "accept")
    with pytest.raises(StoreError, match="needs a reason"):
        decide_many(topic, owner(topic), [waiting["lead"]], "reject")
    with pytest.raises(StoreError, match="one proposal at a time"):
        decide_many(topic, owner(topic), [waiting["lead"]], "edit")
    chosen = [p.ref for p in select(topic, kind="coding", author="m")]
    results = decide_many(topic, owner(topic), chosen, "accept", note="read the quoted places")
    events = [r["event"] for r in results]
    assert [e["target"] for e in events] == chosen and {e["verdict"] for e in events} == {"accepted"}
    assert {e["note"] for e in events} == {"read the quoted places"}
    assert len({e["batch"] for e in events}) == 1 and events[0]["batch"].startswith("batch-")
    assert events[0]["cascade"] and not events[1]["cascade"], "the first coding takes the proposed code with it"
    left = {p.ref for p in proposals(topic)}
    assert waiting["other"] in left and waiting["memo"] in left and waiting["lead"] not in left
    results = decide_many(topic, owner(topic), [waiting["other"], waiting["memo"]], "reject", reason="off topic")
    assert [r["event"]["reason"] for r in results] == ["off topic", "off topic"]
    assert [p.ref for p in proposals(topic)] == ["code:kontrola"], "a rejected coding leaves its code to decide"


def test_a_proposal_decided_with_another_is_skipped_and_an_error_stops_nothing(
    topic: Topic, waiting: dict[str, str]
) -> None:
    code_ref = "code:" + Store(topic).coding(waiting["other"].split(":")[1])["body"]
    results = decide_many(topic, owner(topic), [waiting["other"], code_ref, waiting["lead"]], "accept")
    assert "event" in results[0] and "skipped" in results[1] and "event" in results[2]
    assert waiting["reader"] in {p.ref for p in proposals(topic)}, "its code was accepted with the lead's coding"


def test_cli_by_filter_with_a_dry_run_first(topic: Topic, waiting: dict[str, str], capsys) -> None:
    root = str(topic.root)
    assert main(["review", "accept", root, "--by", "owner"]) == 1
    assert "which proposals?" in capsys.readouterr().out
    assert main(["review", "list", root, "--role", "chapter-reader"]) == 0
    assert waiting["reader"] in capsys.readouterr().out
    assert main(["review", "accept", root, "--kind", "coding", "--author", "m", "--dry-run", "--by", "owner"]) == 0
    out = capsys.readouterr().out
    assert f"would accept: {waiting['lead']}" in out and "nothing was written" in out
    assert len(proposals(topic)) == 4 + 2, "a dry run writes nothing (3 codings, a memo, 2 codes)"
    assert main(["review", "accept", root, "--from-run", waiting["run"], "--by", "owner", "--note", "ok"]) == 0
    assert "1 of 1 decided" in capsys.readouterr().out
    assert main(["review", "reject", root, "--phase", "reading", "--reason", "too early", "--by", "owner"]) == 0
    assert f"{waiting['memo']}: rejected" in capsys.readouterr().out
    assert main(["review", "accept", root, "--all", "--by", "owner"]) == 0
    assert "decided (batch-" in capsys.readouterr().out and proposals(topic) == []
