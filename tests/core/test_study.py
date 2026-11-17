import shutil
import subprocess
import tomllib
from pathlib import Path

import pytest
import yaml

from mmo.cli import main
from mmo.core.study import ENVIRONMENT_ROOT, init_study, relative_path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini-studie"


@pytest.fixture
def study(tmp_path: Path) -> Path:
    """A copy of the simulated study, so tests never change the fixture."""
    target = tmp_path / "mini-studie"
    shutil.copytree(FIXTURE, target)
    return target


def make_environment(root: Path) -> Path:
    """A minimal environment with one method folder."""
    (root / "methods" / "skad").mkdir(parents=True)
    (root / "methods" / "skad" / "method.yaml").write_text("id: skad\n", encoding="utf-8")
    return root


def test_environment_root_is_this_repository() -> None:
    assert (ENVIRONMENT_ROOT / "methods" / "skad" / "method.yaml").is_file()
    assert (ENVIRONMENT_ROOT / "code" / "mmo" / "core" / "study.py").is_file()


def test_init_study_creates_a_project_of_its_own(tmp_path: Path) -> None:
    env = make_environment(tmp_path / "env")
    topic = init_study(tmp_path / "studie" / "my-study", "My study", "skad", environment=env, git=False)
    root = topic.root
    for name in ("AGENTS.md", "CLAUDE.md", "feedback.md", "pyproject.toml", ".gitignore", "topic.yaml"):
        assert (root / name).is_file(), name
    for sub in ("sources", "memos", "graph"):
        assert (root / sub).is_dir()

    data = yaml.safe_load((root / "topic.yaml").read_text(encoding="utf-8"))
    assert data["title"] == "My study" and data["methods"] == ["skad"]
    assert data["environment"]["path"] == "../../env"
    assert {"purpose", "questions", "goals", "sources"} <= data.keys()

    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    source = pyproject["tool"]["uv"]["sources"]["mixed-method-ontology"]
    assert source == {"path": "../../env", "editable": True}
    assert pyproject["tool"]["uv"]["package"] is False

    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    assert "analyst" in agents and "../../env/methods/skad/" in agents
    assert "@../../env/methods/skad/agent-rules.md" in (root / "CLAUDE.md").read_text(encoding="utf-8")
    assert "sources/**/*.jpg" in (root / ".gitignore").read_text(encoding="utf-8")


@pytest.mark.skipif(not shutil.which("git"), reason="git not installed")
def test_init_study_records_the_environment_commit(tmp_path: Path) -> None:
    env = make_environment(tmp_path / "env")
    git = ["git", "-C", str(env), "-c", "user.name=t", "-c", "user.email=t@example.org"]
    subprocess.run(["git", "init", "--quiet", str(env)], check=True)
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "--quiet", "-m", "init"], check=True)
    head = subprocess.run([*git, "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()

    topic = init_study(tmp_path / "s1", "S", "skad", environment=env)
    data = yaml.safe_load((topic.root / "topic.yaml").read_text(encoding="utf-8"))
    assert data["environment"]["commit"] == head and data["environment"]["dirty"] is False
    assert (topic.root / ".git").exists(), "the study is a git repository of its own"


def test_init_study_refuses(tmp_path: Path) -> None:
    env = make_environment(tmp_path / "env")
    with pytest.raises(FileNotFoundError, match="no such method"):
        init_study(tmp_path / "s1", "S", "missing", environment=env, git=False)
    with pytest.raises(ValueError, match="outside the environment"):
        init_study(env / "studie" / "s1", "S", "skad", environment=env, git=False)
    busy = tmp_path / "busy"
    busy.mkdir()
    (busy / "x.txt").write_text("x", encoding="utf-8")
    with pytest.raises(FileExistsError):
        init_study(busy, "S", "skad", environment=env, git=False)
    empty = tmp_path / "empty"
    empty.mkdir()
    assert init_study(empty, "S", "skad", environment=env, git=False).root == empty.resolve()


def test_relative_path_uses_forward_slashes(tmp_path: Path) -> None:
    assert relative_path(tmp_path / "a" / "env", tmp_path / "b" / "study") == "../../a/env"


def test_cli_study_init(tmp_path: Path, capsys) -> None:
    target = tmp_path / "studie" / "s1"
    assert main(["study", "init", str(target), "--title", "S", "--method", "skad", "--no-git"]) == 0
    assert "created study" in capsys.readouterr().out
    data = yaml.safe_load((target / "topic.yaml").read_text(encoding="utf-8"))
    assert data["methods"] == ["skad"]
    assert main(["study", "init", str(target), "--title", "S", "--method", "skad", "--no-git"]) == 1


def test_commands_work_on_a_study_folder(study: Path, monkeypatch, capsys) -> None:
    """Inside a study the topic argument is `.`; the simulated study goes through ingest and check."""
    monkeypatch.chdir(study)
    assert main(["source", "check", "."]) == 0
    out = capsys.readouterr().out
    assert "projev (primary): 1 to fill in or review" in out and "mmo ingest mini-studie projev" in out

    assert main(["ingest", ".", "projev"]) == 0
    assert main(["ingest", "mini-studie", "ohlas"]) == 0, "inside a study its name works as well as `.`"
    text = (study / "sources" / "projev" / "ingest" / "text" / "original.md").read_text(encoding="utf-8")
    assert "the river divided us" in text
    capsys.readouterr()
    assert main(["source", "check", ".", "ohlas"]) == 0
    assert "final text: choose the variant" in capsys.readouterr().out


def test_study_folder_by_path_from_outside(study: Path, capsys) -> None:
    assert main(["source", "check", str(study), "projev"]) == 0
    assert "projev (primary)" in capsys.readouterr().out
