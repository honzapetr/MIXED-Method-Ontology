# 11. The workshop and the research environment

- Status: accepted (2026-11-15, owner; the owner will correct the file layout); supersedes ADR 0010

## Context

One repository holds both the building of the environment (program, plan, decisions, builder roles) and the
research done with it (methods, ontology, analysts, the study `nazi-v-ai-dobe`). An agent started here reads one
`AGENTS.md` that makes it a builder and an analyst at once, and trying an analysis step changes the repository being
developed. ADR 0010 tried to fix this by putting each study in a repository of its own; that read the owner's
request wrongly (`docs/answers.md`, 2026-11-15). The owner wants two repositories: one where the environment is
developed like an ordinary application, and the research environment itself, an ecosystem with many studies.

Claude Code loads `CLAUDE.md` from the folder it is started in and from every parent folder, and other agents read
`AGENTS.md` the same way; so instructions of one role leak into any folder below it. Claude Code keeps its memory
per project path (`~/.claude/projects/<path>/memory/`).

## Decision

Sibling folders on Google Drive under `2026/MIXED-Method-Ontology/`, which itself holds no `AGENTS.md` or
`CLAUDE.md`:

```
2026/MIXED-Method-Ontology/
├── MIXED-Method-Ontology-vyvoj/   workshop – git (today's repository, renamed; keeps its history)
├── MIXED-Method-Ontology/         research environment – git (new, fresh history)
└── zkusebna/                      test research environments – no git (later)
```

The split comes first; test environments and releasing `mmo` follow after it.

### What stays in the workshop (`MIXED-Method-Ontology-vyvoj/`)

| Today | Note |
| :--- | :--- |
| `code/mmo/` | the program |
| `tests/` (incl. `fixtures/mini-studie/`) | `test_methods.py` and `test_ontology.py` read the research environment at `../MIXED-Method-Ontology/` |
| `pyproject.toml`, `uv.lock`, `vendor/wheels/` | |
| `docs/brief.md`, `spec.md`, `plan.md`, `progress.md`, `answers.md`, `owner-notes.md`, `development.md`, `README.md`, `adr/` | `development.md` rewritten as the rules of the workshop |
| `.agents/roles/`, `.agents/lab.yaml`, `.agents/outcome.schema.json`, `.agents/state/` | builder roles |
| `.agents/skills/` write-plan, implement-task, review-task | builder skills |
| `.claude/` (agents, builder skills, `settings.json`) | |
| `.github/`, `.devcontainer/`, `Dockerfile`, `compose.preview.yaml`, `tools/` | |
| `AGENTS.md`, `CLAUDE.md`, `README.md` | rewritten for the builder only |
| `.editorconfig`, `.gitattributes`, `.gitignore`, `.env.example`, `scratch/` | |

### What moves to the research environment (`MIXED-Method-Ontology/`)

| Today | In the research environment |
| :--- | :--- |
| `methods/` (all) | `methods/` |
| `ontology/` (`mapping.md`, `schema/mmo.yaml`) | `ontology/` |
| `docs/environment/analysts/` | `analysts/` |
| `docs/environment/memos.md`, `docs/environment/source-preparation.md` | `docs/` |
| `topics/README.md`, `topics/nazi-v-ai-dobe/` (with the git-ignored page images) | `topics/` |
| `.agents/skills/` ingest-sources, transcribe-pages | `.agents/skills/` and copies in `.claude/skills/` |

New in the research environment: `AGENTS.md` and `CLAUDE.md` for the analyst only, with no reference to the
workshop; `README.md`; `pyproject.toml` with `mmo` as an editable path dependency on `../MIXED-Method-Ontology-vyvoj`
(until `mmo` is released as a wheel); `.gitignore`, `.env.example`, `.editorconfig`, `.gitattributes` copied from
the workshop.

### Deleted

`topics/sample-masaryk-suicide/`, `docs/environment/studies.md`, `mmo study init` (`code/mmo/core/study.py` and its
test), the sandbox `../studie/`.

### Rules

- Only the workshop and the research environment are git repositories; the research environment's first commit
  names the workshop commit it was taken from.
- The analyst works only on research in the research environment. What changes in the analyst's role, the methods
  or the procedures is agreed by the owner with the builder in the workshop.
- Claude Code's memory folder of today's path goes with the workshop (it holds the builder's memory); the research
  environment starts with an empty memory.

## Consequences

- Kept from T11: `tests/fixtures/mini-studie/`, the `fabric-ocr` wheel pinned by path, the `mmo` topic argument
  taking a path.
- Renaming the folder needs VS Code and Claude Code closed; `.venv` is recreated with `uv sync` afterwards.
- `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/development.md`, `docs/spec.md` and the skills of the workshop change
  (protected paths, approved by the owner).
- Later: test research environments in `zkusebna/`, releasing `mmo` as a wheel into the research environment.
