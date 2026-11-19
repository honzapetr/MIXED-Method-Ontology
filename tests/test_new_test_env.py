"""tools/new_test_env.py: a clean test copy of the research environment in zkusebna/."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "new_test_env", Path(__file__).resolve().parent.parent / "tools" / "new_test_env.py"
)
nte = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(nte)


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def layout(tmp_path: Path) -> dict[str, Path]:
    workshop, source, zkusebna = tmp_path / "ws", tmp_path / "research", tmp_path / "zkusebna"
    workshop.mkdir()
    _write(source / ".gitignore", ".env\n.venv/\nscratch/\ntopics/*/sources/**/*.jpg\n")
    _write(source / "AGENTS.md")
    _write(source / "pyproject.toml", '[tool.uv.sources]\nmmo = { path = "../ws", editable = true }\n')
    _write(source / "uv.lock", 'source = { editable = "../ws" }\n')
    _write(source / "analysts" / "model-a.md")
    _write(source / "analysts" / "model-b.md")
    _write(source / "topics" / "t" / "sources" / "s" / "files" / "p001.jpg")
    _write(source / "topics" / "t" / "sources" / "s" / "text.md")
    _write(source / ".env", "SECRET=1")
    _write(source / ".venv" / "lib.py")
    _write(source / "scratch" / "tmp.py")
    _write(source / "untracked.md")
    _write(source / ".editorconfig")
    _write(source / "tools" / "agents_sync.py")
    _write(source / ".agents" / "skills" / "s" / "SKILL.md")
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "add", ".gitignore", "AGENTS.md", "analysts", "topics"], check=True)
    subprocess.run(
        ["git", "-C", str(source), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"],
        check=True,
    )
    return {"workshop": workshop, "source": source, "zkusebna": zkusebna}


def _run(layout: dict[str, Path], *extra: str) -> None:
    args = ["--source", str(layout["source"]), "--zkusebna", str(layout["zkusebna"])]
    assert nte.main([*args, "--workshop", str(layout["workshop"]), "--no-sync", *extra]) == 0


def test_copies_what_git_sees_without_secrets_or_environments(layout):
    _run(layout)
    dest = layout["zkusebna"] / "test1"
    assert (dest / "AGENTS.md").exists()
    assert (dest / "untracked.md").exists()
    assert (dest / "topics/t/sources/s/text.md").exists()
    assert (dest / ".agents/skills/s/SKILL.md").exists()
    for path in (".env", ".venv", "scratch", ".git", "topics/t/sources/s/files/p001.jpg"):
        assert not (dest / path).exists(), path
    assert (layout["zkusebna"] / "_log.tsv").read_text(encoding="utf-8").count("\ttest1\t") == 1


def test_input_documents_kept_out_of_git_are_still_copied(layout):
    source = layout["source"]
    _write(source / "topics" / ".gitignore", "local/sources/\n")
    _write(source / "topics" / "local" / "topic.yaml")
    _write(source / "topics" / "local" / "sources" / "s" / "text.md")
    _write(source / "topics" / "local" / "sources" / "s" / "files" / "p001.jpg")
    _run(layout)
    dest = layout["zkusebna"] / "test1"
    assert (dest / "topics/local/topic.yaml").exists()
    assert (dest / "topics/local/sources/s/text.md").exists()
    assert not (dest / "topics/local/sources/s/files/p001.jpg").exists()  # the root rules still apply
    assert not (dest / "scratch").exists()


def test_project_files_and_the_workshop_path(layout):
    _run(layout, "probe")
    dest = layout["zkusebna"] / "probe"
    assert '"../../ws"' in (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert '"../../ws"' in (dest / "uv.lock").read_text(encoding="utf-8")
    for path in (".gitignore", ".editorconfig", "tools/agents_sync.py"):
        assert (dest / path).exists(), path
    assert not (dest / ".env").exists()


def test_without_project_files(layout):
    _run(layout, "bare", "--without-project-files")
    dest = layout["zkusebna"] / "bare"
    for path in (".gitignore", ".editorconfig", "pyproject.toml", "uv.lock", "tools"):
        assert not (dest / path).exists(), path
    assert (dest / "AGENTS.md").exists()


def test_options(layout):
    _run(layout, "--without-profile", "model-a", "--with-source-files", "--git")
    dest = layout["zkusebna"] / "test1"
    assert not (dest / "analysts/model-a.md").exists()
    assert (dest / "analysts/model-b.md").exists()
    assert (dest / "topics/t/sources/s/files/p001.jpg").exists()
    assert (dest / ".git").exists()
    _run(layout)
    assert (layout["zkusebna"] / "test2").exists()


def test_refuses_instructions_above_and_existing_target(layout, tmp_path):
    _write(tmp_path / "CLAUDE.md")
    with pytest.raises(SystemExit):
        _run(layout)
    (tmp_path / "CLAUDE.md").unlink()
    _run(layout, "same")
    with pytest.raises(SystemExit):
        _run(layout, "same")


def _commit(source: Path, message: str) -> None:
    subprocess.run(["git", "-C", str(source), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(source), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", message],
        check=True,
    )


def _study(layout: dict[str, Path]) -> Path:
    """A research environment with a study: topic, a memo, a position, a profile; committed."""
    source = layout["source"]
    _write(source / "topics" / "t" / "topic.yaml", "title: T\n")
    _write(source / "topics" / "t" / "memos" / "old.md", "old memo\n")
    _write(source / "topics" / "README.md", "how topics work\n")
    _write(source / "analysts" / "model-a.md", "> Status: proposed\n> Version: v1\n")
    _commit(source, "study")
    return source


def test_carry_takes_the_study_work_of_an_earlier_copy(layout):
    source = _study(layout)
    _run(layout, "one")
    one = layout["zkusebna"] / "one"
    # work done in the first test copy
    _write(one / "topics" / "t" / "topic.yaml", "title: T\nquestions: [q1]\n")
    _write(one / "topics" / "t" / "positions" / "model-a.md", "profile_version: v1\nstatus: confirmed\n")
    _write(one / "analysts" / "model-a.md", "> Status: confirmed\n> Version: v1\n")
    (one / "topics" / "t" / "memos" / "old.md").unlink()
    _write(one / "topics" / "t" / "sources" / "s" / "text.md", "rebuilt by the copy")  # machine: not carried
    _write(one / "topics" / "README.md", "edited by the agent\n")  # environment: reported only
    _write(one / "AGENTS.md", "edited by the agent")  # environment: reported only
    # meanwhile the environment moves on
    _write(source / "AGENTS.md", "new instructions")
    _write(source / "topics" / "t" / "sources" / "s" / "text.md", "new text")
    _commit(source, "environment moves on")

    _run(layout, "two", "--carry", "one")
    two = layout["zkusebna"] / "two"
    assert (two / "topics/t/topic.yaml").read_text(encoding="utf-8") == "title: T\nquestions: [q1]\n"
    assert (two / "topics/t/positions/model-a.md").exists()
    assert "confirmed" in (two / "analysts/model-a.md").read_text(encoding="utf-8")
    assert not (two / "topics/t/memos/old.md").exists(), "deleted in the copy, deleted again"
    assert (two / "topics/t/sources/s/text.md").read_text(encoding="utf-8") == "new text", "machine files are new"
    assert (two / "AGENTS.md").read_text(encoding="utf-8") == "new instructions", "instructions come new"
    assert (two / "topics/README.md").read_text(encoding="utf-8") == "how topics work\n"
    assert "--carry one" in (layout["zkusebna"] / "_log.tsv").read_text(encoding="utf-8")

    # the work grows: a memo written in the second copy; the third carries both
    _write(two / "topics" / "t" / "memos" / "new.md", "written in two\n")
    _run(layout, "three", "--carry", "two")
    three = layout["zkusebna"] / "three"
    assert (three / "topics/t/memos/new.md").exists()
    assert (three / "topics/t/topic.yaml").read_text(encoding="utf-8") == "title: T\nquestions: [q1]\n"
    assert (three / "topics/t/positions/model-a.md").exists() and not (three / "topics/t/memos/old.md").exists()


def test_carry_stops_on_a_conflict_until_a_side_is_chosen(layout, capsys):
    source = _study(layout)
    _run(layout, "one")
    one = layout["zkusebna"] / "one"
    _write(one / "topics" / "t" / "topic.yaml", "title: from the test\n")
    _write(source / "topics" / "t" / "topic.yaml", "title: from the environment\n")
    _commit(source, "topic changed in the environment")
    args = ["--source", str(source), "--zkusebna", str(layout["zkusebna"]), "--workshop", str(layout["workshop"])]
    assert nte.main([*args, "--no-sync", "two", "--carry", "one"]) == 1
    assert "CONFLICT" in capsys.readouterr().out and not (layout["zkusebna"] / "two").exists()
    _run(layout, "two", "--carry", "one", "--on-conflict", "copy")
    assert "from the test" in (layout["zkusebna"] / "two/topics/t/topic.yaml").read_text(encoding="utf-8")
    _run(layout, "three", "--carry", "one", "--on-conflict", "env")
    assert "environment" in (layout["zkusebna"] / "three/topics/t/topic.yaml").read_text(encoding="utf-8")


def test_carry_warns_when_a_position_needs_restating(layout, capsys):
    source = _study(layout)
    _run(layout, "one")
    one = layout["zkusebna"] / "one"
    _write(one / "topics" / "t" / "positions" / "model-a.md", "profile_version: v1\nstatus: confirmed\n")
    _write(source / "analysts" / "model-a.md", "> Status: proposed\n> Version: v2\n")
    _commit(source, "profile v2")
    _run(layout, "two", "--carry", "one")
    assert "profile_version v1, profile now v2" in capsys.readouterr().out


def test_carry_needs_a_recorded_copy(layout):
    _study(layout)
    with pytest.raises(SystemExit):
        _run(layout, "two", "--carry", "missing")


def test_study_state_paths():
    assert nte.is_study_state("topics/t/positions/owner.md")
    assert nte.is_study_state("topics/t/sources/s/source.yaml")
    assert nte.is_study_state("analysts/claude-opus-5-5.md")
    for rel in ("topics/t/sources/s/text.md", "topics/t/sources/s/segments.jsonl", "topics/t/sources/s/ingest/x",
                "topics/t/work/ocr.txt", "topics/README.md", "analysts/_template-model.md", "AGENTS.md"):  # fmt: skip
        assert not nte.is_study_state(rel), rel
