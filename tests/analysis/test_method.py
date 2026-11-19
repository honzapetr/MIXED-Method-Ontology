"""The method as orientation, strictness per study (T33): a toy method, never a hard-wired one."""

from pathlib import Path

import pytest
import yaml

from mmo.analysis.method import (
    SettingsError,
    check_method,
    current_phases,
    study_methods,
    study_settings,
)
from mmo.analysis.quote import find_quotation
from mmo.analysis.status import own_type_reminder, study_status
from mmo.analysis.store import Store, StoreError, author_of, write_memo
from mmo.cli import main
from mmo.core.topic import Topic, write_yaml

TOY = {
    "id": "toy",
    "name": "Toy method",
    "status": "draft",
    "version": "1",
    "summary": "A method made up for tests.",
    "research_design": {k: "x" for k in ("purpose", "questions", "prior_theory", "reasoning", "theory_output")},
    "code_types": ["motif"],
    "relation_types": [{"id": "echoes", "description": "one motif echoes another"}],
    "phases": [
        {
            "id": phase,
            "goal": f"do {phase}",
            "input": "segments",
            "output": ["codes"],
            "memos": ["analytic"],
            "model_role": "propose motifs with a quote",
            "researcher_decides": "which motifs to keep",
        }
        for phase in ("reading", "coding", "writing")
    ],
    "practices": ["read twice"],
    "conclusions": "by comparison",
}
PROFILE = "# m – model profile\n"  # noqa: RUF001 - profiles use the en dash
TEXT = "---\nsource: kn\n---\n\n<!-- page 1 (printed) · scan 1 · a.jpg -->\n\nMotiv řeky nás rozdělil.\n"


def make_env(tmp_path: Path, analysis: dict | None = None, methods: list[str] | None = None) -> Topic:
    env = tmp_path / "env"
    for method_id in methods or ["toy"]:
        folder = env / "methods" / method_id
        folder.mkdir(parents=True)
        (folder / "method.yaml").write_text(yaml.safe_dump({**TOY, "id": method_id}), encoding="utf-8")
    (env / "analysts").mkdir()
    (env / "analysts" / "m.md").write_text(PROFILE, encoding="utf-8")
    topic = Topic.create(env / "topics", "st", "S")
    topic.data["methods"] = methods or ["toy"]
    if analysis is not None:
        topic.data["analysis"] = analysis
    write_yaml(topic.root / "topic.yaml", topic.data)
    text = topic.source("kn").final_text_file
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(TEXT, encoding="utf-8", newline="\n")
    (text.parent / "source.yaml").write_text("title: K\n", encoding="utf-8")
    return Topic.load(topic.root)


def test_method_schema(tmp_path: Path) -> None:
    folder = tmp_path / "toy"
    folder.mkdir()
    (folder / "method.yaml").write_text(yaml.safe_dump(TOY), encoding="utf-8")
    assert check_method(folder) == []
    broken = {**TOY, "phases": [{**TOY["phases"][0], "human_gate": "x", "prompt": "prompts/reading.md"}]}
    (folder / "method.yaml").write_text(yaml.safe_dump(broken), encoding="utf-8")
    problems = check_method(folder)
    assert any("researcher_decides" in p for p in problems) and any("does not exist" in p for p in problems)
    (folder / "prompts").mkdir()
    (folder / "prompts" / "reading.md").write_text("---\nversion: 1\n---\nRead.\n", encoding="utf-8")
    ok = {**TOY, "phases": [{**TOY["phases"][0], "prompt": "prompts/reading.md"}, *TOY["phases"][1:]]}
    (folder / "method.yaml").write_text(yaml.safe_dump(ok), encoding="utf-8")
    assert check_method(folder) == [], "a versioned prompt per phase"


def test_defaults_leave_the_analysis_free(tmp_path: Path) -> None:
    topic = make_env(tmp_path)
    settings = study_settings(topic)
    assert settings.changed() == {} and settings["codebook"] == "emergent" and settings["model"]["phases"] == "all"
    store = Store(topic)
    owner = author_of(topic, "owner")
    store.add_code(owner, "own", code_type="not-in-the-vocabulary")
    assert own_type_reminder(topic, "code", "not-in-the-vocabulary") is None, "no memo asked by default"
    with pytest.raises(SettingsError, match="not a setting"):
        study_settings(make_env(tmp_path / "b", {"strict": True}))
    with pytest.raises(SettingsError, match="not one of"):
        study_settings(make_env(tmp_path / "c", {"codebook": "locked"}))


def test_phases_are_a_map_the_researcher_moves_on(tmp_path: Path) -> None:
    topic = make_env(tmp_path)
    store = Store(topic)
    toy = study_methods(topic)[0]
    owner = author_of(topic, "owner")
    store.set_phase(owner, toy, "writing")
    store.set_phase(owner, toy, "reading")  # back and forth, freely
    assert current_phases(store.history()) == {"toy": "reading"}
    assert [e.get("previous") for e in store.history() if e["op"] == "phase"] == [None, "writing"]
    with pytest.raises(StoreError, match="no phase"):
        store.set_phase(owner, toy, "dreaming")
    with pytest.raises(StoreError, match="the researcher says where"):
        store.set_phase(author_of(topic, "m", "chat@1"), toy, "coding")


def test_what_the_study_asks_for_is_kept(tmp_path: Path) -> None:
    topic = make_env(
        tmp_path,
        {
            "codebook": "fixed",
            "own_types": "ask_memo",
            "phases": "sequence",
            "model": {"phases": ["coding"]},
            "quotation_required": {"memos": ["analytic"]},
        },
    )
    store = Store(topic)
    owner = author_of(topic, "owner")
    with pytest.raises(StoreError, match="codebook is fixed"):
        store.add_code(owner, "new")
    toy = study_methods(topic)[0]
    store.set_phase(owner, toy, "reading")
    with pytest.raises(StoreError, match="next phase is coding"):
        store.set_phase(owner, toy, "writing")
    with pytest.raises(StoreError, match="only in the phases coding"):
        author_of(topic, "m", "chat@1")
    store.set_phase(owner, toy, "coding")
    assert author_of(topic, "m", "chat@1").kind == "model"
    with pytest.raises(StoreError, match="asks for a quotation"):
        write_memo(topic, owner, "analytic", "Bez citace")
    q = find_quotation("kn", TEXT, "Motiv řeky")
    assert write_memo(topic, owner, "analytic", "S citací", quotations=[q]).is_file()
    assert write_memo(topic, owner, "reflexive", "Moje pozice").is_file(), "other memo types stay free"
    assert "not in the vocabulary" in (own_type_reminder(topic, "relation", "my-relation") or "")
    assert own_type_reminder(topic, "relation", "echoes") is None


def test_several_methods_in_one_study(tmp_path: Path, capsys) -> None:
    topic = make_env(tmp_path, methods=["toy", "toy2"])
    base = ["--topics", str(topic.root.parent)]
    assert main([*base, "phase", "st", "coding", "--by", "owner"]) == 1, "the phase is in both methods"
    assert "--method" in capsys.readouterr().err
    assert main([*base, "phase", "st", "coding", "--method", "toy2", "--by", "owner"]) == 0
    assert main([*base, "phase", "st", "reading", "--method", "toy", "--by", "owner"]) == 0
    capsys.readouterr()
    assert main([*base, "status", "st"]) == 0
    out = capsys.readouterr().out
    assert "method toy - Toy method (version 1)" in out and "method toy2" in out
    assert " -> reading: do reading" in out and " -> coding: do coding" in out
    assert "the researcher decides: which motifs to keep" in out and "toy: read twice" in out


def test_status_reminds_without_conditions(tmp_path: Path) -> None:
    topic = make_env(tmp_path, {"own_types": "ask_memo"})
    store = Store(topic)
    owner = author_of(topic, "owner")
    store.add_code(owner, "a", code_type="motif")
    store.add_code(owner, "b", code_type="mine")
    store.merge_codes(owner, "a", ["b"])
    lines = "\n".join(study_status(topic))
    assert "merge-codes of a" in lines and "has no reason" in lines
    assert "own type 'mine'" not in lines, "b is superseded; only active codes are reminded"
    assert "settings: own_types=ask_memo" in lines and "made: 1 codes" in lines


def test_method_check_cli(tmp_path: Path, capsys) -> None:
    topic = make_env(tmp_path)
    methods = topic.root.parent.parent / "methods"
    assert main(["method", "check", "--methods", str(methods)]) == 0
    assert "toy: ok" in capsys.readouterr().out
