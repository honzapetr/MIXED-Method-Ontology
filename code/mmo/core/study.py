"""A study as a repository of its own, next to the environment (ADR 0010).

The root of a study is a topic (`topic.yaml`, `sources/`, `memos/`, `graph/`), plus what makes it a project of its
own: a git repository, `pyproject.toml` with `mmo` as an editable path dependency, the analyst's instructions
(`AGENTS.md`, `CLAUDE.md`), `feedback.md` for what the study teaches about the environment, and a `.gitignore`.
The study records which environment (path and commit) and which method it works with.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from mmo.core.topic import Topic, check_slug

ENVIRONMENT_ROOT = Path(__file__).resolve().parents[3]  # code/mmo/core/study.py -> repository root
PACKAGE = "mixed-method-ontology"

GITIGNORE = """\
# Page images and other large source files stay out of git (size, copyright); ingest/files.yaml keeps their hashes.
sources/**/*.jpg
sources/**/*.jpeg
sources/**/*.png
sources/**/*.tif
sources/**/*.tiff
sources/**/*.webp
sources/**/*.pdf
sources/**/*.epub
# Rebuildable indexes
graph/.store/
# Local settings and secrets
.env
.env.local
# Python
.venv/
__pycache__/
# One-off scripts and temporary files
scratch/
"""

PYPROJECT = """\
# The study uses the environment's program `mmo`; it is not a package itself.
[project]
name = "study-{slug}"
version = "0.0.0"
requires-python = ">=3.12"
dependencies = ["{package}"]

[tool.uv]
package = false

[tool.uv.sources]
{package} = {{ path = "{environment}", editable = true }}
"""

AGENTS = """\
# AGENTS.md - study "{title}"

This folder is a **study**: a concrete qualitative analysis with its sources, memos and results. You work here as
an **analyst**, not as a builder of the environment. The environment (program `mmo`, methods, ontology) lives in
its own repository and is not changed from here.

## Where things are

| What | Where |
| :--- | :--- |
| The study: title, purpose, questions, goals, method, environment | `topic.yaml` |
| Sources (`source.yaml`, `notes.md`, `files/`, `text.md`, segments) | `sources/<id>/` |
| Memos: impressions, positions, reflexive and analytic notes | `memos/` |
| What the study teaches about the environment | `feedback.md` |
| One-off scripts and temporary files | `scratch/` (git-ignored) |
| The environment | `{environment}` (commit recorded in `topic.yaml`) |
| The method of this study: procedure, rules for agents, reflexivity | `{environment}/methods/{method}/` |
| Memo format | `{environment}/docs/environment/memos.md` |
| Analyst profiles and the triggers for reflexive notes | `{environment}/docs/environment/analysts/` |

## Rules

* **Talk to the owner in Czech**; files of the study may be in Czech or English.
* **Follow the method's rules for agents** (`methods/{method}/agent-rules.md` in the environment) in every step.
* **The model proposes, the researcher decides.** Nothing is confirmed, added to the corpus or changed in the
  questions without the researcher.
* **Traceability:** every analytic statement leads to a segment (source, page, offsets, quote) and to the step that
  made it (model, prompt version, time).
* **Reflexivity:** a model used for the first time writes its profile before any analytic step; reflexive notes are
  written at once when a trigger occurs.
* **Do not change the environment from here.** When the study shows that the environment needs a change (a missing
  command, a wrong method description, an unclear rule), write it in `feedback.md`; it is taken over by a task of
  the environment.
* **Read `sources/<id>/text.md` and its segments**, never `ingest/`.
* **Secrets:** never read, print or write `.env`.
* **Commands:** `uv sync`, then `uv run mmo --help`; the topic argument of `mmo` is `.` (this folder), e.g.
  `uv run mmo source check .`.
"""

CLAUDE = """\
@AGENTS.md

## Claude Code

The method's rules for agents, loaded from the environment:

@{environment}/methods/{method}/agent-rules.md
"""

FEEDBACK = """\
# Feedback to the environment

> What this study teaches about the environment (program, methods, instructions). Newest last. The builder takes
> each item over in a task of the environment and notes the task here.
"""


def environment_commit(environment: Path) -> dict[str, Any]:
    """Commit of the environment's git repository and whether it has uncommitted changes (empty if unknown)."""
    if not shutil.which("git") or not (environment / ".git").exists():
        return {}
    run = {"cwd": environment, "capture_output": True, "text": True, "check": False}
    head = subprocess.run(["git", "rev-parse", "HEAD"], **run)
    if head.returncode != 0:
        return {}
    status = subprocess.run(["git", "status", "--porcelain"], **run)
    return {"commit": head.stdout.strip(), "dirty": bool(status.stdout.strip())}


def relative_path(target: Path, start: Path) -> str:
    """`target` relative to `start` with forward slashes; absolute when they are on different drives."""
    try:
        return Path(os.path.relpath(target, start)).as_posix()
    except ValueError:
        return target.as_posix()


def init_study(
    path: Path,
    title: str,
    method: str,
    environment: Path = ENVIRONMENT_ROOT,
    git: bool = True,
) -> Topic:
    """Create a study at `path`: the topic files, the project files and (optionally) a git repository."""
    path = path.resolve()
    environment = environment.resolve()
    check_slug(path.name, "study folder name")
    method_dir = environment / "methods" / method
    if not (method_dir / "method.yaml").is_file():
        raise FileNotFoundError(f"no such method in the environment: {method_dir}")
    if path.exists() and any(path.iterdir()):
        raise FileExistsError(f"folder is not empty: {path}")
    if path == environment or environment in path.parents:
        raise ValueError(f"a study must live outside the environment: {path}")

    if path.exists():
        path.rmdir()  # empty, checked above; Topic.create makes it again
    topic = Topic.create(path.parent, path.name, title)
    env_link = relative_path(environment, path)
    topic.data = {
        "title": title,
        "created": topic.data["created"],
        "purpose": "",
        "questions": [],
        "goals": [],
        "methods": [method],
        "environment": {"path": env_link, **environment_commit(environment)},
        "sources": [],
    }
    topic.save()
    values = {
        "title": title,
        "method": method,
        "environment": env_link,
        "slug": path.name,
        "package": PACKAGE,
    }
    files = {
        "AGENTS.md": AGENTS,
        "CLAUDE.md": CLAUDE,
        "feedback.md": FEEDBACK,
        "pyproject.toml": PYPROJECT,
        ".gitignore": GITIGNORE,
    }
    for name, template in files.items():
        (path / name).write_text(template.format(**values), encoding="utf-8", newline="\n")
    if git and shutil.which("git"):
        subprocess.run(["git", "init", "--quiet", str(path)], check=True)
    return topic
