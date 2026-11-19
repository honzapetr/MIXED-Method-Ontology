"""The topic argument of `mmo` takes a study folder by path, `.` or its name (ADR 0010, T15)."""

import shutil
from pathlib import Path

import pytest

from mmo.cli import main

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "mini-studie"


@pytest.fixture
def study(tmp_path: Path) -> Path:
    """A copy of the simulated study, so tests never change the fixture."""
    target = tmp_path / "mini-studie"
    shutil.copytree(FIXTURE, target)
    return target


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
