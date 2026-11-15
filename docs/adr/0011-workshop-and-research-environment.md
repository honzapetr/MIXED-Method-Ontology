# 11. The workshop and the research environment

- Status: accepted (2026-11-15, owner); supersedes ADR 0010

## Context

One repository holds both the building of the environment (program, plan, decisions, builder roles) and the
research done with it (methods, ontology, analysts, the study `nazi-v-ai-dobe`). An agent started here reads one
`AGENTS.md` that makes it a builder and an analyst at once, and trying an analysis step changes the repository being
developed. ADR 0010 tried to fix this by putting each study in a repository of its own; that read the owner's
request wrongly (`docs/answers.md`, 2026-11-15). The owner wants two repositories: one where the environment is
developed like an ordinary application, and the research environment itself, an ecosystem with many studies.

Claude Code loads `CLAUDE.md` from the folder it is started in and from every parent folder, and other agents read
`AGENTS.md` the same way; so instructions of one role leak into any folder below it.

## Decision

Three sibling folders on Google Drive under `2026/MIXED-Method-Ontology/`, which itself holds no `AGENTS.md` or
`CLAUDE.md`:

```
2026/MIXED-Method-Ontology/
├── MIXED-Method-Ontology/   workshop – git (this repository, name kept)
├── vyzkum/                  research environment – git
└── zkusebna/                test research environments – no git
```

**Workshop** (builder; developed like an application): the program and everything about building it.

| What | Where in the workshop |
| :--- | :--- |
| Program `mmo` and its tests, simulated test study | `code/mmo/`, `tests/` (`tests/fixtures/mini-studie/`) |
| Python project, lock, vendored wheels | `pyproject.toml`, `uv.lock`, `vendor/wheels/` |
| Brief, specification, plan, progress, answers, decisions, development rules, owner's notes | `docs/` (`brief.md`, `spec.md`, `plan.md`, `progress.md`, `answers.md`, `adr/`, `development.md`, `owner-notes.md`) |
| Builder roles and skills | `.agents/roles/` (planner, coder, reviewer, advisor), `.agents/skills/` (write-plan, implement-task, review-task), `.claude/` (generated), `.agents/lab.yaml` |
| Tooling, CI, preview | `tools/` (incl. the tool that creates test environments), `.github/`, `Dockerfile`, `compose.preview.yaml` |
| Instructions for the builder | `AGENTS.md`, `CLAUDE.md` |
| One-off scripts | `scratch/T<n>/` (git-ignored) |

**Research environment** (analyst): everything the analyst needs to do analyses, and the studies.

| What | Where in `vyzkum/` |
| :--- | :--- |
| Methods: research design, procedure, rules for agents, applications, sources, reflexivity; template; shared methodology | `methods/` (as today) |
| Ontology | `ontology/` |
| Analysts: profiles and journals of researchers and models, triggers for reflexive notes, templates | `analysts/` (today `docs/environment/analysts/`) |
| Manual for the analyst: memos, source preparation, how to use `mmo` | `docs/` (today `docs/environment/`) |
| Studies | `topics/<slug>/` (first `nazi-v-ai-dobe`; `sample-masaryk-suicide` deleted) |
| Analyst skills | `.agents/skills/` (ingest-sources, transcribe-pages), `.claude/` (generated) |
| The released program | `pyproject.toml`, `uv.lock`, `vendor/wheels/` (`mmo` and `fabric-ocr` wheels pinned by path) |
| Instructions for the analyst, self-contained (no reference to the workshop) | `AGENTS.md`, `CLAUDE.md` |
| Settings and one-off scripts | `.env.example`, `scratch/` (git-ignored) |

**Test research environments** (`zkusebna/<name>/`): throwaway copies of the research environment made by a tool of
the workshop – without `topics/`, `.git` and `.venv`, optionally with the simulated study or a copy of one study,
with `mmo` as an editable path dependency on the workshop. No git. The tool refuses a target that has
`AGENTS.md`, `CLAUDE.md` or `.git` in any parent folder. Automated tests make them in a temporary folder.

**Versions:** only the workshop and the research environment are git repositories. The research environment uses a
released `mmo` (a wheel built in the workshop), never the workshop's working tree. The research environment starts
with a fresh history; its first commit names the workshop commit it was taken from.

Roles: the analyst works only on research in `vyzkum/`. What changes in the analyst's role, the methods or the
procedures is agreed by the owner with the builder in the workshop.

## Consequences

- Kept from T11: `tests/fixtures/mini-studie/`, the `fabric-ocr` wheel pinned by path, the `mmo` topic argument
  taking a path. Removed: `mmo study init`, `docs/environment/studies.md`, the sandbox `studie/piskoviste/`.
- `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/development.md`, `docs/spec.md` and the skills of the workshop change
  (protected paths, approved by the owner).
- Claude Code's memory is keyed by the repository, so the builder and the analyst keep separate memories; a test
  environment without git gets a fresh one.
- Tasks T12-T16 in `docs/plan.md`.
