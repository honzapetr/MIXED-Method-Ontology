# Studies

> How a study is started and run next to the environment. Status: built (T11); the real study moves out in T12.
> Decision: ADR 0010.

## Two repositories

| | Environment | Study |
| :--- | :--- | :--- |
| Folder | `2026/MIXED-Method-Ontology/MIXED-Method-Ontology/` | `2026/MIXED-Method-Ontology/studie/<slug>/` |
| Holds | program `mmo`, methods, ontology, tests, docs | one study: `topic.yaml`, sources, memos, results |
| The agent works as | builder of the environment | analyst of the study (`AGENTS.md` of the study) |
| Agent memory | its own (keyed to the git repository) | its own |
| Changes | tasks `T<n>` of `docs/plan.md` | steps of the method; what the environment lacks goes to `feedback.md` |

The study uses the environment, it does not change it. Started in the study's folder, Claude Code reads the study's
`CLAUDE.md`, which imports the study's `AGENTS.md` and the method's `agent-rules.md` from the environment (Claude
Code asks once to allow an import from outside the folder).

## Start a study

From the environment:

```sh
uv run mmo study init ../studie/<slug> --title "<title>" --method <method id>
cd ../studie/<slug>
uv sync
uv run mmo source check .
```

`mmo study init` creates in a new or empty folder outside the environment:

| File | Content |
| :--- | :--- |
| `topic.yaml` | title, `purpose`, `questions`, `goals`, `methods`, `environment` (relative path, commit, uncommitted changes), `sources` |
| `sources/`, `memos/`, `graph/` | as in a topic (`docs/spec.md`, section Topic folder) |
| `AGENTS.md` | the analyst's role and rules, where things are |
| `CLAUDE.md` | `@AGENTS.md` and `@<environment>/methods/<id>/agent-rules.md` |
| `feedback.md` | what the study teaches about the environment, newest last |
| `pyproject.toml` | `mmo` as an editable path dependency on the environment; the study is not a package |
| `.gitignore` | page images and other source files, indexes, `.env`, `.venv`, `scratch/` |
| `.git` | the study's own repository (`--no-git` skips it); nothing is committed yet |

The environment is a path dependency, so the study always runs the environment's current code. `topic.yaml` keeps
the commit the study was started with; a step of the analysis records the commit it ran with (planned, T5).

## Commands in a study

The topic argument of every `mmo` command is a slug under `--topics`, a path to a study, or the study's own name
when run inside it: `uv run mmo source check .`, `uv run mmo ingest <slug> <source>`.

## Sandbox

`studie/piskoviste/` is a throwaway study for trying the environment on real use. Delete it and start it again
with `mmo study init` whenever needed; nothing in it is analysis.

## Tests

Tests never use a real study. `tests/fixtures/mini-studie/` is a simulated study with invented material (two
sources, one memo); tests copy it to a temporary folder (`tests/core/test_study.py`).
