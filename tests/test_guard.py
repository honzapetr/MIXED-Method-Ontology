# ruff: noqa: RUF001 - profiles use the en dash in their titles and version lines
"""mmo-guard: Claude Code hooks for the analyst (T22)."""

import io
import json
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
    _write(study / "sources" / "k" / "segments" / "book.jsonl")
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
    for rel in ("sources/k/text.md", "sources/k/segments/book.jsonl", "work/ocr.txt"):
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
    assert bash("echo x > /tmp/probe.txt") is None


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
