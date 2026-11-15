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

### T13 – Test research environments
- Goal: the workshop can make a clean test research environment in `zkusebna/<name>/` to try the environment
  without touching `vyzkum/`.
- Acceptance criteria: a tool in `tools/` copies the research environment without `topics/`, `.git`, `.venv`,
  optionally adds `tests/fixtures/mini-studie/` or a copy of one study, writes `pyproject.toml` with `mmo` as an
  editable path dependency on the workshop; makes no git; refuses a target with `AGENTS.md`, `CLAUDE.md` or `.git`
  in a parent folder, and a non-empty target; tests in a temporary folder. `mmo study init`, `code/mmo/core/study.py`,
  its tests and `docs/environment/studies.md` removed; the `mmo` topic argument keeps taking a path.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check .`
- Paths: `tools/`, `code/mmo/`, `tests/`, `docs/`
- Depends on: T12

### T14 – Releasing `mmo` to the research environment
- Goal: the research environment uses a released `mmo`, never the workshop's working tree.
- Acceptance criteria: a tool builds the `mmo` wheel and puts it with the `fabric-ocr` wheel into the target's
  `vendor/wheels/`, pinned by path in the target's `pyproject.toml`; tested on a temporary target; the version of
  `mmo` is visible in the target's lock.
- Verify: `uv run pytest`, and in a test environment `uv sync && uv run mmo --help`
- Paths: `tools/`, `pyproject.toml`, `tests/`, `docs/`
- Depends on: T13

### T15 – Create the research environment `vyzkum/`
- Goal: the research environment is a repository of its own with everything the analyst needs and the studies; the
  workshop holds no research.
- Acceptance criteria: `vyzkum/` laid out as in ADR 0011 (`methods/`, `ontology/`, `analysts/`, `docs/`,
  `topics/nazi-v-ai-dobe/`, analyst skills, self-contained `AGENTS.md`/`CLAUDE.md` for the analyst, released `mmo`),
  fresh git whose first commit names the workshop commit; git-ignored page images copied and checked against the
  hashes in `ingest/files.yaml`; `uv run mmo source check nazi-v-ai-dobe` passes there; `sample-masaryk-suicide`
  deleted (owner 2026-11-14); the moved folders removed from the workshop; `AGENTS.md`, `CLAUDE.md`, `README.md`,
  `docs/development.md`, `docs/spec.md` and the skills of the workshop updated (**protected paths, need the owner's
  approval**); the parent folder holds no `AGENTS.md` or `CLAUDE.md`.
- Verify: in the workshop `uv run pytest && python tools/agents_sync.py --check`; in `vyzkum/` `uv sync && uv run
  mmo source check nazi-v-ai-dobe`
- Paths: `methods/`, `ontology/`, `topics/`, `docs/`, `AGENTS.md`, `CLAUDE.md`, `README.md`, `.agents/`, `.claude/`,
  `.gitignore`; new repository `../vyzkum/`
- Depends on: T14

### T16 – Trial in a test environment
- Goal: the analyst role is clean in a test environment.
- Acceptance criteria: a test environment made from `vyzkum/` with the simulated study; Claude Code started there
  loads only the analyst's instructions (checked with `/memory`) and takes `mini-studie` through `source check`,
  `ingest` and `segment`; findings reported to the owner; the test environment deleted afterwards.
- Verify: report to the owner
- Paths: `../zkusebna/`, `docs/progress.md`
- Depends on: T15

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
