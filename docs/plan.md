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

### T11 – Study as a repository of its own: `mmo study init` and a test study
- Goal: the environment can create and serve a study that lives in its own git repository next to it, so the
  builder and the analyst roles are separated by folder (ADR 0010, owner 2026-11-14).
- Acceptance criteria: `mmo study init <path> --method <id> --title ...` creates a study folder with its own git,
  `pyproject.toml` (`mmo` as an editable path dependency), `study.yaml` (title, purpose, questions, goals, method,
  environment commit), `sources/`, `memos/`, `feedback.md`, `.gitignore` for page images, and `AGENTS.md`/`CLAUDE.md`
  for the analyst built from `methods/<id>/agent-rules.md`; the other `mmo` commands work on a study folder;
  a simulated study in `tests/fixtures/` used by the tests; `studie/piskoviste/` created and tried by hand (not in
  git of the environment); `docs/environment/` describes how to start a study; ADR 0010 accepted.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/`, `tests/`, `docs/`
- Depends on: T10

### T12 – Move `nazi-v-ai-dobe` out of the environment
- Goal: the real study lives in `studie/nazi-v-ai-dobe/` and the environment holds no study.
- Acceptance criteria: study repository made with `mmo study init`, its content and history since the rename taken
  over (`git subtree split`), git-ignored page images copied and checked against the hashes in `ingest/files.yaml`;
  `mmo source check` passes there; `topics/nazi-v-ai-dobe/` removed from the environment, `sample-masaryk-suicide`
  moved to the fixtures or removed (owner decides); references to `topics/` updated in `AGENTS.md`, `README.md`,
  `docs/`, `methods/` and the skills (**protected paths, need the owner's approval**).
- Verify: `uv run pytest && python tools/agents_sync.py --check`, and in the study `uv run mmo source check`
- Paths: `topics/`, `AGENTS.md`, `README.md`, `docs/`, `methods/`, `.agents/skills/`, `.claude/skills/`, `.gitignore`
- Depends on: T11

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
