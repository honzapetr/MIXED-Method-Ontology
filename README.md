# MIXED-Method-Ontology

Infrastructure for qualitative and mixed-methods research: sources of a research topic become segments, codes,
categories, themes and relations in a versioned knowledge graph. The model proposes, the researcher decides, and
every statement leads back to an exact place in a source.

Status: the source pipeline (any original -> `text.md` -> segments -> quotations) is built; the analytic layer is
next (`docs/plan.md`, ADR 0013).

This repository is the **workshop**: the program `mmo`, its tests, tools and the project's memory. The research
environment - methods, ontology, studies, analyst profiles - is the repository `../MIXED-Method-Ontology/`, which
uses `mmo` from here (ADR 0010, ADR 0011). Test copies of it are made with `tools/new_test_env.py`
(`docs/test-copies.md`).

Agents follow [`AGENTS.md`](AGENTS.md); the project's memory is in [`docs/`](docs/) (brief, spec, plan, answers,
progress, ADRs). The repository follows the Project Lab template, so it works with Claude Code, Antigravity CLI and
the lab.

## Layout

| Path | What |
| :--- | :--- |
| `code/mmo/` | the program and its command `mmo`: `core/` (topics, sources), `ingest/` (OCR, reading order, final text, segments), `analysis/` (quotations, the analytic layer), `guard.py` (the analyst's hooks) |
| `tests/` | tests; `test_methods.py` and `test_ontology.py` check the research environment when it is next to this repository |
| `tools/` | `new_test_env.py` (test copies), `agents_sync.py` |
| `docs/` | brief, spec, plan, answers, progress, ADRs, source pipeline, test copies |

## Quick start

```bash
uv sync && uv run pytest
cp .env.example .env            # fill in the gateway URL and key

uv run mmo topic new my-topic --title "My topic"
uv run mmo source add my-topic my-book --kind book --title "My book" --language ces
# put page photos or text files into topics/my-topic/sources/my-book/files/
uv run mmo ingest my-topic my-book --backend fabric      # OCR, page numbers, reading order, working text
uv run mmo source check my-topic                         # what the sources still lack (citation, memo, ...)

# supplementary information about a source is a source of its own
uv run mmo source add my-topic review --kind article --role context --about my-book

uv run mmo source finalize my-topic my-book   # text.md and its segments, from `text: {variant: ...}` in source.yaml
uv run mmo segment my-topic my-book            # cut the segments of text.md again
uv run mmo quote find my-topic my-book "exact words"   # a quotation: offsets, pages, scans
```

How every kind of source becomes `text.md`, segments and quotations: [`docs/source-pipeline.md`](docs/source-pipeline.md).
How the analyst prepares sources is described in the research environment (`docs/source-preparation.md` there).

`uv run python -m mmo` starts the health endpoint used by the lab preview (`/healthz`).
