# AGENTS.md – MIXED-Method-Ontology

Ontology and tooling for qualitative and mixed-methods research: sources become segments, codes, categories, themes and relations in a versioned knowledge graph.

This file is the single source of instructions for every coding agent working here (Claude Code, Antigravity CLI and
others). Agent-specific files (`CLAUDE.md`, `.claude/`) only add to it.

## Before you start

* Read `docs/brief.md`, `docs/spec.md`, `docs/plan.md` and the end of `docs/progress.md`. They are the memory of the
  project – do not rely on what you think was done before.
* Find your task in `docs/plan.md` (ID `T<n>`). Work on that task only.

## Commands

| Purpose | Command |
| :--- | :--- |
| Set up | `uv sync` |
| Test | `uv run pytest` |
| Lint and format check | `uv run ruff check . && uv run ruff format --check .` |
| Preview | `docker compose -f compose.preview.yaml up --build` → `http://<lab>:8400/healthz` |

The same commands are in `.agents/lab.yaml`, which the lab uses. Run the task's `verify` command from the plan before
you claim a task is done, and quote its result.

## How work is organised

1. `docs/brief.md` – what the owner wants (goal, scope, non-goals). Written with the owner; change only on request.
2. `docs/spec.md` – how it will work (behaviour, data, interfaces, constraints).
3. `docs/plan.md` – small tasks `T<n>`, each with acceptance criteria, a `verify` command and the paths it touches.
4. `docs/answers.md` – the owner's answers to questions; they override earlier assumptions.
5. `docs/progress.md` – append a short entry after every task: what changed, what is left, what the next session
   must know.
6. `docs/adr/` – one file per significant decision (context, decision, consequences).
7. `docs/development.md` – the working rules while the environment is built: building the environment and the
   concrete analysis are two lines kept apart, and what goes where. Follow it in every session.

## Rules

* **Git:** one branch per task, `task/T<n>-<short-name>`; Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`,
  `refactor:`, `chore:`); small commits. **Never push to `main`** and never force-push.
* **GitHub account:** local commits need none. Before the first operation in a session that talks to GitHub (push,
  pull request, any `gh` command), run `gh auth status`, tell the owner which account is active and which others are
  logged in, and wait for their confirmation. Never switch accounts or log in on your own. If `gh` cannot run, ask
  the owner to run `gh auth status` and share the result. Headless runs in the lab use the account the lab gives
  them.
* **Git identity:** before the first commit in a session, check `git config user.name` and `git config user.email`
  and ask the owner if they are unset or look unexpected.
* **Scope:** change only what the task needs. If the task needs more, stop and ask.
* **Tests:** new behaviour comes with tests; never delete or weaken a test to make it pass.
* **Dependencies:** commit lock files (`uv.lock`, `package-lock.json`) together with the change that updates them.
* **Questions:** never guess product decisions (behaviour, data, scope, money, security). Ask – interactively, or in
  the outcome of a headless run (below).
* **Secrets:** never read, print or write `.env` or any credentials. Use `.env.example` for new settings.
* **Protected paths** – change them only when the task explicitly says so; such a change is always approved by the
  owner, never merged automatically: `.github/`, `.claude/`, `.agents/roles/`, `.agents/skills/`, `.agents/lab.yaml`,
  `AGENTS.md`, `CLAUDE.md`, `tools/agents_sync.py`.
* **Language:** code, comments, commits and docs in English.
* **One-off scripts and temporary files** (decoding, image crops, quick counts, test inputs) go only to `scratch/`
  (git-ignored), one subfolder per task (`scratch/T<n>/`), never elsewhere in the repository. When the task ends,
  delete what is no longer needed; a script worth keeping for later analysis stays there and is named in the task's
  `docs/progress.md` entry. A script whose output enters the analysis is not a one-off: it becomes an `mmo` command
  in `code/mmo/` with tests, so every result can be traced to the code that made it.

## Headless runs in the lab

The lab runs agents without a person at the keyboard. At the end of every run write `.agents/state/outcome.json`
(schema `.agents/outcome.schema.json`):

```json
{"status": "done", "summary": "what was done and how it was verified", "questions": []}
```

* `done` – the step is finished and verified.
* `question` – you need the owner's decision; put each question in `questions`, self-contained, with the options you
  see and your recommendation. Stop after writing it.
* `blocked` – something outside the project stops you (missing access, broken tool); explain in `summary`.

## Skills and roles

Workflows live in `.agents/skills/` (Agent Skills format): `write-plan`, `implement-task`, `review-task`,
`ingest-sources`. Role
prompts for the lab live in `.agents/roles/`. Copies for Claude Code in `.claude/` are generated by
`python3 tools/agents_sync.py` – edit the source in `.agents/`, never the copies.

## Project specifics

* **Talk to the owner in Czech**; code, comments, commits and docs stay in English.
* **Layout:** `code/mmo/` (the program, CLI `mmo`: `core/` topics and sources, `ingest/` bringing new sources in),
  `topics/<slug>/` (research topics, the only place for research data: sources, their text, segments, graph),
  `methods/<id>/` (one folder per method: research design, procedure, rules for agents, applications, sources,
  `method.yaml`), `ontology/` (LinkML schema and mapping to standards), `docs/` (project memory and, in
  `docs/environment/`, how the environment works). Details: `docs/development.md`, `docs/spec.md`.
* **Methods: precision before economy.** Describe each method completely in its own terms, even where it repeats
  another; never merge, shorten or "deduplicate" method texts, codes or memos on your own (`methods/README.md`).
* **Reflexivity: models are positioned analysts.** A model used for the first time writes its own profile in
  `docs/environment/analysts/` before any analytic step, and writes a short reflexive note at once whenever a
  trigger listed in `docs/environment/analysts/README.md` occurs (e.g. the owner corrects it, it used background
  knowledge, it merged or softened something, the material concerns AI or its maker). The human researcher does
  the same in their own profile and memos.
* **Source preparation** (OCR of page photos, reading order, transcription) is a tool of the project, used when a
  new source needs it (`docs/environment/source-preparation.md`). The analysis reads `sources/<id>/text.md` and its segments,
  not `ingest/`.
* **CLI:** `uv run mmo --help` – `topic new`, `source add`, `source check`, `source finalize`, `segment`; tools for
  bringing sources in: `ingest`, `ocr ...`.
* **Traceability is the core rule:** every analytic record carries its author and time, and for a model the model
  and prompt version. Codes and everything a model proposes must be traced to quotations (the exact words with
  source, pages and offsets in `text.md`, ADR 0012); a reflexive or methodological memo and an idea of the
  researcher may stand without one. What a model writes is a proposal until the researcher accepts it (ADR 0013).
* **The analysis is free:** `mmo` checks integrity (the rule above), never the method. A method's vocabulary and
  phases are orientation; strictness is set by the researcher per study (ADR 0013). Never hard-wire one method.
* **Sources:** page images and other source files are git-ignored (size, copyright); commit only manifests, the
  text and segments.
* **Models:** local first, through the OpenAI-compatible gateway configured in `.env`. Homelab services are
  reachable only from the owner's LAN or VPN – if a call fails from elsewhere, report it as `blocked`, do not work
  around it. A cloud model needs the owner's approval.
* **Nothing is final yet:** keep every variant's output side by side instead of overwriting.
