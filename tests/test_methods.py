"""Consistency checks of the method folders in methods/<id>/ (layout: methods/README.md)."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
METHODS_DIR = ROOT / "methods"
DOCUMENTS = ("research-design.md", "procedure.md", "agent-rules.md", "applications.md", "sources.md", "reflexivity.md")
STATUSES = {"draft", "testing", "stable"}
# memo types of docs/environment/memos.md
MEMO_TYPES = {
    "context",
    "first-impression",
    "familiarisation",
    "reflexive",
    "analytic",
    "theoretical",
    "methodological",
    "steering",
}
METHODS = sorted(p for p in METHODS_DIR.iterdir() if p.is_dir() and not p.name.startswith(("_", ".")))


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_methods_are_folders() -> None:
    assert METHODS, "no method folders"
    assert not list(METHODS_DIR.glob("*.yaml")), "a method is a folder methods/<id>/, not a loose YAML file"
    assert {"skad", "grounded-theory", "thematic-analysis"} <= {p.name for p in METHODS}


def test_template_has_every_file() -> None:
    template = METHODS_DIR / "_template"
    for name in ("method.yaml", *DOCUMENTS):
        assert (template / name).is_file(), f"_template: missing {name}"


@pytest.mark.parametrize("folder", METHODS, ids=[p.name for p in METHODS])
def test_method_documents(folder: Path) -> None:
    for name in DOCUMENTS:
        path = folder / name
        assert path.is_file(), f"{folder.name}: missing {name}"
        assert path.read_text(encoding="utf-8").strip(), f"{folder.name}/{name} is empty"


@pytest.mark.parametrize("folder", METHODS, ids=[p.name for p in METHODS])
def test_method_module(folder: Path) -> None:
    path = folder / "method.yaml"
    method = load(path)
    assert method["id"] == folder.name
    assert method.get("status") in STATUSES, f"{folder.name}: status must be one of {sorted(STATUSES)}"
    for key in ("name", "summary", "phases", "relation_types", "conclusions"):
        assert method.get(key), f"{folder.name}: missing {key}"
    for key in ("purpose", "questions", "prior_theory", "reasoning", "theory_output"):
        assert method.get("research_design", {}).get(key), f"{folder.name}: missing research_design.{key}"
    relation_ids = {r["id"] for r in method["relation_types"]}
    phase_ids = [p["id"] for p in method["phases"]]
    assert len(phase_ids) == len(set(phase_ids))
    for phase in method["phases"]:
        for key in ("goal", "input", "output", "memos", "model_role", "human_gate"):
            assert phase.get(key), f"{folder.name}/{phase['id']}: missing {key}"
        assert set(phase.get("allowed_relations", [])) <= relation_ids
        assert set(phase["memos"]) <= MEMO_TYPES, f"{folder.name}/{phase['id']}: unknown memo type"
