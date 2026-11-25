"""The method as orientation, strictness per study (T33, ADR 0013 and its amendment).

A method is a description (`methods/<id>/method.yaml` of the research environment): a vocabulary of code and
relation types, a map of phases with what the model does (`model_role`) and what the researcher decides
(`researcher_decides`), practices, and optionally a prompt per phase. `mmo` reads it to guide - `mmo status`,
reminders - never to limit the researcher. What a study wants stricter it says itself, in `topic.yaml`:

```yaml
analysis:
  codebook: emergent          # emergent | evolving | fixed (no new codes while fixed)
  own_types: allowed          # allowed | ask_memo (a type outside the methods' vocabulary asks for a memo)
  phases: orientation         # orientation | sequence (only the next phase or back)
  model:
    phases: all               # all, or the phase ids in which a model may write proposals
    alternatives: false       # a model offers alternative readings (used by T29)
  team: none                  # none | consensus | agreement
  quotation_required:
    memos: []                 # memo types that need a quotation, e.g. [analytic, theoretical]
  web_search: []              # the models the researcher lets search the web for this study (T44, ADR 0015)
  critic:                     # the critic of another maker, through agy (T46, ADR 0014)
    analyst: gemini-4-neon    # the id of its profile in analysts/
    model: gemini-4-neon-medium   # the agy model
    timeout_minutes: 60
```

The core is not a setting: codes and everything a model proposes always carry quotations (ADR 0013).
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from mmo.core.topic import Topic

STATUSES = {"draft", "testing", "stable"}
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
    "passage-choice",
}
PHASE_KEYS = ("goal", "input", "output", "memos", "model_role", "researcher_decides")
PROPOSAL_KINDS = {"code", "coding", "relation", "memo"}  # what a model may write as a proposal (T29)
FRONT_VERSION = re.compile(r"(?m)^version:\s*\S+")

DEFAULTS: dict[str, Any] = {
    "codebook": "emergent",
    "own_types": "allowed",
    "phases": "orientation",
    "model": {"phases": "all", "alternatives": False},
    "team": "none",
    "quotation_required": {"memos": []},
    "web_search": [],
    "critic": {"analyst": "gemini-4-neon", "model": "gemini-4-neon-medium", "timeout_minutes": 60},
    # keys for choosing passages for fine analysis (T36; the owner's default of 2026-11-19)
    "passage_keys": {"first": ["structural", "questions"], "later": ["reception", "contrast"]},
}
CHOICES = {
    "codebook": {"emergent", "evolving", "fixed"},
    "own_types": {"allowed", "ask_memo"},
    "phases": {"orientation", "sequence"},
    "team": {"none", "consensus", "agreement"},
}


class SettingsError(ValueError):
    """`analysis:` of `topic.yaml` names something `mmo` does not know."""


# ---------------------------------------------------------------- methods


@dataclass
class Method:
    id: str
    folder: Path
    data: dict[str, Any]

    @property
    def name(self) -> str:
        return str(self.data.get("name", self.id))

    @property
    def version(self) -> str:
        return str(self.data.get("version", "unversioned"))

    @property
    def phases(self) -> list[dict[str, Any]]:
        return list(self.data.get("phases") or [])

    @property
    def phase_ids(self) -> list[str]:
        return [str(p["id"]) for p in self.phases]

    def phase(self, phase_id: str) -> dict[str, Any] | None:
        return next((p for p in self.phases if p["id"] == phase_id), None)

    @property
    def code_types(self) -> set[str]:
        return {str(t) for t in self.data.get("code_types") or []}

    @property
    def relation_types(self) -> set[str]:
        return {str(r["id"]) for r in self.data.get("relation_types") or []}

    @property
    def practices(self) -> list[str]:
        return [str(p) for p in self.data.get("practices") or []]

    @property
    def context_search(self) -> dict[str, Any]:
        """What relevant context is for the method and when its search is repeated (T44, ADR 0015)."""
        return dict(self.data.get("context_search") or {})


def environment_of(topic: Topic) -> Path:
    return topic.root.parent.parent  # <environment>/topics/<slug>


def load_method(methods_dir: Path, method_id: str) -> Method:
    path = methods_dir / method_id / "method.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"no method {method_id!r}: {path}")
    return Method(method_id, path.parent, yaml.safe_load(path.read_text(encoding="utf-8")) or {})


def study_methods(topic: Topic) -> list[Method]:
    methods_dir = environment_of(topic) / "methods"
    return [load_method(methods_dir, str(m)) for m in topic.data.get("methods") or []]


def check_method(folder: Path) -> list[str]:
    """What is wrong with a method folder's `method.yaml`; the template only needs the shape."""
    path = folder / "method.yaml"
    if not path.is_file():
        return ["no method.yaml"]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as err:
        return [f"method.yaml cannot be read: {err}"]
    template = folder.name.startswith("_")
    problems: list[str] = []
    if not template and data.get("id") != folder.name:
        problems.append(f"id {data.get('id')!r} is not the folder name {folder.name!r}")
    if data.get("status") not in STATUSES:
        problems.append(f"status must be one of {sorted(STATUSES)}")
    for key in ("name", "summary", "phases", "relation_types", "conclusions"):
        if not data.get(key):
            problems.append(f"missing {key}")
    if "version" in data and not str(data["version"]).strip():
        problems.append("version is empty")
    for key in ("purpose", "questions", "prior_theory", "reasoning", "theory_output"):
        if not (data.get("research_design") or {}).get(key):
            problems.append(f"missing research_design.{key}")
    if not isinstance(data.get("code_types", []), list):
        problems.append("code_types must be a list (a vocabulary that orients, not a list of what is allowed)")
    relation_ids = {str(r.get("id")) for r in data.get("relation_types") or [] if isinstance(r, dict)}
    seen: set[str] = set()
    for phase in data.get("phases") or []:
        pid = str(phase.get("id"))
        if pid in seen:
            problems.append(f"phase {pid} appears twice")
        seen.add(pid)
        for key in PHASE_KEYS:
            if not phase.get(key):
                problems.append(f"phase {pid}: missing {key}")
        if "human_gate" in phase:
            problems.append(f"phase {pid}: human_gate is now researcher_decides (a decision, never a lock)")
        if not template:
            unknown = set(phase.get("allowed_relations") or []) - relation_ids
            if unknown:
                problems.append(f"phase {pid}: allowed_relations not among relation_types: {sorted(unknown)}")
            bad_memos = set(phase.get("memos") or []) - MEMO_TYPES
            if bad_memos:
                problems.append(f"phase {pid}: unknown memo types {sorted(bad_memos)}")
        proposes = phase.get("model_proposes")
        if proposes is not None and (not isinstance(proposes, list) or set(proposes) - PROPOSAL_KINDS):
            problems.append(f"phase {pid}: model_proposes is a list of {sorted(PROPOSAL_KINDS)}")
        if prompt := phase.get("prompt"):
            prompt_file = folder / str(prompt)
            if not prompt_file.is_file():
                problems.append(f"phase {pid}: prompt {prompt} does not exist")
            elif not FRONT_VERSION.search(prompt_file.read_text(encoding="utf-8")):
                problems.append(f"phase {pid}: prompt {prompt} has no 'version:' line")
    problems += check_context_search(data.get("context_search"))
    roles = data.get("roles")
    if roles is not None and not isinstance(roles, dict):
        problems.append("roles maps a role to the method's own prompt for it (role: prompts/roles/<role>.md)")
    for role_id, prompt in (roles or {}).items():
        prompt_file = folder / str(prompt)
        if not prompt_file.is_file():
            problems.append(f"role {role_id}: prompt {prompt} does not exist")
        elif not FRONT_VERSION.search(prompt_file.read_text(encoding="utf-8")):
            problems.append(f"role {role_id}: prompt {prompt} has no 'version:' line")
    return problems


CONTEXT_SEARCH_KEYS = ("derived_from", "source_types", "character", "where", "repeat")


def check_context_search(block: Any) -> list[str]:
    """`context_search:` of `method.yaml` (T44, ADR 0015): its shape only, never what a method asks.

    derived_from (what the search is derived from), source_types (a list: the types of sources and why they matter),
    character (how the character and independence of a source are judged), where (a list of places, not only the
    web), repeat (when the search returns).
    """
    if block is None:
        return []
    if not isinstance(block, dict):
        return ["context_search: a mapping of " + ", ".join(CONTEXT_SEARCH_KEYS)]
    problems = [f"context_search: missing {key}" for key in CONTEXT_SEARCH_KEYS if not block.get(key)]
    problems += [f"context_search: {key} is not a field" for key in block if key not in CONTEXT_SEARCH_KEYS]
    for key in ("source_types", "where"):
        if block.get(key) and not isinstance(block[key], list):
            problems.append(f"context_search: {key} must be a list")
    return problems


def prompt_version(method: Method, phase_id: str) -> str | None:
    """`<method>/<phase>@<version>` of a phase's prompt (T39), or None when the phase has none."""
    phase = method.phase(phase_id) or {}
    if not phase.get("prompt"):
        return None
    path = method.folder / str(phase["prompt"])
    match = FRONT_VERSION.search(path.read_text(encoding="utf-8")) if path.is_file() else None
    if not match:
        return None
    return f"{method.id}/{phase_id}@{match.group(0).split(':', 1)[1].strip().strip(chr(34))}"


# ---------------------------------------------------------------- settings of a study


def _merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for key, value in over.items():
        if key not in base:
            raise SettingsError(f"analysis.{key} is not a setting (known: {', '.join(sorted(base))})")
        out[key] = _merge(base[key], value) if isinstance(base[key], dict) and isinstance(value, dict) else value
    return out


@dataclass
class Settings:
    data: dict[str, Any] = field(default_factory=lambda: copy.deepcopy(DEFAULTS))

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def changed(self) -> dict[str, Any]:
        """The settings that differ from the free defaults."""
        return {k: v for k, v in self.data.items() if v != DEFAULTS[k]}


def study_settings(topic: Topic) -> Settings:
    settings = Settings(_merge(DEFAULTS, topic.data.get("analysis") or {}))
    for key, allowed in CHOICES.items():
        if settings[key] not in allowed:
            raise SettingsError(f"analysis.{key}: {settings[key]!r} is not one of {sorted(allowed)}")
    model_phases = settings["model"]["phases"]
    if model_phases != "all" and not isinstance(model_phases, list):
        raise SettingsError("analysis.model.phases: 'all' or a list of phase ids")
    if not isinstance(settings["quotation_required"]["memos"], list):
        raise SettingsError("analysis.quotation_required.memos: a list of memo types")
    if not isinstance(settings["web_search"], list):
        raise SettingsError("analysis.web_search: a list of the model ids the researcher lets search the web")
    for round_name, keys in settings["passage_keys"].items():
        if round_name not in ("first", "later") or not isinstance(keys, list):
            raise SettingsError("analysis.passage_keys: first and later, each a list of keys (e.g. structural)")
    return settings


# ---------------------------------------------------------------- where the study is


def current_phases(history: list[dict[str, Any]]) -> dict[str, str]:
    """The phase of each method, from the last `phase` operation for it."""
    phases: dict[str, str] = {}
    for event in history:
        if event.get("op") == "phase":
            phases[str(event["method"])] = str(event["phase"])
    return phases


def check_move(method: Method, settings: Settings, current: str | None, target: str) -> str | None:
    """None when the move is fine, else why not (only when the study asked for a sequence)."""
    if target not in method.phase_ids:
        return f"{method.id} has no phase {target!r} (phases: {', '.join(method.phase_ids)})"
    if settings["phases"] != "sequence" or current is None:
        return None
    order = method.phase_ids
    if order.index(target) > order.index(current) + 1:
        return (
            f"the study follows the phases in sequence (analysis.phases: sequence): from {current} the next phase is "
            f"{order[order.index(current) + 1]}; going back is always possible"
        )
    return None


def model_may_write(topic: Topic, history: list[dict[str, Any]]) -> str | None:
    """None when a model may write proposals now, else why not (the study limits models to some phases)."""
    allowed = study_settings(topic)["model"]["phases"]
    if allowed == "all":
        return None
    now = set(current_phases(history).values())
    if now & set(allowed):
        return None
    where = ", ".join(sorted(now)) or "no phase set (mmo phase)"
    return f"the study lets models propose only in the phases {', '.join(allowed)}; the study is at: {where}"


def model_may_propose(topic: Topic, history: list[dict[str, Any]], kind: str) -> str | None:
    """None when a model may propose a `kind` now, else why not.

    `model_proposes` of the current phase (a binding part of `model_role`, for models only) names what a model may
    write there; a phase without it, or a study whose phase is not set, does not limit the kind. With several
    methods, one current phase that allows the kind is enough.
    """
    now = current_phases(history)
    limits: list[str] = []
    for method in study_methods(topic):
        phase = method.phase(now.get(method.id, "")) if method.id in now else None
        if phase is None or phase.get("model_proposes") is None:
            return None
        allowed = [str(k) for k in phase["model_proposes"]]
        if kind in allowed:
            return None
        limits.append(f"{method.id}/{phase['id']}: {', '.join(allowed) or 'nothing'}")
    if not limits:
        return None
    return (
        f"in the study's current phase a model does not propose a {kind} ({'; '.join(limits)}); "
        "say it in a memo, or the researcher moves the study to another phase"
    )


def vocabulary(topic: Topic) -> tuple[set[str], set[str]]:
    """Code types and relation types of all the study's methods."""
    codes: set[str] = set()
    relations: set[str] = set()
    for method in study_methods(topic):
        codes |= method.code_types
        relations |= method.relation_types
    return codes, relations
