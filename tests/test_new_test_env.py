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
    subprocess.run(["git", "init", "-q", str(source)], check=True)
    subprocess.run(["git", "-C", str(source), "add", ".gitignore", "AGENTS.md", "analysts", "topics"], check=True)
    subprocess.run(
        ["git", "-C", str(source), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init"],
        check=True,
    )
    return {"workshop": workshop, "source": source, "zkusebna": zkusebna}


def _run(layout: dict[str, Path], *extra: str) -> None:
    args = ["--source", str(layout["source"]), "--zkusebna", str(layout["zkusebna"])]
    assert nte.main([*args, "--workshop", str(layout["workshop"]), *extra]) == 0


def test_copies_what_git_sees_without_secrets_or_environments(layout):
    _run(layout)
    dest = layout["zkusebna"] / "test1"
    assert (dest / "AGENTS.md").exists()
    assert (dest / "untracked.md").exists()
    assert (dest / "topics/t/sources/s/text.md").exists()
    for left_out in (".env", ".venv", "scratch", ".git", "topics/t/sources/s/files/p001.jpg"):
        assert not (dest / left_out).exists(), left_out
    assert (layout["zkusebna"] / "_log.tsv").read_text(encoding="utf-8").count("\ttest1\t") == 1


def test_rewrites_the_workshop_path(layout):
    _run(layout, "probe")
    dest = layout["zkusebna"] / "probe"
    assert '"../../ws"' in (dest / "pyproject.toml").read_text(encoding="utf-8")
    assert '"../../ws"' in (dest / "uv.lock").read_text(encoding="utf-8")


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
