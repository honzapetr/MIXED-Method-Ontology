"""Consistency checks of the drafts: the LinkML schema and the method modules (no LinkML dependency needed)."""

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
BUILTIN_TYPES = {"string", "integer", "float", "boolean", "datetime", "date", "uriorcurie", "uri"}


def load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_schema_references_are_defined() -> None:
    schema = load(ROOT / "ontology" / "schema" / "mmo.yaml")
    classes, slots, enums = schema["classes"], schema["slots"], schema["enums"]
    known_ranges = BUILTIN_TYPES | set(classes) | set(enums)
    for name, cls in classes.items():
        if cls and cls.get("is_a"):
            assert cls["is_a"] in classes, f"{name}: unknown parent {cls['is_a']}"
        for slot in (cls or {}).get("slots", []):
            assert slot in slots, f"{name}: slot {slot} is not defined"
    for name, slot in slots.items():
        rng = (slot or {}).get("range", schema.get("default_range", "string"))
        assert rng in known_ranges, f"slot {name}: unknown range {rng}"


METHODS = sorted((ROOT / "methods").glob("*.yaml"))


@pytest.mark.parametrize("path", METHODS, ids=[p.stem for p in METHODS])
def test_method_module(path: Path) -> None:
    method = load(path)
    assert method["id"] == path.stem
    for key in ("name", "summary", "phases", "relation_types", "conclusions"):
        assert method.get(key), f"{path.name}: missing {key}"
    relation_ids = {r["id"] for r in method["relation_types"]}
    phase_ids = [p["id"] for p in method["phases"]]
    assert len(phase_ids) == len(set(phase_ids))
    for phase in method["phases"]:
        for key in ("goal", "input", "output", "model_role", "human_gate"):
            assert phase.get(key), f"{path.name}/{phase['id']}: missing {key}"
        assert set(phase.get("allowed_relations", [])) <= relation_ids
