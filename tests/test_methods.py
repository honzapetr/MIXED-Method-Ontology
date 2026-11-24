"""Consistency checks of the method folders of the research environment (`../MIXED-Method-Ontology/methods/`).

The methods live in the research environment (ADR 0011); the workshop checks them when the two repositories sit
side by side, as on the owner's machine. Where the research environment is absent (CI) the checks are skipped.
"""

from pathlib import Path

import pytest
import yaml

ENVIRONMENT = Path(__file__).resolve().parents[2] / "MIXED-Method-Ontology"
METHODS_DIR = ENVIRONMENT / "methods"
if not METHODS_DIR.is_dir():
    pytest.skip("the research environment is not next to the workshop", allow_module_level=True)
DOCUMENTS = ("research-design.md", "procedure.md", "agent-rules.md", "applications.md", "sources.md", "reflexivity.md")
STATUSES = {"draft", "testing", "stable"}
# memo types of docs/memos.md of the research environment
MEMO_TYPES = {
    "context",
    "first-impression",
    "familiarisation",
    "reflexive",
    "analytic",
    "theoretical",
    "methodological",
    "steering",
    "search-plan",
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
        for key in ("goal", "input", "output", "memos", "model_role", "researcher_decides"):
            assert phase.get(key), f"{folder.name}/{phase['id']}: missing {key}"
        assert set(phase.get("allowed_relations", [])) <= relation_ids
        assert set(phase["memos"]) <= MEMO_TYPES, f"{folder.name}/{phase['id']}: unknown memo type"


@pytest.mark.parametrize("folder", [*METHODS, METHODS_DIR / "_template"], ids=[*(p.name for p in METHODS), "_template"])
def test_method_schema_of_mmo(folder: Path) -> None:
    """The schema `mmo method check` uses (T33): a version, researcher_decides, versioned prompts if any."""
    from mmo.analysis.method import check_method

    assert check_method(folder) == []
    assert "version" in load(folder / "method.yaml"), f"{folder.name}: no version"
    assert load(folder / "method.yaml").get("context_search"), f"{folder.name}: no context_search (T44, ADR 0015)"
