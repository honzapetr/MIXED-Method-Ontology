# Plan

> Tasks `T<n>` with goal, acceptance criteria, verify command, paths and dependencies (`write-plan` skill).
> The next tasks build the environment for qualitative analysis; how it works is
> defined with the owner first, so T4-T6 are direction, not decided. The plan holds the building of the environment;
> a concrete analysis lives in its topic (`topics/<slug>/`: questions, goals, memos). Finished tasks on source
> preparation (T2-T3) are recorded in `docs/progress.md`; the tool is described in `docs/source-preparation.md`.

### T1 – Repository, ingest scripts and drafts (done)
- Goal: agent-ready repository with OCR and segmentation scripts and the first ontology and method drafts.
- Acceptance criteria: Project Lab layout; `mmo` CLI with `topic new`, `source scan`, `ocr run` (tesseract, openai),
  `ocr compare`, `segment`; LinkML draft and standards mapping; GT and TA method modules; tests pass.
- Verify: `uv run pytest`
- Paths: everything (initial commit).

### T7 – Instructions centred on the analysis (done)
- Goal: instructions, docs and plan describe source preparation (OCR) as a tool of the project (owner's
  answer 2026-11-13).
- Acceptance criteria: OCR detail moved from `docs/spec.md` and `README.md` to `docs/source-preparation.md` (nothing
  lost); brief scope and AGENTS.md (**protected path, changed by this task with the owner's approval**) no longer
  frame the project around OCR; the done source-preparation tasks removed from the plan (record in `docs/progress.md`); no code or data removed; links updated.
- Verify: `uv run pytest && python tools/agents_sync.py --check`
- Paths: `AGENTS.md`, `README.md`, `docs/`, `.agents/skills/ingest-sources/`, `.claude/skills/ingest-sources/`
- Depends on: T2g

### T8 – Design of the analysis environment (done)
- Goal: record how methods link purpose, research questions and theory, and the layers of the environment (approach
  as analytic moves, connections, theme map, theory), by walking one study: SKAD on `nazi-v-ai-dobe`.
- Acceptance criteria: `docs/research-design.md` with sources; `research_design` in every method module, checked by
  the method test; owner's answers in `docs/answers.md`; no analysis output yet.
- Verify: `uv run pytest tests/test_ontology_and_methods.py`
- Paths: `docs/`, `methods/`, `tests/test_ontology_and_methods.py`
- Depends on: T7

### T9 – Method folders and the development rules (done)
- Goal: each method in its own folder with its research design, procedure, rules for agents, applications and
  sources; SKAD added; `docs/` separates how the environment is built from how it works (owner 2026-11-14).
- Acceptance criteria: `methods/<id>/` for SKAD, GT and TA with all six files and `methods/_template/`;
  `methods/foundations.md`; `docs/research-design.md` split without loss into `methods/` (method content),
  `docs/spec.md` (planned research design in a topic) and `docs/environment/memos.md`; `docs/development.md`,
  `docs/README.md`, `docs/owner-notes.md`; source preparation moved to `docs/environment/`; links updated, including
  `AGENTS.md` and the `ingest-sources` skill (**protected paths, owner approved**); ADR 0008; topic records its method.
- Verify: `uv run pytest && python tools/agents_sync.py --check`
- Paths: `methods/`, `docs/`, `tests/test_methods.py`, `tests/test_ontology.py`, `AGENTS.md`, `README.md`,
  `ontology/schema/mmo.yaml`, `.agents/skills/ingest-sources/`, `.claude/skills/ingest-sources/`,
  `topics/nazi-v-ai-dobe/topic.yaml`
- Depends on: T8

### T10 – Reflexivity of researchers and models (done)
- Goal: reflexive techniques of qualitative research recorded for the methods, and applied to both analysts: the
  human researcher and every model, which writes notes about itself and writes them whenever a reason arises
  (owner 2026-11-14).
- Acceptance criteria: `methods/reflexivity.md` with sources; `reflexivity.md` in every method folder and the
  template, required by `tests/test_methods.py`; agent rules of each method require a profile, a positionality memo
  and notes on triggers; `docs/environment/analysts/` with README (roles, where notes go, triggers, gate questions),
  templates for a model and a researcher, the profile of `claude-opus-5-5`; `AGENTS.md` rule (**protected path,
  owner asked for the instructions**); ADR 0009; in the study the model's positionality memo and a question
  skeleton for the researcher's memo.
- Verify: `uv run pytest && python tools/agents_sync.py --check`
- Paths: `methods/`, `docs/`, `tests/test_methods.py`, `AGENTS.md`, `topics/nazi-v-ai-dobe/memos/`
- Depends on: T9

### T11 – Study as a repository of its own: `mmo study init` and a test study (done)
- Goal: the environment can create and serve a study that lives in its own git repository next to it, so the
  builder and the analyst roles are separated by folder (ADR 0010, owner 2026-11-14).
- Acceptance criteria: `mmo study init <path> --method <id> --title ...` creates a study folder with its own git,
  `pyproject.toml` (`mmo` as an editable path dependency), `topic.yaml` at its root (title, purpose, questions,
  goals, method, environment path and commit), `sources/`, `memos/`, `feedback.md`, `.gitignore` for page images, and `AGENTS.md`/`CLAUDE.md`
  for the analyst built from `methods/<id>/agent-rules.md`; the other `mmo` commands work on a study folder;
  a simulated study in `tests/fixtures/` used by the tests; `studie/piskoviste/` created and tried by hand (not in
  git of the environment); `docs/environment/` describes how to start a study; ADR 0010 accepted.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/`, `tests/`, `docs/`; `pyproject.toml`, `uv.lock`, `vendor/wheels/README.md` (wheel pinned by
  path, owner approved 2026-11-15)
- Depends on: T10

> T11 was built on a wrong reading of the owner's request; ADR 0011 supersedes ADR 0010. T12-T16 replace the
> earlier T12 ("move `nazi-v-ai-dobe` out").

### T12 – Decision: workshop and research environment (done)
- Goal: the split into the workshop and the research environment is recorded (owner 2026-11-15).
- Acceptance criteria: ADR 0011 with the layout of files of both repositories and of the test environments; ADR
  0010 marked superseded; the owner's answers in `docs/answers.md`; T13-T16 planned.
- Verify: review by the owner
- Paths: `docs/`
- Depends on: T11

### T13 – Rename today's repository to the workshop (done)
- Goal: today's repository becomes the workshop `MIXED-Method-Ontology-vyvoj/` with its history, so the name
  `MIXED-Method-Ontology/` is free for the research environment (ADR 0011).
- Acceptance criteria: the owner renames the folder with VS Code and Claude Code closed; Claude Code's memory folder
  of the old path is moved to the new path's key; `uv sync`, `uv run pytest` pass in the renamed folder; no
  `AGENTS.md` or `CLAUDE.md` in `2026/MIXED-Method-Ontology/`.
- Verify: `uv sync && uv run pytest`
- Paths: the folder itself, `~/.claude/projects/` (memory)
- Depends on: T12

### T14 – Create the research environment `MIXED-Method-Ontology/` (done; `/memory` check by the owner)
- Goal: the research environment is a repository of its own with everything the analyst needs and the study.
- Acceptance criteria: the folders that move (ADR 0011 table) copied; git-ignored page images of `nazi-v-ai-dobe`
  copied and checked against the hashes in `ingest/files.yaml`; `sample-masaryk-suicide` not copied (deleted, owner
  2026-11-14); new `AGENTS.md`/`CLAUDE.md` for the analyst only, `README.md`, `pyproject.toml` (`mmo` as an editable
  path dependency on `../MIXED-Method-Ontology-vyvoj`), `.gitignore`, `.env.example`, `.editorconfig`,
  `.gitattributes`, `.claude/settings.json`, `tools/agents_sync.py`; references to moved files point to their new
  paths; `git init` and a first commit naming the workshop commit; the owner sees the analyst's `AGENTS.md` before
  the commit.
- Verify: in the research environment `uv sync && uv run mmo source check nazi-v-ai-dobe`; Claude Code started
  there shows only the analyst's instructions (`/memory`)
- Paths: new repository `../MIXED-Method-Ontology/`
- Depends on: T13

### T15 – Clean the workshop
- Goal: the workshop holds no research and instructs only the builder.
- Acceptance criteria: `methods/`, `ontology/`, `topics/`, `docs/environment/` and the analyst skills removed;
  `mmo study init` (`code/mmo/core/study.py`, `tests/core/test_study.py`) and `docs/environment/studies.md` removed,
  the `mmo` topic argument keeps taking a path; `tests/test_methods.py`, `tests/test_ontology.py` read
  `../MIXED-Method-Ontology/`; `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/development.md`, `docs/spec.md`,
  `docs/README.md` rewritten for the builder (**protected paths, need the owner's approval**); sandbox `../studie/`
  deleted.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check . && python tools/agents_sync.py --check`
- Paths: `methods/`, `ontology/`, `topics/`, `docs/`, `code/mmo/`, `tests/`, `AGENTS.md`, `CLAUDE.md`, `README.md`,
  `.agents/`, `.claude/`
- Depends on: T14

### T16 – Model profiles from sources (research environment)
- Goal: a model working as an analyst knows what shapes its position and works with it; scalable to any model.
- Acceptance criteria: in `../MIXED-Method-Ontology/`: skill `profile-model` (identify the model from the harness,
  look for its profile, find sources, report to the owner, write with sources and certainty marks, status
  `proposed`, owner confirms; a local model's profile written by the session model); `analysts/_template-model.md`
  by the layers of `methods/reflexivity.md` §2 with "What follows for the analysis"; `AGENTS.md`: read your profile
  at the start of every session, without one run the skill first; profile of `claude-opus-5-5` rewritten from its
  system card and the maker's documents; `methods/reflexivity.md` §2 extended (filters, measured biases, hidden
  system prompt). Each profile complete on its own (owner, 2026-11-15).
- Verify: `python tools/agents_sync.py --check` in the research environment; the owner simulates the first start
  in a test copy
- Paths: `../MIXED-Method-Ontology/` (`.agents/skills/profile-model/`, `.claude/skills/`, `analysts/`, `AGENTS.md`,
  `methods/reflexivity.md`)
- Depends on: T14

### T17 – Test copies of the research environment in `zkusebna/` (done)
- Goal: one command makes a clean test copy of the research environment, e.g. to simulate a model's first start
  (owner 2026-11-15).
- Acceptance criteria: `tools/new_test_env.py` copies what git sees (tracked and untracked-not-ignored), never
  `.env`, `.venv/`, caches, `scratch/` or `.git/`; page images only with `--with-source-files`; `--without-profile`
  leaves out a model profile; no git unless `--git`; rewrites the workshop path in `pyproject.toml` and `uv.lock`;
  refuses an existing target and a target with `AGENTS.md`, `CLAUDE.md` or `.git` above it; logs each copy in
  `zkusebna/_log.tsv`; tests.
- Verify: `uv run pytest tests/test_new_test_env.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `tools/new_test_env.py`, `tests/test_new_test_env.py`, `docs/`
- Depends on: T16

### T18 – The analyst's role: profile × method × topic (research environment) (done; owner tests)
- Goal: the profile is the model's role as an analyst, and in each study it is joined with the method and the topic
  into a role for that study, framed again when the profile or the method changes (owner 2026-11-15; one study,
  one method).
- Acceptance criteria: in `../MIXED-Method-Ontology/`: skill `frame-role` (role memo
  `topics/<slug>/memos/<date>-role-<model-id>.md` before the data are read, with `profile_version`; owner confirms);
  `AGENTS.md` sets the role in three steps every session (profile, study and method, role memo) and asks to act
  from it whenever information is weighed; profile template and `profile-model` with a Role and a Version; Role in
  the profile of `claude-opus-5-5`; `analysts/README.md`, `methods/reflexivity.md`, the agent rules of the methods
  and `docs/memos.md` updated.
- Verify: `python tools/agents_sync.py --check` in the research environment; the owner tests a first start in a test
  copy
- Paths: `../MIXED-Method-Ontology/` (`.agents/skills/`, `.claude/skills/`, `AGENTS.md`, `analysts/`, `methods/`,
  `docs/memos.md`)
- Depends on: T16

### T19 – GitHub account asked when needed, not hard-coded (both repositories) (done)
- Goal: the instructions name no GitHub accounts and work for any researcher; the old positionality memo of the
  study goes (owner 2026-11-16).
- Acceptance criteria: in `AGENTS.md` of the workshop and of `../MIXED-Method-Ontology/` the account question is
  gone from "Before you start"; the Git rules say: no account for local commits, `gh auth status` shown to the owner
  and confirmed before the first push, pull request or `gh` command, never switch accounts, ask the owner to run it
  if `gh` fails; check `git config user.name/email` before the first commit. The memo
  `topics/nazi-v-ai-dobe/memos/2026-11-14-position-claude-opus-5-5.md` is deleted.
- Verify: `grep -rn "honzapetr\|Jan-dolphin" AGENTS.md ../MIXED-Method-Ontology/AGENTS.md` finds nothing; the owner
  tests a first start in a new test copy
- Paths: `AGENTS.md`, `docs/`, `../MIXED-Method-Ontology/` (`AGENTS.md`, `topics/nazi-v-ai-dobe/memos/`)
- Depends on: T18

### T20 – Analysts are the profile files, no hand-kept list (research environment) (done)
- Goal: `analysts/README.md` does not list the profiles by hand; the list went stale in a test copy without the
  profile and repeated the status the profile holds (owner 2026-11-16, test in `zkusebna/test4/`).
- Acceptance criteria: in `../MIXED-Method-Ontology/` the table "Analysts" in `analysts/README.md` is replaced by the
  rule that the analysts are the files `analysts/<id>.md` (not `_template-*`), status and version in each header;
  `profile-model` no longer adds a row; `.claude/` copies synced.
- Verify: `python tools/agents_sync.py --check` in the research environment
- Paths: `../MIXED-Method-Ontology/` (`analysts/README.md`, `.agents/skills/profile-model/`, `.claude/skills/`)
- Depends on: T19

### T21 – Positions apart from memos; profile without build history (research environment) (done)
- Goal: a memo is a note from research, not a position or a version; the analyst's own position and biases in a
  study are a statement of their own; the profile's journal holds research only, the build history is in git
  (owner 2026-11-16).
- Acceptance criteria: in `../MIXED-Method-Ontology/`: positions in `topics/<slug>/positions/<analyst-id>.md`
  (model: `profile_version`, `status`); skill `frame-role` renamed `state-position`; the profile section Role is
  Position; the Opus profile has no workshop task references and an empty journal; the researcher's draft moved to
  `positions/owner.md`; `AGENTS.md` step 2 is a discussion with the researcher where the study is not defined
  (sources, method, topic, questions, the researcher's position); method rules, templates, `docs/memos.md`,
  `analysts/README.md`, `topics/README.md` follow; `.claude/` synced.
- Verify: `python tools/agents_sync.py --check` in the research environment; no `role memo`, `frame-role` or
  `positionality memo` left there
- Paths: `../MIXED-Method-Ontology/` (`AGENTS.md`, `.agents/skills/`, `.claude/skills/`, `analysts/`, `methods/`,
  `docs/memos.md`, `topics/`)
- Depends on: T20

### T22 – Guards for the analyst in Claude Code (research environment) (done; owner tests)
- Goal: the analyst gets what it needs at the start and cannot leave the environment, skip steps or confirm on the
  owner's behalf (owner 2026-11-16).
- Acceptance criteria: a `SessionStart` hook loads only step 1 (the model's profile, its status and version); the
  study context is added to it once studies are defined with the researcher; a `PreToolUse` hook denies paths
  outside the project root, denies reading `sources/*/text.md` and segments of a study until the profile is
  confirmed and the model's position matches the profile version and is confirmed, and asks the owner (permission
  prompt) when a profile or a position is set to `confirmed`; the logic is an `mmo` command with tests, so other
  agents can run it too.
- Decided (owner 2026-11-16): when the hooks cannot run, the start reports `Guards: NOT running` and the model does
  no analytic step (`AGENTS.md`); test copies include the project files and run `uv sync` by default
  (`--without-project-files`, `--no-sync`).
- Built: `mmo-guard` (`code/mmo/guard.py`, standard library and PyYAML only); hooks in
  `../MIXED-Method-Ontology/.claude/settings.json` run `uv run --project "$CLAUDE_PROJECT_DIR" --no-sync mmo-guard`.
  Each guarded tool call costs about 1 s (Python start on the shared drive).
- Verify: `uv run pytest tests/test_guard.py tests/test_new_test_env.py && uv run ruff check . && uv run ruff format
  --check .`; the owner tests a session in a new test copy
- Depends on: T21

### T23 – Input documents of a study out of git (research environment) (done)
- Goal: while the environment is versioned, the study's input documents are not (owner 2026-11-17).
- Acceptance criteria: `topics/.gitignore` lists `nazi-v-ai-dobe/sources/`; the files leave the index and stay on
  disk; `topic.yaml`, `positions/` and `memos/` stay in git; `topics/README.md` says how; test copies still get the
  ignored sources (but not the scans).
- Verify: `uv run pytest tests/test_new_test_env.py && uv run ruff check . && uv run ruff format --check .`
- Depends on: T22

### Later (after the split)
- Check of the computer's environment, at the end of development (owner 2026-11-16): the start hook first checks
  what the environment needs (`uv`, `git`, the virtual environment from `uv sync`, the program `mmo`) and tells the
  researcher plainly what to install; where the guards cannot run, the model offers to install the missing
  dependencies; with `mmo` released as a package, so others can use the environment.
- A trial that the analyst role is clean in a test copy (`/memory`).
- Releasing `mmo` as a wheel into the research environment instead of the path dependency.

## Analysis

### T4 – Graph store and topic versioning
- Goal: segments and the topic in RDF (sorted Turtle files of record + Oxigraph index), versioned in git.
- Acceptance criteria: ADR on the graph store; `mmo graph build` writes Turtle per named graph and rebuilds the index;
  round-trip test; SPARQL query by segment id works.
- Verify: `uv run pytest tests/test_graph.py`
- Paths: `src/mixed_method_ontology/graph/`, `ontology/`, `tests/`, `docs/adr/`
- Depends on: T1

### T5 – Model backends for analysis
- Goal: one interface for LLM calls (gateway, local, optionally Claude) with structured output and quote checking.
- Acceptance criteria: backend per analysis step configured in the topic; every call recorded (model, prompt
  version, input segments); proposals with quotes that are not in the segment are rejected.
- Verify: `uv run pytest tests/test_llm.py`
- Paths: `src/mixed_method_ontology/llm/`, `tests/`
- Depends on: T4

### T6 – First analysis loop with review
- Goal: open coding (GT) / coding (TA) proposals into the graph and their review in the CLI.
- Acceptance criteria: proposals have status, author and provenance; `mmo review` confirms, edits, merges or rejects
  with reason; steering memos are stored and passed to the next step.
- Verify: `uv run pytest tests/test_review.py`
- Paths: `src/mixed_method_ontology/`, `methods/`, `tests/`
- Depends on: T5

Later: exports (SKOS, `.qdpx` tested in ATLAS.ti and QualCoder, report), querying a finished topic, adding material
with a change overview, quantitative link (DDI-CDI), read-only MCP server, UI.
