"""Roles of subagents and their runs: what a role may write is checked, never how it reads (T43, ADR 0014)."""

import json
from pathlib import Path

import pytest

from mmo.analysis.method import check_method, load_method, prompt_version
from mmo.analysis.quote import find_quotation
from mmo.analysis.roles import check_roles, load_roles
from mmo.analysis.status import study_status
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
"""

MODEL_PROFILE = "# m – model profile\n\n> Status: confirmed\n"  # noqa: RUF001 - profiles use the en dash
READER = """---
name: chapter-reader
description: Reads one part of a source whole and returns reading notes with exact quotations.
version: "2026-11-24"
writes: memo
---

Read the part whole.
"""
FINDER = """---
name: instance-finder
description: Finds instances and counter-instances of one code across a source.
version: "2026-11-24.1"
writes: coding, memo
---

Find instances.
"""
PREPARER = """---
name: source-preparer
description: Brings one source to its final text.
version: "1"
writes: none
---
"""


def position(roles: list[str]) -> str:
    listed = "".join(f"  - {r}\n" for r in roles)
    return f"---\nanalyst: m\nstatus: confirmed\nprofile_version: '1'\nroles:\n{listed}---\n\n# Position\n"


@pytest.fixture
def env(tmp_path: Path) -> Path:
    env = tmp_path / "env"
    (env / "analysts").mkdir(parents=True)
    (env / "analysts" / "m.md").write_text(MODEL_PROFILE, encoding="utf-8")
    roles = env / ".agents" / "roles"
    roles.mkdir(parents=True)
    (roles / "chapter-reader.md").write_text(READER, encoding="utf-8")
    (roles / "instance-finder.md").write_text(FINDER, encoding="utf-8")
    (roles / "source-preparer.md").write_text(PREPARER, encoding="utf-8")
    return env


@pytest.fixture
def topic(env: Path) -> Topic:
    topic = Topic.create(env / "topics", "st", "S")
    text = topic.source("kn").final_text_file
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(TEXT, encoding="utf-8", newline="\n")
    (text.parent / "source.yaml").write_text("title: Kniha\n", encoding="utf-8")
    (topic.root / "positions").mkdir()
    (topic.root / "positions" / "m.md").write_text(
        position(["chapter-reader", "instance-finder", "source-preparer"]), encoding="utf-8"
    )
    return topic


def lead(topic: Topic):
    return author_of(topic, "m", "skad/fine-analysis@2026-11-24")


def q(words: str):
    return find_quotation("kn", TEXT, words)


def test_a_role_file_names_its_version_and_what_it_writes(env: Path) -> None:
    roles = load_roles(env)
    assert roles["chapter-reader"].prompt_version == "role/chapter-reader@2026-11-24"
    assert roles["instance-finder"].writes == {"coding", "memo"}
    assert roles["source-preparer"].writes == set(), "'none': nothing in the analysis"
    (env / ".agents" / "roles" / "bad.md").write_text("---\nname: other\nwrites: theory\n---\n", encoding="utf-8")
    problems = check_roles(env)["bad"]
    assert any("file name" in p for p in problems) and any("no version" in p for p in problems)
    assert any("unknown kinds" in p for p in problems)


def test_a_run_needs_the_role_in_the_models_position(topic: Topic) -> None:
    store = Store(topic)
    (topic.root / "positions" / "m.md").write_text(position(["chapter-reader"]), encoding="utf-8")
    with pytest.raises(StoreError, match="takes no role 'instance-finder'"):
        store.start_run(lead(topic), "m", "instance-finder", ["kn p. 15"])
    with pytest.raises(StoreError, match="no role 'critic'"):
        store.start_run(lead(topic), "m", "critic", ["kn"])
    with pytest.raises(StoreError, match="--input"):
        store.start_run(lead(topic), "m", "chapter-reader", [])
    with pytest.raises(StoreError, match="roles are for models"):
        store.start_run(author_of(topic, "owner"), "owner", "chapter-reader", ["kn"])
    event = store.start_run(lead(topic), "m", "chapter-reader", ["kn p. 15"], note="opening")
    assert (event["run"], event["analyst"], event["role"]) == ("run-0001", "m", "chapter-reader")
    assert event["prompt_version"] == "role/chapter-reader@2026-11-24" and event["input"] == ["kn p. 15"]
    assert event["author"] == "m" and event["generated_by"]["prompt_version"] == "skad/fine-analysis@2026-11-24"
    assert Store(topic).start_run(author_of(topic, "owner"), "m", "chapter-reader", ["kn"])["run"] == "run-0002"


def test_a_subagent_writes_in_its_run_with_the_runs_role_and_prompt(topic: Topic) -> None:
    run = Store(topic).start_run(lead(topic), "m", "chapter-reader", ["kn p. 15"])["run"]
    reader = author_of(topic, "m", run=run)
    assert (reader.role, reader.run, reader.prompt_version) == ("chapter-reader", run, "role/chapter-reader@2026-11-24")
    path = write_memo(topic, reader, "first-impression", "Reading notes p. 15", "notes", quotations=[q("AI je nový")])
    text = path.read_text(encoding="utf-8")
    assert "role: chapter-reader" in text and f"run: {run}" in text and "status: proposed" in text
    with pytest.raises(StoreError, match="writes memo, not a coding"):
        Store(topic).apply_code(reader, "prorok", q("AI je nový prorok"))
    history = Store(topic).history()
    assert history[-1]["generated_by"] == {
        "model": "m",
        "prompt_version": "role/chapter-reader@2026-11-24",
        "role": "chapter-reader",
        "run": run,
    }


def test_an_instance_finder_codes_with_existing_codes_only(topic: Topic) -> None:
    store = Store(topic)
    store.add_code(author_of(topic, "owner"), "Spása skrze AI")
    run = store.start_run(lead(topic), "m", "instance-finder", ["code spasa-skrze-ai in kn"])["run"]
    finder = author_of(topic, "m", run=run)
    coding = Store(topic).apply_code(finder, "spasa-skrze-ai", q("spása přichází z kódu"))
    assert coding["generated_by"]["role"] == "instance-finder" and coding["status"] == "proposed"
    with pytest.raises(StoreError, match="not a code"):
        Store(topic).apply_code(finder, "A new label", q("AI je nový prorok"))
    assert Store(topic).run_records(run) == [f"coding:{coding['id']}"]
    assert check_store(topic) == []


def test_a_run_is_bound_to_its_model_and_prompt(topic: Topic) -> None:
    run = Store(topic).start_run(lead(topic), "m", "chapter-reader", ["kn"])["run"]
    with pytest.raises(StoreError, match="not of owner"):
        author_of(topic, "owner", run=run)
    with pytest.raises(StoreError, match="works from role/chapter-reader"):
        author_of(topic, "m", "chat@2026-11-24", run=run)
    assert author_of(topic, "m", "role/chapter-reader@2026-11-24", run=run).run == run
    with pytest.raises(StoreError, match="no run 'run-0099'"):
        author_of(topic, "m", run="run-0099")
    with pytest.raises(StoreError, match="does not start runs"):
        Store(topic).start_run(author_of(topic, "m", run=run), "m", "chapter-reader", ["kn"])
    preparer = Store(topic).start_run(lead(topic), "m", "source-preparer", ["kn"])["run"]
    with pytest.raises(StoreError, match="writes nothing in the analysis"):
        write_memo(topic, author_of(topic, "m", run=preparer), "context", "C")


def test_the_check_finds_a_record_whose_run_does_not_match(topic: Topic) -> None:
    store = Store(topic)
    store.add_code(author_of(topic, "owner"), "Prorok")
    run = store.start_run(lead(topic), "m", "instance-finder", ["kn"])["run"]
    Store(topic).apply_code(author_of(topic, "m", run=run), "prorok", q("AI je nový prorok"))
    rows = (topic.root / "analysis" / "codings.jsonl").read_text(encoding="utf-8").splitlines()
    record = json.loads(rows[0])
    record["generated_by"]["run"] = "run-0042"
    (topic.root / "analysis" / "codings.jsonl").write_text(json.dumps(record) + "\n", encoding="utf-8")
    problems = [f.problem for f in check_store(topic)]
    assert any("run-0042, which is not in the history" in p for p in problems)


def test_cli_starts_and_lists_runs_and_lists_roles(topic: Topic, env: Path, capsys: pytest.CaptureFixture) -> None:
    root = str(topic.root)
    by = ["--by", "m", "--prompt-version", "skad/fine-analysis@2026-11-24"]
    assert main(["run", "start", root, *by, "--role", "chapter-reader", "--input", "kn p. 15"]) == 0
    out = capsys.readouterr().out
    assert "run-0001: m as chapter-reader (role/chapter-reader@2026-11-24)" in out and "--run run-0001" in out
    words = ["kn", "AI je nový prorok"]
    assert main(["memo", "add", root, "--by", "m", "--run", "run-0001", "--type", "first-impression",
                 "--title", "Notes", "--text", "n", "--quote", *words]) == 0  # fmt: skip
    capsys.readouterr()
    assert main(["run", "list", root]) == 0
    out = capsys.readouterr().out
    assert "input: kn p. 15" in out and "wrote: memo:" in out and "1 runs" in out
    assert main(["status", root]) == 0
    assert "runs of subagents: 1 (chapter-reader 1)" in capsys.readouterr().out
    assert main(["role", "list", "--env", str(env)]) == 0
    out = capsys.readouterr().out
    assert "chapter-reader (role/chapter-reader@2026-11-24) writes memo" in out
    assert "source-preparer (role/source-preparer@1) writes nothing in the analysis" in out


METHOD = """id: toy
name: Toy
status: draft
version: "1"
summary: s
research_design: {purpose: p, questions: q, prior_theory: t, reasoning: r, theory_output: o}
relation_types: [{id: rel, description: d}]
conclusions: c
phases:
  - {id: read, goal: g, input: i, output: [memos], memos: [analytic], model_role: m, researcher_decides: d,
     prompt: prompts/read.md}
roles:
  critic: prompts/roles/critic.md
"""


def test_method_names_prompts_of_phases_and_roles_with_versions(tmp_path: Path) -> None:
    folder = tmp_path / "toy"
    (folder / "prompts" / "roles").mkdir(parents=True)
    (folder / "method.yaml").write_text(METHOD, encoding="utf-8")
    (folder / "prompts" / "read.md").write_text("---\nversion: 2026-11-24\n---\nRead.\n", encoding="utf-8")
    assert check_method(folder) == ["role critic: prompt prompts/roles/critic.md does not exist"]
    (folder / "prompts" / "roles" / "critic.md").write_text("no version here\n", encoding="utf-8")
    assert check_method(folder) == ["role critic: prompt prompts/roles/critic.md has no 'version:' line"]
    (folder / "prompts" / "roles" / "critic.md").write_text("---\nversion: 1\n---\n", encoding="utf-8")
    assert check_method(folder) == []
    method = load_method(tmp_path, "toy")
    assert prompt_version(method, "read") == "toy/read@2026-11-24"
    assert prompt_version(method, "nothing") is None


def test_status_names_the_prompt_of_the_current_phase(topic: Topic, env: Path) -> None:
    folder = env / "methods" / "toy"
    (folder / "prompts" / "roles").mkdir(parents=True)
    (folder / "method.yaml").write_text(METHOD, encoding="utf-8")
    (folder / "prompts" / "read.md").write_text('---\nversion: "2026-11-24"\n---\n', encoding="utf-8")
    data = topic.data | {"methods": ["toy"]}
    topic.data = data
    topic.save()
    Store(topic).set_phase(author_of(topic, "owner"), load_method(env / "methods", "toy"), "read")
    lines = "\n".join(study_status(Topic.load(topic.root)))
    assert "the model's prompt: prompts/read.md - write with --prompt-version toy/read@2026-11-24" in lines
