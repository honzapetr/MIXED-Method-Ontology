"""Consistency check of the LinkML schema draft (no LinkML dependency needed)."""

from pathlib import Path

import pytest
import yaml

# the ontology lives in the research environment (ADR 0011); skipped where it is absent (CI)
ENVIRONMENT = Path(__file__).resolve().parents[2] / "MIXED-Method-Ontology"
if not (ENVIRONMENT / "ontology").is_dir():
    pytest.skip("the research environment is not next to the workshop", allow_module_level=True)
ROOT = ENVIRONMENT
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
