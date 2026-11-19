"""The analysis store and the free toolbox: integrity is checked, the method never is (T32, ADR 0013)."""

import json
from pathlib import Path

import pytest
import yaml

from mmo.analysis.quote import find_quotation
from mmo.analysis.store import Store, StoreError, author_of, check_store, write_memo
from mmo.cli import main
from mmo.core.topic import Topic

TEXT = """---
source: "kn"
---

# Kniha

<!-- page 15 (printed) · scan 1 · a.jpg -->

Mohl jsem rozvést téma nahoty, kterou vnímám jako upřímný stav.

AI je nový prorok a spása přichází z kódu.

<!-- page 16 (printed) · scan 2 · b.jpg -->

My Američané jsme zvláštní, vyvolený národ.
"""

MODEL_PROFILE = "# m – model profile\n\n> Status: confirmed\n"  # noqa: RUF001 - profiles use the en dash


@pytest.fixture
def topic(tmp_path: Path) -> Topic:
    """A study inside an environment: <env>/topics/st, <env>/analysts/m.md is a model."""
    env = tmp_path / "env"
    (env / "analysts").mkdir(parents=True)
    (env / "analysts" / "m.md").write_text(MODEL_PROFILE, encoding="utf-8")
    topic = Topic.create(env / "topics", "st", "S")
    text = topic.source("kn").final_text_file
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(TEXT, encoding="utf-8", newline="\n")
    (text.parent / "source.yaml").write_text("title: Kniha\n", encoding="utf-8")
    return topic


def q(words: str):
    return find_quotation("kn", TEXT, words)


def test_who_does_it_is_required_and_a_model_names_its_prompt(topic: Topic) -> None:
    with pytest.raises(StoreError, match="--by"):
        author_of(topic, None)
    with pytest.raises(StoreError, match="--prompt-version"):
        author_of(topic, "m")
    model = author_of(topic, "m", "skad-fine-analysis@1")
    person = author_of(topic, "owner")
    assert (model.kind, model.status, person.kind, person.status) == ("model", "proposed", "person", "accepted")


def test_any_label_and_any_type_are_welcome(topic: Topic) -> None:
    store = Store(topic)
    owner = author_of(topic, "owner")
    code = store.add_code(owner, "Spása skrze AI", code_type="my-own-type", method="toy")
    assert code["id"] == "spasa-skrze-ai" and code["code_type"] == "my-own-type", "no vocabulary is enforced"
    with pytest.raises(StoreError, match="exists already"):
        store.add_code(owner, "Spása skrze AI")
    saved = yaml.safe_load((topic.root / "analysis" / "codebook.yaml").read_text(encoding="utf-8"))
    assert saved["codes"][0]["author"] == "owner" and saved["codes"][0]["status"] == "accepted"


def test_coding_points_to_a_quotation_and_a_new_label_adds_the_code(topic: Topic) -> None:
    store = Store(topic)
    model = author_of(topic, "m", "chat@2026-11-19")
    coding = store.apply_code(model, "AI jako prorok", q("AI je nový prorok"), method="toy")
    assert coding["body"] == "ai-jako-prorok" and coding["status"] == "proposed"
    assert coding["target"]["pages"] == [15] and coding["generated_by"]["prompt_version"] == "chat@2026-11-19"
    rows = (topic.root / "analysis" / "codings.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(rows[0])["id"] == "cd-0001"


def test_rename_merge_split_recode_withdraw_keep_the_history(topic: Topic) -> None:
    store = Store(topic)
    owner = author_of(topic, "owner")
    a = store.apply_code(owner, "spása", q("spása přichází z kódu"))
    b = store.apply_code(owner, "prorok", q("AI je nový prorok"))
    store.rename_code(owner, "spasa", "spása z kódu")
    assert store.code("spasa")["label"] == "spása z kódu", "the id stays"

    store.merge_codes(owner, "spasa", ["prorok"], reason="one figure")
    assert store.code("prorok")["status"] == "superseded" and store.coding(b["id"])["body"] == "spasa"
    assert store.coding(b["id"])["was"] == ["prorok"]

    new = store.split_code(owner, "spasa", ["technologická spása", "prorocká figura"])
    assert store.code("spasa")["superseded_by"] == [c["id"] for c in new]
    assert store.coding(a["id"])["body"] == "spasa", "codings wait for the researcher to recode them"
    store.recode(owner, a["id"], "technologicka-spasa")
    assert store.coding(a["id"])["body"] == "technologicka-spasa"

    store.withdraw(owner, f"coding:{b['id']}", reason="too broad")
    assert store.coding(b["id"])["status"] == "withdrawn", "kept for the history, not deleted"
    ops = [e["op"] for e in Store(topic).history()]
    assert ops.count("add-code") == 4 and {"rename-code", "merge-codes", "split-code", "recode", "withdraw"} <= set(ops)
    assert all("state" in e and e["at"] for e in Store(topic).history())


def test_relations_and_memos_point_to_anything_that_exists(topic: Topic) -> None:
    store = Store(topic)
    owner = author_of(topic, "owner")
    store.add_code(owner, "spása")
    store.add_code(owner, "vyvolenost")
    rel = store.relate(owner, "code:spasa", "story_link", "code:vyvolenost", evidence=[q("vyvolený národ")])
    assert rel["evidence"][0]["pages"] == [16]
    with pytest.raises(StoreError, match="does not exist"):
        store.relate(owner, "code:spasa", "x", "code:nothing")
    with pytest.raises(StoreError, match="not a reference"):
        store.relate(owner, "spasa", "x", "code:spasa")

    memo = write_memo(
        topic,
        author_of(topic, "m", "chat@1"),
        "analytic",
        "Spása a vyvolenost",
        "Obě figury sdílejí slib.",
        about=[f"relation:{rel['id']}", "source:kn"],
        quotations=[q("vyvolený národ")],
        method="toy",
    )
    front = yaml.safe_load(memo.read_text(encoding="utf-8").split("---")[1])
    assert front["status"] == "proposed" and front["basis"]["quotations"][0]["exact"] == "vyvolený národ"
    assert front["about"] == ["relation:rel-0001", "source:kn"] and "# Spása a vyvolenost" in memo.read_text("utf-8")
    store = Store(topic)
    assert store.check_ref(f"memo:{front['id']}")


def test_check_finds_hand_edits_and_broken_quotations(topic: Topic) -> None:
    store = Store(topic)
    owner = author_of(topic, "owner")
    store.apply_code(owner, "spása", q("spása přichází z kódu"))
    assert check_store(topic) == []

    codebook = topic.root / "analysis" / "codebook.yaml"
    codebook.write_text(codebook.read_text(encoding="utf-8").replace("label: spása", "label: Spása"), encoding="utf-8")
    assert [f.problem for f in check_store(topic)] == ["edited by hand since the last mmo operation (--record)"]
    assert check_store(topic, record_hand_edits=True, by="owner") == []
    assert Store(topic).history()[-1]["op"] == "hand-edit" and check_store(topic) == []

    text = topic.source("kn").final_text_file
    text.write_text(TEXT.replace("spása přichází z kódu", "spasení přichází"), encoding="utf-8", newline="\n")
    assert "quotation gone" in check_store(topic)[0].problem


def test_cli_toolbox(topic: Topic, capsys) -> None:
    base = ["--topics", str(topic.root.parent)]
    assert main([*base, "code", "apply", "st", "spása", "kn", "spása přichází z kódu", "--by", "owner"]) == 0
    assert "coding cd-0001: spasa <- kn p. 15" in capsys.readouterr().out
    assert main([*base, "code", "apply", "st", "x", "kn", "neexistuje", "--by", "owner"]) == 1
    assert "not in the final text" in capsys.readouterr().err
    assert main([*base, "code", "add", "st", "prorok", "--by", "m"]) == 1, "a model names its prompt version"
    assert main([*base, "code", "add", "st", "prorok", "--by", "m", "--prompt-version", "chat@1"]) == 0
    assert main([*base, "relation", "add", "st", "code:spasa", "supports", "code:prorok", "--by", "owner"]) == 0
    assert (
        main(
            [
                *base,
                "memo",
                "add",
                "st",
                "--type",
                "reflexive",
                "--title",
                "Moje čtení",
                "--by",
                "owner",
                "--quote",
                "kn",
                "upřímný stav",
                "--about",
                "code:spasa",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert main([*base, "code", "list", "st"]) == 0
    out = capsys.readouterr().out
    assert "spasa: spása - 1 codings" in out and "prorok: prorok - 0 codings (proposed)" in out
    assert main([*base, "analysis", "check", "st"]) == 0
    assert main([*base, "quote", "check", "st"]) == 0


def test_cli_quote_with_a_page_on_the_source(topic: Topic, capsys) -> None:
    base = ["--topics", str(topic.root.parent), "memo", "add", "st", "--type", "analytic", "--title", "T"]
    assert main([*base, "--quote", "kn@16", "vyvolený národ", "--by", "owner"]) == 0
    assert main([*base, "--quote", "kn@15", "vyvolený národ", "--by", "owner"]) == 1, "not on that page"
    assert "not at the place given" in capsys.readouterr().err
