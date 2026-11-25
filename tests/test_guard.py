# ruff: noqa: RUF001 - profiles use the en dash in their titles and version lines
"""mmo-guard: Claude Code hooks for the analyst (T22)."""

import io
import json
import os
from pathlib import Path

import pytest

from mmo import guard

PROFILE = """# m – model profile

> Status: {status} (2026-11-15, written by `m`). To be confirmed by the owner.
>
> Version: 2026-11-15 – raised whenever the Position, Identity, the layers or the tendencies change.

## Position

I am m.
"""

POSITION = """---
analyst: m
kind: model
study: s
method: skad
profile_version: '{version}'
status: {status}
written: '2026-11-16'
---

# Position of m in s
"""


def _write(path: Path, text: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


@pytest.fixture
def root(tmp_path: Path, monkeypatch) -> Path:
    """A research environment with one model profile and one study; temp is elsewhere (pytest runs inside it)."""
    monkeypatch.setattr(guard.tempfile, "gettempdir", lambda: str(tmp_path / "systemp"))
    root = tmp_path / "env"
    _write(root / "AGENTS.md")
    _write(root / "analysts" / "README.md", "# Analysts\n")
    _write(root / "analysts" / "_template-model.md", "# <model-id> – model profile\n")
    _write(root / "analysts" / "m.md", PROFILE.format(status="proposed"))
    _write(root / "analysts" / "owner.md", "# owner – researcher profile\n")
    _write(root / "methods" / "skad" / "agent-rules.md")
    study = root / "topics" / "s"
    _write(study / "topic.yaml", "title: S\n")
    _write(study / "memos" / "2026-11-13-a.md")
    _write(study / "sources" / "k" / "source.yaml")
    _write(study / "sources" / "k" / "notes.md")
    _write(study / "sources" / "k" / "text.md", "the data")
    _write(study / "sources" / "k" / "segments.jsonl")
    _write(study / "work" / "ocr.txt")
    return root.resolve()


def _open_study(root: Path, version: str = "2026-11-15", status: str = "confirmed") -> None:
    _write(root / "analysts" / "m.md", PROFILE.format(status="confirmed"))
    _write(root / "topics" / "s" / "positions" / "m.md", POSITION.format(version=version, status=status))


def _decide(root: Path, tool: str, **tool_input) -> str | None:
    result = guard.pre_tool_use({"tool_name": tool, "tool_input": tool_input, "cwd": str(root)}, root)
    return result["hookSpecificOutput"]["permissionDecision"] if result else None


def _reason(root: Path, tool: str, **tool_input) -> str:
    result = guard.pre_tool_use({"tool_name": tool, "tool_input": tool_input, "cwd": str(root)}, root)
    return result["hookSpecificOutput"]["permissionDecisionReason"]


def test_outside_the_environment_is_denied(root, tmp_path):
    _write(tmp_path / "test3" / "analysts" / "m.md")
    assert _decide(root, "Read", file_path=str(tmp_path / "test3" / "analysts" / "m.md")) == "deny"
    assert _decide(root, "Glob", pattern="*.md", path=str(tmp_path / "test3")) == "deny"
    assert _decide(root, "Write", file_path=str(tmp_path / "notes.md"), content="x") == "deny"
    assert _decide(root, "Read", file_path=str(root / "AGENTS.md")) is None
    assert _decide(root, "Read", file_path="../test3/analysts/m.md") == "deny"


def test_temp_and_the_projects_own_claude_folder_are_allowed(root, tmp_path):
    assert _decide(root, "Write", file_path=str(tmp_path / "systemp" / "scratch.txt"), content="x") is None
    memory = guard.claude_project_dir(root) / "memory" / "MEMORY.md"
    assert _decide(root, "Read", file_path=str(memory)) is None


def test_study_data_closed_until_profile_and_position_confirmed(root):
    text = str(root / "topics" / "s" / "sources" / "k" / "text.md")
    assert _decide(root, "Read", file_path=text) == "deny"
    assert "profile not confirmed" in _reason(root, "Read", file_path=text)
    _write(root / "analysts" / "m.md", PROFILE.format(status="confirmed"))
    assert "no position in the study" in _reason(root, "Read", file_path=text)
    _open_study(root, status="proposed")
    assert "position not confirmed" in _reason(root, "Read", file_path=text)
    _open_study(root, version="2026-11-01")
    assert "profile version" in _reason(root, "Read", file_path=text)
    _open_study(root)
    assert _decide(root, "Read", file_path=text) is None


def test_what_is_closed_and_what_stays_open(root):
    for rel in ("sources/k/text.md", "sources/k/segments.jsonl", "work/ocr.txt"):
        assert _decide(root, "Read", file_path=str(root / "topics" / "s" / rel)) == "deny", rel
    for rel in ("topic.yaml", "memos/2026-11-13-a.md", "sources/k/source.yaml", "sources/k/notes.md"):
        assert _decide(root, "Read", file_path=str(root / "topics" / "s" / rel)) is None, rel
    assert _decide(root, "Glob", pattern="topics/s/sources/**/*") is None  # names only


def test_content_search_over_closed_data(root):
    assert _decide(root, "Grep", pattern="x") == "deny"  # the root holds the study
    assert _decide(root, "Grep", pattern="x", path="topics/s") == "deny"
    assert _decide(root, "Grep", pattern="x", path="methods") is None
    assert _decide(root, "Grep", pattern="x", path="topics/s/memos") is None
    _open_study(root)
    assert _decide(root, "Grep", pattern="x") is None


def test_mmo_quote_reads_the_text_so_it_is_closed_too(root):
    def bash(command: str) -> str | None:
        return _decide(root, "Bash", command=command)

    assert bash('uv run mmo quote find s k "the data"') == "deny"
    assert "works on the study s, which stays closed" in _reason(root, "Bash", command="mmo quote check s")
    assert bash("uv run mmo source check s") is None, "commands that do not read the text stay open"
    assert bash('uv run mmo quote find other k "x"') is None, "not a study of this environment"
    assert bash("uv run mmo run start s --role chapter-reader --input k --by m --prompt-version p") == "deny"
    _open_study(root)
    assert bash("uv run mmo run start s --role chapter-reader --input k --by m --prompt-version p") is None
    assert bash('uv run mmo quote find s k "the data"') is None
    assert bash("mmo quote check s") is None


def test_the_analysis_store_is_written_through_mmo_under_ones_own_id(root):
    _open_study(root)
    store = root / "topics" / "s" / "analysis" / "codebook.yaml"
    _write(store, "codes: []\n")

    def decide(tool: str, **data) -> str | None:
        result = guard.pre_tool_use({"tool_name": tool, "tool_input": data, "cwd": str(root)}, root, "m")
        return result["hookSpecificOutput"]["permissionDecision"] if result else None

    assert decide("Write", file_path=str(store), content="codes: [x]") == "deny"
    assert decide("Edit", file_path=str(store), old_string="[]", new_string="[x]") == "deny"
    assert decide("Read", file_path=str(store)) is None, "reading the store is free"
    assert decide("Bash", command="echo x >> topics/s/analysis/codebook.yaml") == "deny"
    assert decide("Bash", command="sed -i s/a/b/ topics/s/analysis/codebook.yaml") == "deny"
    assert decide("Bash", command="cat topics/s/analysis/codebook.yaml") is None
    assert decide("Bash", command='uv run mmo code add s "nahota" --by m --prompt-version chat@1') is None
    assert decide("Bash", command='uv run mmo code add s "nahota" --by owner') == "deny", "no writing as someone else"
    assert decide("Bash", command="mmo memo add s --type analytic --title t --by=owner") == "deny"
    memo = root / "topics" / "s" / "memos" / "2026-11-19-b.md"
    assert decide("Write", file_path=str(memo), content="---\nauthor: m\n---\n") is None, "memos stay free Markdown"


def test_only_the_owner_confirms(root):
    profile = str(root / "analysts" / "m.md")
    assert _decide(root, "Edit", file_path=profile, old_string="proposed (2026", new_string="confirmed (2026") == "ask"
    assert _decide(root, "Edit", file_path=profile, old_string="I am m.", new_string="I am m, a model.") is None
    position = str(root / "topics" / "s" / "positions" / "m.md")
    assert _decide(root, "Write", file_path=position, content=POSITION.format(version="1", status="proposed")) is None
    assert _decide(root, "Write", file_path=position, content=POSITION.format(version="1", status="confirmed")) == "ask"
    memo = str(root / "topics" / "s" / "memos" / "2026-11-13-a.md")
    assert _decide(root, "Write", file_path=memo, content="status: confirmed\n") is None


def test_bash(root, tmp_path):
    def bash(command: str) -> str | None:
        return _decide(root, "Bash", command=command)

    assert bash("cat topics/s/sources/k/text.md") == "deny"
    assert bash("head -5 topics/s/sources/*/text.md") == "deny"
    assert bash("grep -rn stav topics") == "deny"
    assert bash("rg stav") == "deny"
    assert bash("ls -R topics/s") is None
    assert bash("grep -n Status analysts/m.md") is None
    assert bash("git status --short") is None
    assert bash(f'cd "{(tmp_path / "test3").as_posix()}" && ls') == "deny"
    assert bash(f'ls "{(tmp_path / "test3").as_posix()}"') == "deny"
    assert bash("cat ../test3/AGENTS.md") == "deny"
    assert bash(f'cd "{root.as_posix()}" && ls analysts/ topics/') is None
    assert bash("sed -i 's/Status: proposed/Status: confirmed/' analysts/m.md") == "ask"
    assert bash('echo "status: confirmed" >> topics/s/positions/m.md') == "ask"
    assert bash("curl -s https://example.org/a/b") is None
    # shell devices and the temp folder are not paths of the environment (test7: `2>/dev/null` was denied)
    assert bash("ls topics/ && ls topics/*/positions/ 2>/dev/null; ls analysts/") is None
    assert bash("git status > /dev/null 2>&1") is None
    temp = "/tmp" if os.name == "nt" else (tmp_path / "systemp").as_posix()  # Git Bash maps /tmp to temp
    assert bash(f"echo x > {temp}/probe.txt") is None


@pytest.mark.skipif(os.name != "nt", reason="Git Bash spellings of paths exist only on Windows")
def test_git_bash_drive_paths():
    assert guard.to_path("/g/Some dir/x", Path("C:/")).as_posix().lower().startswith("g:/some dir")


def test_session_start_loads_only_the_model(root):
    context = guard.session_start({"model": "m"}, root)
    assert context.startswith("Guards: on")
    assert "status proposed, version 2026-11-15" in context
    assert "I am m." in context
    assert "settled with the researcher" in context
    assert "topics/s" not in context
    unknown = guard.session_start({}, root)
    assert "did not name the model" in unknown
    assert "m (proposed, version 2026-11-15)" in unknown
    assert "owner" not in unknown.split("Model profiles here:")[1]
    assert "no profile analysts/x.md" in guard.session_start({"model": {"id": "x"}}, root)


def test_main_reads_stdin_and_writes_hook_json(root, monkeypatch, capsys):
    event = {"tool_name": "Read", "tool_input": {"file_path": str(root / "topics/s/sources/k/text.md")}}
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(root))
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(json.dumps(event).encode("utf-8"))))
    assert guard.main(["pre-tool-use"]) == 0
    assert json.loads(capsys.readouterr().out)["hookSpecificOutput"]["permissionDecision"] == "deny"
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(b'{"source": "startup"}')))
    assert guard.main(["session-start"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["hookSpecificOutput"]["additionalContext"].startswith("Guards: on")
    assert guard.main(["nonsense"]) == 2


def test_only_the_researcher_sets_the_phase(root):
    _open_study(root)
    result = guard.pre_tool_use(
        {"tool_name": "Bash", "tool_input": {"command": "uv run mmo phase s coding --by m"}}, root, "m"
    )
    assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert (
        guard.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": "uv run mmo status s"}}, root, "m") is None
    )


def test_only_the_researcher_decides_proposals(root):
    _open_study(root)

    def decide(command: str) -> str | None:
        result = guard.pre_tool_use({"tool_name": "Bash", "tool_input": {"command": command}}, root, "m")
        return result["hookSpecificOutput"]["permissionDecision"] if result else None

    assert decide("uv run mmo review accept s code:x --by m") == "deny"
    assert decide("uv run mmo review accept s --role chapter-reader --by owner") == "deny", "a filter too (T47)"
    assert decide("uv run mmo review reject s --all --reason x") == "deny"
    assert decide("uv run mmo review list s --role chapter-reader") is None
    assert decide("uv run mmo review list s") is None, "a model may see what waits"


def _history(root: Path, slug: str, *events: dict) -> None:
    _write(root / "topics" / slug / "analysis" / "history.jsonl", "".join(json.dumps(e) + "\n" for e in events))


def test_web_search_only_during_an_open_run_of_an_approving_study(root, monkeypatch):
    """T44, T48, ADR 0015: the approval is the study's; the web is open only while a run that may search it is open."""
    monkeypatch.delenv("MMO_STUDY", raising=False)

    def web(model: str | None = "m") -> str | None:
        event = {"tool_name": "WebSearch", "tool_input": {"query": "x"}, "cwd": str(root)}
        result = guard.pre_tool_use(event, root, model)
        return result["hookSpecificOutput"]["permissionDecision"] if result else None

    assert _decide(root, "WebSearch", query="Nazi v AI dobe recenze") == "deny"
    assert "analysis.web_search" in _reason(root, "WebFetch", url="https://example.org")
    assert _decide(root, "Bash", command="uv run mmo context list s") == "deny", "mmo context is closed with the study"
    assert _decide(root, "Bash", command="uv run mmo outline s k") == "deny", "the outline reads text.md (T36)"
    assert _decide(root, "Bash", command="uv run mmo coverage list s") == "deny"
    _write(root / "topics" / "s" / "topic.yaml", "title: S\nanalysis:\n  web_search: [m]\n")
    assert web() == "deny", "an approval alone does not open the web: a run does"
    assert "mmo run close" in _reason(root, "WebSearch", query="x")
    started = {"op": "run", "run": "run-0001", "analyst": "m", "role": "context-searcher", "web": True}
    _history(root, "s", started)
    assert web() is None and _decide(root, "WebFetch", url="https://example.org") is None
    assert web("n") == "deny", "the run is m's, not n's"
    _write(root / "topics" / "b" / "topic.yaml", "title: B\n")
    monkeypatch.setenv("MMO_STUDY", "b")
    assert web() == "deny", "an open run in study s does not open the web for study b"
    monkeypatch.delenv("MMO_STUDY")
    _write(root / "topics" / "s" / "topic.yaml", "title: S\nanalysis:\n  web_search: []\n")
    assert web() == "deny", "the researcher withdrew the approval"
    _write(root / "topics" / "s" / "topic.yaml", "title: S\nanalysis:\n  web_search: [m]\n")
    _history(root, "s", started, {"op": "run-closed", "run": "run-0001"})
    assert web() == "deny", "closed with the run"
    _history(root, "s", {**started, "web": False})
    assert web() == "deny", "a run recorded without the web"


def test_a_blind_probe_stays_blind(root):
    """T45: when the harness names the subagent blind-probe, the study, other mmo commands and the web stay closed."""
    _open_study(root)
    _write(root / "topics" / "s" / "topic.yaml", "title: S\nanalysis:\n  web_search: [m]\n")

    def probe(tool: str, **tool_input) -> str | None:
        event = {"tool_name": tool, "tool_input": tool_input, "cwd": str(root), "agent_type": "blind-probe"}
        result = guard.pre_tool_use(event, root)
        return result["hookSpecificOutput"]["permissionDecision"] if result else None

    assert probe("Read", file_path=str(root / "topics" / "s" / "sources" / "k" / "text.md")) == "deny"
    assert probe("Read", file_path=str(root / "topics" / "s" / "memos" / "2026-11-13-a.md")) == "deny"
    assert probe("Read", file_path=str(root / "topics" / "s" / "topic.yaml")) == "deny"
    assert probe("Grep", pattern="x", path=str(root)) == "deny"
    assert probe("WebSearch", query="x") == "deny", "even where the study approves the web"
    assert probe("Bash", command="uv run mmo quote find s k x") == "deny"
    assert probe("Bash", command="cat topics/s/sources/k/notes.md") == "deny"
    assert probe("Read", file_path=str(root / "analysts" / "m.md")) is None
    assert probe("Read", file_path=str(root / "topics" / "s" / "positions" / "m.md")) is None
    assert (
        probe("Bash", command="uv run mmo memo add s --by m --run run-0001 --type reflexive --title P --text x") is None
    )
    assert _decide(root, "Read", file_path=str(root / "topics" / "s" / "memos" / "2026-11-13-a.md")) is None, (
        "the lead is not blind"
    )


def _agy(root, name: str, args: dict, model: str | None = "m", round_no: str | None = None) -> dict:
    event = {"toolCall": {"name": name, "args": args}, "cwd": str(root), "workspacePaths": [str(root)]}
    return guard.agy_pre_tool_use(event, root, model, round_no)


def test_the_guard_as_a_hook_of_agy(root, monkeypatch):
    """T46: the same checks for the Antigravity CLI; no objection is 'ask', or 'allow' inside a critic's run."""
    text = str(root / "topics" / "s" / "sources" / "k" / "text.md")
    assert _agy(root, "read_file", {"Path": text})["decision"] == "deny"
    assert _agy(root, "run_command", {"CommandLine": f'cat "{text}"'})["decision"] == "deny"
    assert _agy(root, "read_file", {"Path": str(root / "AGENTS.md")}) == {"decision": "ask"}
    monkeypatch.setenv("MMO_CRITIC_RUN", "run-0001")
    assert _agy(root, "read_file", {"Path": str(root / "AGENTS.md")}) == {"decision": "allow"}
    _open_study(root)
    assert _agy(root, "read_file", {"Path": text}) == {"decision": "allow"}
    assert _agy(root, "search_web", {"query": "x"})["decision"] == "deny", "web only in an open run that may"
    assert _agy(root, "read_file", {"Path": str(root.parent / "elsewhere.txt")})["decision"] == "deny"
    analysis = str(root / "topics" / "s" / "analysis" / "codings.jsonl")
    assert "through mmo" in _agy(root, "write_file", {"Path": analysis, "Content": "x"})["reason"]
    assert _agy(root, "write_file", {"Path": str(root / "methods" / "x.md"), "Content": "x"})["decision"] == "deny"
    by_other = "uv run mmo memo add s --by n --run run-0001 --type analytic --title T --text x"
    assert _agy(root, "run_command", {"CommandLine": by_other})["decision"] == "deny"
    own = by_other.replace("--by n", "--by m")
    assert _agy(root, "run_command", {"CommandLine": own}) == {"decision": "allow"}


def test_round_one_of_the_critic_reads_independently(root, monkeypatch):
    monkeypatch.setenv("MMO_CRITIC_RUN", "run-0001")
    _open_study(root)
    memo = str(root / "topics" / "s" / "memos" / "2026-11-13-a.md")
    _write(root / "topics" / "s" / "positions" / "lead.md", "lead")
    assert _agy(root, "read_file", {"Path": memo}, round_no="1")["decision"] == "deny"
    assert _agy(root, "read_file", {"Path": memo}, round_no="2") == {"decision": "allow"}
    lead = str(root / "topics" / "s" / "positions" / "lead.md")
    assert _agy(root, "read_file", {"Path": lead}, round_no="1")["decision"] == "deny"
    own = str(root / "topics" / "s" / "positions" / "m.md")
    assert _agy(root, "read_file", {"Path": own}, round_no="1") == {"decision": "allow"}
    assert _agy(root, "grep_search", {"SearchPath": str(root), "Query": "x"}, round_no="1")["decision"] == "deny"
    assert _agy(root, "run_command", {"CommandLine": "uv run mmo memo list s"}, round_no="1")["decision"] == "deny"
    assert _agy(root, "run_command", {"CommandLine": "uv run mmo code list s"}, round_no="1") == {"decision": "allow"}
    add = "uv run mmo memo add s --by m --run run-0001 --type analytic --title T --text x"
    assert _agy(root, "run_command", {"CommandLine": add}, round_no="1") == {"decision": "allow"}


def test_the_brief_is_not_a_models_and_the_critic_is_no_claude_subagent(root):
    brief = str(root / "topics" / "s" / "critic" / "brief.md")
    assert "researcher" in _reason(root, "Write", file_path=brief, content="x")
    assert _decide(root, "Bash", command=f'echo x > "{brief}"') == "deny"
    event = {"tool_name": "Read", "tool_input": {"file_path": str(root / "AGENTS.md")}, "cwd": str(root)}
    result = guard.pre_tool_use({**event, "agent_type": "critic"}, root)
    assert "mmo critic run" in result["hookSpecificOutput"]["permissionDecisionReason"]


def test_main_answers_agy(root, monkeypatch, capsys):
    event = {
        "toolCall": {"name": "read_file", "args": {"Path": str(root / "AGENTS.md")}},
        "workspacePaths": [str(root)],
    }
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(json.dumps(event).encode("utf-8"))))
    monkeypatch.delenv("MMO_CRITIC_RUN", raising=False)
    assert guard.main(["agy-pre-tool-use"]) == 0
    assert json.loads(capsys.readouterr().out) == {"decision": "ask"}


def test_agy_may_read_its_own_task_logs(root):
    log = guard.agy_brain_dir() / "conv" / ".system_generated" / "tasks" / "task-8.log"
    assert _agy(root, "read_file", {"Path": str(log)}) == {"decision": "ask"}
    assert _agy(root, "read_file", {"Path": str(guard.agy_brain_dir().parent / "settings.json")})["decision"] == "deny"
