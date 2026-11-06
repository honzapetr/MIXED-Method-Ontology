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
