"""The critic of another maker through agy: who it may be, its brief, its run and what it may change (T46)."""

import json
from pathlib import Path

import pytest
import yaml

from mmo.analysis.critic import check_critic, maker_of, read_brief, round_section, run_critic, write_brief
from mmo.analysis.store import Store, StoreError, author_of, write_memo
from mmo.cli import main
from mmo.core.topic import Topic

PROFILE = """# {m} – model profile

> Status: confirmed
>
> Version: 2026-11-15 – raised when the position changes.

| id | `{m}` | harness |
| name, maker | {name}, {maker} | model card; maker |
"""  # noqa: RUF001 - profiles use the en dash
POSITION = "---\nanalyst: {m}\nprofile_version: '2026-11-15'\nstatus: confirmed\nroles:\n  - {role}\n---\n\n# P\n"
CRITIC_ROLE = """---
name: critic
description: A critic of another maker.
version: "2026-11-24"
writes: coding, memo
---

# Critic

Look for counter-evidence.
"""
TEMPLATE = """---
version: "2026-11-24"
method: toy
role: critic
---

# Brief of the critic

Study: <fill: the study and its questions>

## Round 1

Read: <fill: which parts of the sources, whole>

## Round 2

Compare with: <fill: the lead's memos>
"""
METHOD = {
    "id": "toy",
    "name": "Toy",
    "status": "draft",
    "version": "1",
    "phases": [],
    "roles": {"critic": "prompts/roles/critic.md"},
}


@pytest.fixture
def topic(tmp_path: Path) -> Topic:
    env = tmp_path / "env"
    for model, name, maker in (("lead", "Claude", "Anthropic"), ("gem", "Gemini", "Google DeepMind")):
        path = env / "analysts" / f"{model}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(PROFILE.format(m=model, name=name, maker=maker), encoding="utf-8")
    (env / ".agents" / "roles").mkdir(parents=True)
    (env / ".agents" / "roles" / "critic.md").write_text(CRITIC_ROLE, encoding="utf-8")
    method = env / "methods" / "toy"
    (method / "prompts" / "roles").mkdir(parents=True)
    (method / "method.yaml").write_text(yaml.safe_dump(METHOD), encoding="utf-8")
    (method / "prompts" / "roles" / "critic.md").write_text(TEMPLATE, encoding="utf-8")
    topic = Topic.create(env / "topics", "st", "S")
    topic.data["methods"] = ["toy"]
    topic.data["analysis"] = {"critic": {"analyst": "gem", "model": "gemini-4-neon-medium"}}
    topic.save()
    (topic.root / "positions").mkdir()
    (topic.root / "positions" / "lead.md").write_text(POSITION.format(m="lead", role="chapter-reader"), "utf-8")
    (topic.root / "positions" / "gem.md").write_text(POSITION.format(m="gem", role="critic"), "utf-8")
    return Topic.load(topic.root)


def owner(topic: Topic):
    return author_of(topic, "owner")


def ready_brief(topic: Topic) -> None:
    path = write_brief(topic, owner(topic))
    text = path.read_text(encoding="utf-8").replace("status: draft", "status: ready")
    text = text.replace("<fill: the study and its questions>", "st, q1").replace("<fill: which parts", "kniha ch. 3")
    text = text.replace(" of the sources, whole>", "").replace("<fill: the lead's memos>", "memos of the lead")
    path.write_text(text, encoding="utf-8")


DENIED = "denied by pre-tool hook"


def stream(text: str) -> str:
    rows = [
        {"event": "init", "init": {"model": "gemini-4-neon-medium"}},
        {"event": "step_update", "step_update": {"state": "DONE", "step_type": "run_command"}},
        {"event": "step_update", "step_update": {"state": "DONE", "step_type": "run_command", "x": DENIED}},
        {"event": "result", "result": {"status": "SUCCESS", "response": text}},
    ]  # fmt: skip
    return "\n".join(json.dumps(r) for r in rows)


def test_the_critic_is_of_another_maker(topic: Topic) -> None:
    assert maker_of(topic, "gem") == "Google DeepMind" and maker_of(topic, "lead") == "Anthropic"
    assert check_critic(topic) == []
    topic.data["analysis"] = {"critic": {"analyst": "lead2", "model": "claude-opus-5-5-high"}}
    (topic.root.parent.parent / "analysts" / "lead2.md").write_text(
        PROFILE.format(m="lead2", name="Claude", maker="Anthropic"), encoding="utf-8"
    )
    (topic.root / "positions" / "lead2.md").write_text(POSITION.format(m="lead2", role="critic"), "utf-8")
    assert any("same maker as lead" in p for p in check_critic(topic))


def test_the_critic_needs_its_confirmed_position_with_the_role(topic: Topic) -> None:
    (topic.root / "positions" / "gem.md").write_text(POSITION.format(m="gem", role="chapter-reader"), "utf-8")
    assert any("does not list the role critic" in p for p in check_critic(topic))
    (topic.root / "positions" / "gem.md").unlink()
    assert any("no position in the study" in p for p in check_critic(topic))


def test_the_brief_is_the_researchers_and_must_be_filled_in(topic: Topic) -> None:
    with pytest.raises(StoreError, match="the researcher writes the critic's brief"):
        write_brief(topic, author_of(topic, "lead", "p@1"))
    with pytest.raises(StoreError, match="no brief"):
        read_brief(topic)
    path = write_brief(topic, owner(topic))
    assert "template: toy/critic@2026-11-24" in path.read_text(encoding="utf-8")
    with pytest.raises(StoreError, match="not ready"):
        read_brief(topic)
    path.write_text(path.read_text(encoding="utf-8").replace("status: draft", "status: ready"), encoding="utf-8")
    with pytest.raises(StoreError, match="places to fill in"):
        read_brief(topic)
    ready_brief_text = "intro\n## Round 1\nread whole\n## Round 2\ncompare\n"
    assert "compare" not in round_section(ready_brief_text, 1) and "read whole" in round_section(ready_brief_text, 1)
    assert "read whole" not in round_section(ready_brief_text, 2) and "intro" in round_section(ready_brief_text, 2)


def test_a_run_keeps_everything_and_accepts_only_what_a_critic_may_write(topic: Topic) -> None:
    brief_path = topic.root / "critic" / "brief.md"
    ready_brief(topic)
    seen: dict = {}

    def agy(cmd, cwd, env, timeout):
        seen.update(cmd=cmd, cwd=cwd, env=env)
        critic = author_of(topic, "gem", run=env["MMO_CRITIC_RUN"])
        write_memo(topic, critic, "analytic", "Counter-evidence", "The end of chapter 3 says the opposite.")
        return 0, stream("Done: 1 memo."), ""

    with pytest.raises(StoreError, match="run round 1 first"):
        run_critic(topic, owner(topic), 2, runner=agy)
    record = run_critic(topic, owner(topic), 1, runner=agy)
    assert record["status"] == "ok" and record["round"] == 1 and record["violations"] == []
    assert seen["cmd"][1] == "-p" and seen["cmd"][3:] == ["--model", "gemini-4-neon-medium", "--output-format",
                                                            "stream-json", "--sandbox"]  # fmt: skip
    assert seen["env"]["MMO_ANALYST"] == "gem" and seen["env"]["MMO_CRITIC_ROUND"] == "1"
    prompt = seen["cmd"][2]
    assert "kniha ch. 3" in prompt and "memos of the lead" not in prompt, "round 1 sees only its own section"
    assert "role/critic@2026-11-24" in prompt and "--by gem --run run-0001" in prompt
    run_dir = topic.root / "critic" / "runs" / "run-0001"
    assert (run_dir / "prompt.md").read_text(encoding="utf-8") == prompt
    assert (run_dir / "response.md").read_text(encoding="utf-8") == "Done: 1 memo."
    assert "run_command" in (run_dir / "stream.jsonl").read_text(encoding="utf-8")
    assert record["steps"] == 2 and record["denied_by_guard"] == 1 and len(record["wrote"]) == 1
    event, closed = Store(topic).history()[-2:]
    assert event["op"] == "critic-run" and event["brief"]["template"] == "toy/critic@2026-11-24"
    assert closed["op"] == "run-closed" and closed["run"] == "run-0001", "the run (and the web) closes when agy ends"
    assert brief_path.is_file()

    def rogue(cmd, cwd, env, timeout):
        (cwd / "methods" / "toy" / "procedure.md").write_text("changed by the critic", encoding="utf-8")
        return 0, stream("I improved the method."), ""

    record = run_critic(topic, owner(topic), 2, runner=rogue)
    assert record["status"] == "violations" and record["violations"] == ["methods/toy/procedure.md"]
    assert "memos of the lead" in (topic.root / "critic" / "runs" / "run-0002" / "prompt.md").read_text("utf-8")


def test_cli_dry_run_and_list(topic: Topic, capsys) -> None:
    ready_brief(topic)
    root = str(topic.root)
    assert main(["critic", "run", root, "--round", "1", "--by", "owner", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "round 1: dry-run" in out and "-p <prompt.md> --model gemini-4-neon-medium" in out
    assert main(["critic", "list", root]) == 0
    assert "run-0001 round 1" in capsys.readouterr().out
    assert main(["critic", "brief", root, "--by", "owner"]) == 1, "the brief exists already"
