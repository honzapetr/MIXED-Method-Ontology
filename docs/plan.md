# Plan

> Tasks `T<n>` with goal, acceptance criteria, verify command, paths and dependencies (`write-plan` skill).
> T1 is done (repository setup). The rest is the proposed order; the owner decides after testing OCR on real scans.

### T1 – Repository, ingest scripts and drafts (done)
- Goal: agent-ready repository with OCR and segmentation scripts and the first ontology and method drafts.
- Acceptance criteria: Project Lab layout; `mmo` CLI with `topic new`, `source scan`, `ocr run` (tesseract, openai),
  `ocr compare`, `segment`; LinkML draft and standards mapping; GT and TA method modules; tests pass.
- Verify: `uv run pytest`
- Paths: everything (initial commit).

### T2 – OCR tuning on real scans
- Goal: choose the OCR variant for the first book from measured results.
- Acceptance criteria: 5-10 sample pages scanned; at least Tesseract and one local vision model through the gateway
  run; 2-3 pages corrected by hand as ground truth; `mmo ocr compare` report and a recommendation (CER, seconds per
  page) in `docs/progress.md`; prompt or preprocessing changes covered by tests.
- Verify: `uv run pytest && uv run mmo ocr compare <topic> <source>`
- Paths: `src/mixed_method_ontology/ocr/`, `topics/`, `tests/`, `docs/progress.md`
- Depends on: T1. Runs on the owner's computer (homelab reachable).

### T2a – Fabric OCR backend and reading order
- Goal: read the first book (213 phone photos, taken out of order) with the homelab OCR service and sort its pages
  by the printed page numbers.
- Acceptance criteria: backend `fabric` with the vendored client (ADR 0005), parallel pages, a failed page does not
  stop the run; `mmo ocr numbers` (page numbers from the page edges); `mmo ocr order` (printed / inferred / manual / unknown, gaps, duplicates) and `mmo ocr book`;
  segments in reading order; the book read and its order report in `docs/progress.md`.
- Verify: `uv run pytest && uv run mmo ocr order nazi-v-dobe-ai kniha --variant fabric`
- Paths: `src/mixed_method_ontology/`, `tests/`, `vendor/wheels/`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `docs/`,
  `topics/nazi-v-dobe-ai/`
- Depends on: T1. Runs on the owner's computer (homelab reachable). Takes the printed page numbers from T3.

### T2b – Code layout by function
- Goal: the program lives in `code/mmo/`, split into the project core and the ingest of new data, so nobody takes
  it for research sources (ADR 0007, owner's answer 2026-11-12).
- Acceptance criteria:
  - `src/mixed_method_ontology/` moved to `code/mmo/` with `git mv` (history kept): `cli.py`, `__main__.py`,
    `config.py`; `core/topic.py`; `ingest/ocr/`, `ingest/page_numbers.py`, `ingest/order.py`, `ingest/segment.py`,
    `ingest/compare.py` (was `metrics.py`);
  - package `mmo`; command `mmo` and every subcommand behave as before; no `src/` left;
  - `pyproject.toml`, `uv.lock`, `Dockerfile`, tests (split into `tests/core/`, `tests/ingest/`), README, spec
    updated; the empty `data/` folder is gone (done 2026-11-12);
  - `AGENTS.md` section Project specifics: layout line names `code/mmo/` (**protected path, changed by this task
    with the owner's approval**);
  - no behaviour change: the same tests pass, none weakened.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mmo --help`
- Paths: `src/`, `code/`, `tests/`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `README.md`, `AGENTS.md`, `docs/`
- Depends on: T2a

### T2c – Source-centric topic layout
- Goal: store everything about a source in its own folder, researcher-written files apart from machine output
  (ADR 0006, owner's answer 2026-11-12).
- Acceptance criteria:
  - all paths come from `Topic` / `Source` and follow `docs/spec.md`, section Topic folder; every `mmo` command
    reads and writes there;
  - `source.yaml` holds only researcher fields; `mmo source scan` writes `ingest/files.yaml` and finds files in
    `files/`; `topic.yaml` `sources` lists the topic's sources;
  - OCR JSON uses `scan` (files `scan-NNNN.json`), segment ids `<source>:s<scan>:<n>`; readers still accept the
    old `page` key;
  - `mmo topic new` creates `sources/`, `memos/`, `graph/`;
  - `mmo topic migrate <topic>` moves an old-layout topic to the new one; OCR text and provenance unchanged
    (test: every `text` and `image_sha256` identical before and after); a second run changes nothing;
  - `nazi-v-dobe-ai` migrated (images moved to `files/` locally), `order` and `book` rerun with the same result;
  - README, `topics/README.md` updated.
- Verify: `uv run pytest && uv run mmo ocr order nazi-v-dobe-ai kniha --variant fabric`
- Paths: `code/mmo/`, `tests/`, `topics/`, `.gitignore`, `README.md`, `docs/`
- Depends on: T2b

### T2d – Adding a source in one step, context sources
- Goal: add a new source - primary or supplementary - with one command that runs the whole ingest.
- Acceptance criteria:
  - `mmo source add <topic> <id> --kind ... [--role context --about <id>] [--title ...]` creates the folder,
    `source.yaml`, `notes.md` and `files/`, and adds the id to `topic.yaml`;
  - `mmo ingest <topic> <source> [--backend fabric]` runs scan, OCR, page numbers, order and text for images; plain
    text and Markdown files are taken as text without OCR (variant `original`); resumable; ends with what to review;
  - `mmo source check <topic> [<source>]` lists what is missing: citation, attributes, questions, `about` of a
    context source, unreviewed order problems;
  - skill `ingest-sources` updated to this workflow including the `fabric` backend (**protected path, changed by
    this task with the owner's approval**; `.claude/` copy regenerated by `tools/agents_sync.py`);
  - tests for each command with fake backends.
- Verify: `uv run pytest && python3 tools/agents_sync.py --check`
- Paths: `code/mmo/`, `tests/`, `.agents/skills/ingest-sources/`, `.claude/skills/ingest-sources/`,
  `README.md`, `docs/`
- Depends on: T2c. PDF with a text layer and audio transcripts: later, as their own tasks.

### T2e – OCR clean-up and stuck pages
- Goal: a clean text of the first book without losing information: remove OCR junk by rules, find the pages where
  the OCR model got stuck in a loop and replace them with a new reading (owner's request 2026-11-12).
- Acceptance criteria:
  - `mmo ocr clean <topic> <source> --variant V [--fallback W]` writes the variant `V-clean` next to `V` (`V` is
    never changed); rules: separator lines, runs of number-only lines, a long line repeated within a page, a phrase
    repeated within a line; every removed or shortened line is kept in the record (`cleaning.removed`: line, rule)
    so the raw text can be restored;
  - a page is marked `stuck` (`cleaning.stuck` with reasons) when the rules found a loop; with `--fallback W` every
    scan that variant `W` has takes its text (`cleaning.replaced_from`) - also a short page the rules cannot see;
    a stuck page without a new reading stays marked;
  - `mmo ocr import <topic> <source> <folder> --variant W --model M --prompt-version P` stores hand or model
    transcriptions (`scan-NNNN.txt`) as an OCR variant with image hash, model, prompt version and time;
  - `mmo source check` lists stuck pages that have no replacement;
  - the 19 stuck scans of `kniha` transcribed (OCR service unavailable; owner approved a cloud model,
    variant `claude`), `fabric-clean` built with `--fallback claude`, order and book rerun;
  - tests with small invented texts for every rule.
- Verify: `uv run pytest && uv run mmo ocr clean nazi-v-dobe-ai kniha --variant fabric --fallback claude`
- Paths: `code/mmo/`, `tests/`, `topics/nazi-v-dobe-ai/sources/kniha/ingest/`,
  `topics/nazi-v-dobe-ai/sources/kniha/text/`, `README.md`, `docs/`
- Depends on: T2d.

### T2f – Reading the book with a cloud model
- Goal: a reliable text of `kniha` for the analysis without more local OCR tuning (owner's request 2026-11-13).
- Acceptance criteria:
  - a model comparison on scans with an Opus reading (`claude`) picks the smallest model that reads well enough;
    result recorded in the progress entry (owner chose Claude Sonnet 5.5 and approved the cloud model);
  - every scan without a `claude` reading transcribed with the same instructions as `claude`, stored with
    `mmo ocr import` as the variant `sonnet` (model, prompt version, image hash, time); the prompt saved next to it;
  - a combined variant of the whole book from `claude` and `sonnet` (`mmo ocr merge`, variant `book`), its reading
    order and text built; photo rotation as seen by the model recorded; in the reading order the number a
    transcription of the whole page carries goes before the number read from the page edges;
  - the pages missing from the book, the duplicates and the pages without a number listed for the owner.
- Verify: `uv run pytest && uv run mmo ocr order nazi-v-dobe-ai kniha --variant book`
- Paths: `code/mmo/`, `tests/`, `topics/nazi-v-dobe-ai/sources/kniha/ingest/`,
  `topics/nazi-v-dobe-ai/sources/kniha/text/`, `docs/`
- Depends on: T2e.

### T3 – Image preprocessing and page layout
- Goal: improve OCR input and drop running headers / page numbers from segments.
- Acceptance criteria: optional deskew/contrast step; header and page-number lines detected and stored apart from
  segments; printed page numbers recorded when found.
- Verify: `uv run pytest tests/test_segment.py`
- Paths: `src/mixed_method_ontology/`, `tests/`
- Depends on: T2

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
