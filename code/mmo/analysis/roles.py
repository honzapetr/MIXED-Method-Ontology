"""Roles of subagents and their runs (T43, ADR 0014).

A lead analyst hands bounded work to subagents with a clean context: a chapter reader, an instance finder, a context
searcher, a source preparer, a blind probe, a critic. A role is a file of the research environment,
`.agents/roles/<role>.md`, whose front matter says what `mmo` needs:

```yaml
---
name: chapter-reader
description: ...
version: "2026-11-24"        # raised whenever the role's text changes; the prompt version is role/<name>@<version>
writes: memo                 # what the role may write as a proposal: code, coding, relation, memo, or none
---
```

The body is the role's prompt. A model takes a role only in a study whose confirmed position of that model lists
the role (`roles:` in `positions/<model-id>.md`). Every piece of work is a **run**: the lead starts it with
`mmo run start` (who, which role, which input), and the subagent writes with `--run <id>`; its records then carry
the role and the run, and the run's prompt version. The run is an event of `analysis/history.jsonl`; what it wrote is
found by its id. `mmo` checks only what a role may write - never how it reads or interprets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from mmo.core.topic import Topic

KINDS = {"code", "coding", "relation", "memo"}
ROLE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")


class RoleError(ValueError):
    """A role or a run is not what `mmo` can work with."""


@dataclass
class Role:
    id: str
    version: str
    writes: frozenset[str]
    description: str
    path: Path

    @property
    def prompt_version(self) -> str:
        return f"role/{self.id}@{self.version}"


def environment(topic: Topic) -> Path:
    return topic.root.parent.parent  # <environment>/topics/<slug>


def front_matter(text: str) -> dict[str, Any]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    try:
        data = yaml.safe_load(text[3:end])
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_role(path: Path) -> tuple[Role | None, list[str]]:
    """A role file and the problems found in it."""
    meta = front_matter(path.read_text(encoding="utf-8"))
    problems: list[str] = []
    name = str(meta.get("name") or "")
    if name != path.stem:
        problems.append(f"name {name!r} is not the file name {path.stem!r}")
    if not ROLE_NAME.match(path.stem):
        problems.append("a role name is lower-case words joined by '-'")
    version = str(meta.get("version") or "")
    if not version:
        problems.append("no version")
    if not meta.get("description"):
        problems.append("no description")
    raw = meta.get("writes")
    words = [w.strip() for w in (raw if isinstance(raw, list) else str(raw or "").split(","))]
    words = [w for w in words if w]
    if not words:
        problems.append("no 'writes' (code, coding, relation, memo, or none)")
    writes = frozenset() if words == ["none"] else frozenset(words)
    if unknown := writes - KINDS:
        problems.append(f"writes unknown kinds: {', '.join(sorted(unknown))}")
    if problems:
        return None, problems
    return Role(path.stem, version, writes, str(meta["description"]), path), []


def roles_dir(env: Path) -> Path:
    return env / ".agents" / "roles"


def load_roles(env: Path) -> dict[str, Role]:
    found: dict[str, Role] = {}
    folder = roles_dir(env)
    for path in sorted(folder.glob("*.md")) if folder.is_dir() else []:
        role, problems = parse_role(path)
        if role is None:
            raise RoleError(f"role {path.name}: {'; '.join(problems)}")
        found[role.id] = role
    return found


def check_roles(env: Path) -> dict[str, list[str]]:
    """Problems per role file (empty lists: the file is fine)."""
    folder = roles_dir(env)
    return {path.stem: parse_role(path)[1] for path in sorted(folder.glob("*.md"))} if folder.is_dir() else {}


def role(env: Path, role_id: str) -> Role:
    roles = load_roles(env)
    if role_id not in roles:
        known = ", ".join(sorted(roles)) or "none"
        raise RoleError(f"no role {role_id!r} in .agents/roles/ (known: {known})")
    return roles[role_id]


def position_roles(topic: Topic, model_id: str) -> list[str]:
    """The roles a model takes in a study, from `roles:` of its position there."""
    path = topic.root / "positions" / f"{model_id}.md"
    if not path.is_file():
        return []
    roles = front_matter(path.read_text(encoding="utf-8")).get("roles") or []
    if isinstance(roles, dict):
        return [str(r) for r in roles]
    return [str(r) for r in roles] if isinstance(roles, list) else [str(roles)]


def runs(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [event for event in history if event.get("op") == "run"]


def closed_runs(history: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Run id -> the event that closed it (`op: run-closed`, T48)."""
    return {str(e["run"]): e for e in history if e.get("op") == "run-closed" and e.get("run")}


def next_run_id(history: list[dict[str, Any]]) -> str:
    numbers = [int(e["run"].split("-")[1]) for e in runs(history) if str(e.get("run", "")).startswith("run-")]
    return f"run-{max(numbers, default=0) + 1:04d}"


def find_run(history: list[dict[str, Any]], run_id: str) -> dict[str, Any]:
    for event in runs(history):
        if event.get("run") == run_id:
            return event
    raise RoleError(f"no run {run_id!r} in this study (mmo run list)")
