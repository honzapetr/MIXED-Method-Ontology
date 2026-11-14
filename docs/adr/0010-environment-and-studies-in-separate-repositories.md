# 10. The environment and the studies in separate repositories

- Status: accepted (2026-11-14, owner: T11 started; the real study moves in T12)

## Context

The repository holds two things: the environment for qualitative analysis (program `mmo`, methods, ontology, tests,
docs) and a concrete study (`topics/nazi-v-ai-dobe/`). `docs/development.md` keeps them apart only by folder. In
practice this mixes the agent's two roles: started here, Claude Code reads one `AGENTS.md` that tells it both to
build the environment (branches, tests) and to act as a positioned analyst. Its automatic memory is keyed to the git
repository, so the builder and the analyst share one memory. Trying an analysis step changes the repository that
is being developed, and tests have no small study of their own. The owner found this confusing.

What the sources say:
- A study is a *research compendium*: one folder or repository per study with inputs (read-only raw data), methods
  and outputs kept apart; general tools are published separately and used by the compendium as a dependency
  (The Turing Way, "Research compendia"; Marwick, Boettiger & Mullen 2018, The American Statistician 72(1)).
- Tests should run on simulated data so the code runs without the real material (The Turing Way, project setup).
- Claude Code loads `CLAUDE.md` from the folder it is started in and its parents; auto memory is shared by all
  folders of one git repository (code.claude.com/docs/en/memory).
- uv installs a local project as a path dependency (`editable = true`); path dependencies suit projects that need
  their own environment better than a workspace (docs.astral.sh/uv, Managing dependencies; Using workspaces).
- QDA applications (ATLAS.ti, QualCoder) keep the program apart from the project file (general knowledge of the
  model, not checked against their docs).

## Decision

- **Environment repository** (this one): `code/`, `methods/`, `ontology/`, `tests/`, `docs/`, the builder's
  `AGENTS.md`. It holds no real study; tests use a small simulated study in `tests/fixtures/`.
- **Study repository**, one per study, next to it: `2026/MIXED-Method-Ontology/studie/<slug>/`, its own git.
  It contains what `topics/<slug>/` contains today, a `pyproject.toml` with `mmo` as an editable path dependency,
  and its own `AGENTS.md`/`CLAUDE.md` for the analyst role, made by `mmo study init` from the method's
  `agent-rules.md`. The study records which commit of the environment and which method it works with.
- **Sandbox:** a throwaway study (`studie/piskoviste/`) for trying the environment on real use.
- **Feedback:** what a study teaches about the environment is written in the study's `feedback.md` and taken over
  by the builder in a task of the environment (the two lines of `docs/development.md`, now in two repositories).
- Both stay on Google Drive (owner).
- **uv:** a relative flat index of a path dependency is resolved against the folder uv runs in, not against the
  dependency (tried in T11 with uv 0.6.8 and 0.13.8). The vendored `fabric-ocr` wheel is therefore pinned by its
  file path (`tool.uv.sources`), which uv resolves against the environment; it still never comes from PyPI
  (ADR 0005).

## Consequences

- `mmo` works on a study folder as well as on `topics/` inside the environment (`docs/environment/studies.md`).
- The real study moves out with its history since the rename (`git subtree split`); older history stays in this
  repository. Git-ignored page images are moved by hand.
- `AGENTS.md`, `README.md`, `docs/development.md`, `docs/spec.md` and the skills that point to `topics/` change
  (`AGENTS.md` and skills are protected paths).
- Open: where analyst profiles live (environment or next to the studies), GitHub for studies – both later (owner).
