# How we develop the environment

> The working rules while the analysis environment is being built: what goes where. Agents and the owner follow
> them in every session. Agreed with the owner 2026-11-14 (T9); since T15 the two lines are two repositories
> (ADR 0010, ADR 0011).

## Two lines, two repositories

1. **Building the environment** – this workshop: the program `mmo`, its tests, tools and the project's memory of
   how it is built (`code/`, `tests/`, `tools/`, `docs/`).
2. **The environment and the research** – `../MIXED-Method-Ontology/`: methods, ontology, the analyst's
   instructions, skills and manuals, the analysts' profiles, and the studies in `topics/<slug>/`.

The environment is built by walking one study through it (SKAD on `topics/nazi-v-ai-dobe/` of the research
environment), tried in test copies (`docs/test-copies.md`). What the study shows about the environment is written
here as a task; what it shows about the book and its discourse stays in the study. Nothing about a concrete study
goes to this workshop.

## What goes where

| What | Where |
| :--- | :--- |
| What the owner wants | `docs/brief.md` |
| How the environment will work (specification) | `docs/spec.md` |
| Tasks and their record | `docs/plan.md`, `docs/progress.md` |
| The owner's decisions and answers | `docs/answers.md` |
| A significant decision with its reasons | `docs/adr/` |
| How sources become `text.md`, segments and quotations (for the builder) | `docs/source-pipeline.md` |
| Test copies of the research environment | `docs/test-copies.md`, `tools/new_test_env.py` |
| The owner's own notes while building | `docs/owner-notes.md` (written by the owner, in Czech – the one exception to English docs) |
| Program and its tests | `code/mmo/`, `tests/` |
| One-off scripts and temporary files | `scratch/T<n>/` (git-ignored) |
| Methods (one folder each, from `methods/_template/`), shared methodology, reflexivity | research environment: `methods/` |
| Schema and mapping to standards | research environment: `ontology/` |
| Manuals for the researcher and the analyst | research environment: `docs/`, `analysts/README.md` |
| Profiles of analysts (researchers, models) | research environment: `analysts/<id>.md` – each written by the analyst |
| A study: topic, sources, memos, positions, analysis | research environment: `topics/<slug>/` |

## Writing about methods

Precision before economy: each method is described completely in its own terms, even when the same information
appears in another method. Agents do not merge or shorten method texts, codes or memos to avoid repetition
(`docs/owner-notes.md`, 2026-11-14).

## Order of work in a task

The general rules (branch per task, commits, tests, protected paths) are in `AGENTS.md`. In addition:
- a task that changes the research environment does it on a branch of the same name there, and both are merged
  together; never check out an old commit there (the studies' input data are git-ignored and would be overwritten);
- a finding about a method goes to its folder in the research environment in the same task in which it is found;
- an owner's answer goes to `docs/answers.md` before it is acted on;
- a step of the study that teaches something about the environment is recorded in both lines: the result in the
  study, the lesson for the environment as a task here.
