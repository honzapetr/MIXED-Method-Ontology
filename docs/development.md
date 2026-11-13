# How we develop the environment

> The working rules while the analysis environment is being built: what goes where. Agents and the owner follow
> them in every session. Status: agreed with the owner 2026-11-14 (T9).

## Two lines, kept apart

1. **Building the environment** – the methods, the program, the ontology and the project's memory of how it is
   built: `methods/`, `code/`, `tests/`, `ontology/`, `docs/`.
2. **The concrete analysis** – a study with its purpose, questions, sources, memos and results:
   `topics/<slug>/`.

The environment is built by walking one study through it (SKAD on `topics/nazi-v-ai-dobe/`). What the study shows
about the environment is written in line 1; what it shows about the book and its discourse stays in line 2.
Nothing about a concrete study goes to `docs/` or `methods/`; nothing about how a method works in general goes to
`topics/`.

## What goes where

| What | Where |
| :--- | :--- |
| A new method while it is developed | `methods/<id>/` copied from `methods/_template/`, `status: draft` |
| Literature and findings about a method | `methods/<id>/sources.md`, `methods/<id>/research-design.md` |
| The method's procedure, rules for agents, connected applications | `methods/<id>/procedure.md`, `agent-rules.md`, `applications.md` |
| Methodology shared by methods (overview, comparison) | `methods/foundations.md` – never instead of a method's own text |
| What the owner wants | `docs/brief.md` |
| How the environment will work (specification) | `docs/spec.md` |
| How a built part of the environment works (manual) | `docs/environment/` |
| Tasks and their record | `docs/plan.md`, `docs/progress.md` |
| The owner's decisions and answers | `docs/answers.md` |
| A significant decision with its reasons | `docs/adr/` |
| The owner's own notes while building | `docs/owner-notes.md` (written by the owner, in Czech – the one exception to English docs) |
| Program and its tests | `code/mmo/`, `tests/` |
| Schema and mapping to standards | `ontology/` |
| A study: title, purpose, questions, goals, chosen method, sources | `topics/<slug>/topic.yaml` |
| A source of the study and information about it | `topics/<slug>/sources/<id>/` (`source.yaml`, `notes.md`, `files/`, `text.md`) |
| Supplementary material about a source (reviews, interviews, announcements) | a source of its own with `role: context` |
| Notes, impressions and memos of the study | `topics/<slug>/memos/` (format `docs/environment/memos.md`) |
| Results of the analysis | `topics/<slug>/` (runs and graph, planned) |
| One-off scripts and temporary files | `scratch/T<n>/` (git-ignored) |

## Writing about methods

Precision before economy: each method is described completely in its own terms, even when the same information
appears in another method. Agents do not merge or shorten method texts, codes or memos to avoid repetition
(`docs/owner-notes.md`, 2026-11-14).

## Order of work in a task

The general rules (branch per task, commits, tests, protected paths) are in `AGENTS.md`. In addition:
- a finding about a method goes to its folder in the same task in which it is found;
- an owner's answer goes to `docs/answers.md` before it is acted on;
- a step of the study that teaches something about the environment is recorded in both lines: the result in the
  topic, the lesson for the environment in `methods/` or `docs/`.
