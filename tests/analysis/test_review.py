"""Proposals of models and the researcher's review (T29): decided in place, provenance kept, phases bind models."""

from pathlib import Path

import pytest
import yaml

from mmo.analysis.method import study_methods
from mmo.analysis.quote import find_quotation
from mmo.analysis.review import decide, proposals
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
        {**PHASE, "id": "reading", "model_role": "impressions only", "model_proposes": ["memo"]},
        {**PHASE, "id": "coding", "model_role": "codes with quotes", "model_proposes": ["code", "coding", "memo"]},
        {**PHASE, "id": "free", "model_role": "anything"},
    ],
    "conclusions": "c",
}
TEXT = (
    "---\nsource: kn\n---\n\n<!-- page 1 (printed) · scan 1 · a.jpg -->\n\n"
    "Motiv řeky nás rozdělil. Spása přichází z kódu.\n"
)


@pytest.fixture
def topic(tmp_path: Path) -> Topic:
    env = tmp_path / "env"
    (env / "methods" / "toy").mkdir(parents=True)
    (env / "methods" / "toy" / "method.yaml").write_text(yaml.safe_dump(TOY), encoding="utf-8")
    (env / "analysts").mkdir()
    (env / "analysts" / "m.md").write_text("# m – model profile\n", encoding="utf-8")  # noqa: RUF001
    topic = Topic.create(env / "topics", "st", "S")
    topic.data["methods"] = ["toy"]
    write_yaml(topic.root / "topic.yaml", topic.data)
    text = topic.source("kn").final_text_file
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(TEXT, encoding="utf-8", newline="\n")
    (text.parent / "source.yaml").write_text("title: K\n", encoding="utf-8")
    return Topic.load(topic.root)


def q(words: str):
    return find_quotation("kn", TEXT, words)


def phase(topic: Topic, name: str) -> None:
    Store(topic).set_phase(author_of(topic, "owner"), study_methods(topic)[0], name)


def test_the_phase_binds_what_a_model_proposes_never_the_researcher(topic: Topic) -> None:
    model = author_of(topic, "m", "chat@1")
    owner = author_of(topic, "owner")
    phase(topic, "reading")
    with pytest.raises(StoreError, match="does not propose a coding"):
        Store(topic).apply_code(model, "řeka", q("Motiv řeky"))
    assert write_memo(topic, model, "first-impression", "Dojem", quotations=[q("Motiv řeky")]).is_file()
    assert Store(topic).apply_code(owner, "řeka", q("Motiv řeky"))["status"] == "accepted", "the researcher: free"
    phase(topic, "coding")
    assert Store(topic).apply_code(model, "spása", q("Spása přichází"))["status"] == "proposed"
    with pytest.raises(StoreError, match="does not propose a relation"):
        Store(topic).relate(model, "code:reka", "echoes", "code:spasa")
    phase(topic, "free")
    assert Store(topic).relate(model, "code:reka", "echoes", "code:spasa")["status"] == "proposed"


def test_a_model_proposes_changes_of_the_codebook_does_not_make_them(topic: Topic) -> None:
    owner = author_of(topic, "owner")
    model = author_of(topic, "m", "chat@1")
    store = Store(topic)
    store.add_code(owner, "řeka")
    for change in (
        lambda: store.rename_code(model, "reka", "voda"),
        lambda: store.merge_codes(model, "reka", ["reka"]),
        lambda: store.split_code(model, "reka", ["a", "b"]),
    ):
        with pytest.raises(StoreError, match="the researcher"):
            change()
    with pytest.raises(StoreError, match="only its own proposals"):
        store.withdraw(model, "code:reka")
    mine = store.add_code(model, "moje")
    store.withdraw(model, f"code:{mine['id']}", reason="nepotřebné")
    assert store.code(mine["id"])["status"] == "withdrawn"


def test_review_accept_edit_reject_in_place(topic: Topic) -> None:
    model = author_of(topic, "m", "skad-fine@1")
    owner = author_of(topic, "owner")
    store = Store(topic)
    coding = store.apply_code(model, "spása", q("Spása přichází z kódu"))
    store.add_code(model, "řeka", code_type="motif")
    store.add_code(model, "zbytečný")
    waiting = {p.ref: p for p in proposals(topic)}
    assert set(waiting) == {"code:spasa", f"coding:{coding['id']}", "code:reka", "code:zbytecny"}
    listed = waiting[f"coding:{coding['id']}"]
    assert "spasa <- kn p. 1: 'Spása přichází z kódu'" in listed.summary and "skad-fine@1" in listed.provenance

    event = decide(topic, owner, f"coding:{coding['id']}", "accept")
    assert event["cascade"] == ["code:spasa"], "a coding taken over takes its code with it"
    decide(topic, owner, "code:reka", "edit", changes={"label": "voda", "code_type": "element"})
    with pytest.raises(StoreError, match="needs a reason"):
        decide(topic, owner, "code:zbytecny", "reject")
    decide(topic, owner, "code:zbytecny", "reject", reason="duplicates spása")

    store = Store(topic)
    reka = store.code("reka")
    assert reka["status"] == "edited" and reka["label"] == "voda" and reka["author"] == "m", "provenance stays"
    assert reka["decided"]["changes"] == {"label": ["řeka", "voda"], "code_type": ["motif", "element"]}
    assert store.code("zbytecny")["decided"]["reason"] == "duplicates spása"
    assert store.coding(coding["id"])["generated_by"]["prompt_version"] == "skad-fine@1"
    assert proposals(topic) == []
    with pytest.raises(StoreError, match="not a proposal waiting"):
        decide(topic, owner, "code:reka", "accept")
    assert [e["verdict"] for e in store.history() if e["op"] == "review"] == ["accepted", "edited", "rejected"]


def test_only_a_person_decides_and_rejecting_a_code_takes_its_proposed_codings(topic: Topic) -> None:
    model = author_of(topic, "m", "chat@1")
    owner = author_of(topic, "owner")
    store = Store(topic)
    coding = store.apply_code(model, "spása", q("Spása přichází"))
    with pytest.raises(StoreError, match="only the researcher decides"):
        decide(topic, model, "code:spasa", "accept")
    event = decide(topic, owner, "code:spasa", "reject", reason="not in the text's sense")
    assert event["cascade"] == [f"coding:{coding['id']}"]
    assert Store(topic).coding(coding["id"])["status"] == "rejected"


def test_a_rejected_code_still_used_by_the_researcher_is_refused(topic: Topic) -> None:
    model = author_of(topic, "m", "chat@1")
    owner = author_of(topic, "owner")
    Store(topic).add_code(model, "spása")
    Store(topic).apply_code(owner, "spasa", q("Spása přichází"))
    with pytest.raises(StoreError, match="used by codings the researcher holds"):
        decide(topic, owner, "code:spasa", "reject", reason="x")


def test_memos_are_decided_too_and_alternatives_can_be_asked_for(topic: Topic) -> None:
    topic.data["analysis"] = {"model": {"alternatives": True}}
    write_yaml(topic.root / "topic.yaml", topic.data)
    topic = Topic.load(topic.root)
    model = author_of(topic, "m", "chat@1")
    owner = author_of(topic, "owner")
    with pytest.raises(StoreError, match="alternative"):
        write_memo(topic, model, "analytic", "Čtení", quotations=[q("Motiv řeky")])
    memo = write_memo(
        topic, model, "analytic", "Čtení", "Řeka dělí.", quotations=[q("Motiv řeky")], alternatives=["Řeka spojuje."]
    )
    memo_id = memo.stem
    assert [p.ref for p in proposals(topic, "memo")] == [f"memo:{memo_id}"]
    with pytest.raises(StoreError, match="says what changed"):
        decide(topic, owner, f"memo:{memo_id}", "edit")
    decide(topic, owner, f"memo:{memo_id}", "edit", note="shortened the second paragraph by hand")
    front = yaml.safe_load(memo.read_text(encoding="utf-8").split("---")[1])
    assert front["status"] == "edited" and front["alternatives"] == ["Řeka spojuje."]
    assert front["decided"]["by"] == "owner" and "Řeka dělí." in memo.read_text(encoding="utf-8")


def test_cli_review(topic: Topic, capsys) -> None:
    base = ["--topics", str(topic.root.parent)]
    model = ["--by", "m", "--prompt-version", "chat@1"]
    assert main([*base, "code", "apply", "st", "spása", "kn", "Spása přichází", *model]) == 0
    capsys.readouterr()
    assert main([*base, "review", "list", "st"]) == 0
    out = capsys.readouterr().out
    assert "code:spasa" in out and "coding:cd-0001" in out and "2 proposals wait" in out
    assert main([*base, "review", "accept", "st", "coding:cd-0001", "--by", "m", "--prompt-version", "x"]) == 1
    assert main([*base, "review", "edit", "st", "coding:cd-0001", "--code", "spása z kódu", "--by", "owner"]) == 0
    assert "coding:cd-0001: edited" in capsys.readouterr().out
    assert main([*base, "review", "list", "st"]) == 0
    assert "code:spasa" in capsys.readouterr().out, "the model's code still waits: the coding now has another code"
    with pytest.raises(SystemExit):
        main([*base, "review", "reject", "st", "code:spasa", "--by", "owner"])  # --reason is required
    assert (
        main([*base, "review", "reject", "st", "code:spasa", "--reason", "the text means more", "--by", "owner"]) == 0
    )
    capsys.readouterr()
    assert main([*base, "status", "st"]) == 0
    assert "proposals of models waiting for the researcher: 0" in capsys.readouterr().out
