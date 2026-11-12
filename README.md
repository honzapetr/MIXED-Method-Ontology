# MIXED-Method-Ontology

Infrastructure for qualitative and mixed-methods research: sources of a research topic become segments, codes,
categories, themes and relations in a versioned knowledge graph. The model proposes, the researcher decides, and
every statement leads back to an exact place in a source.

Status: early. Ingest of scanned books (OCR variants, segmentation) works; the ontology and method modules are
drafts; the graph and analysis come next (`docs/plan.md`).

Agents follow [`AGENTS.md`](AGENTS.md); the project's memory is in [`docs/`](docs/) (brief, spec, plan, answers,
progress, ADRs). The repository follows the Project Lab template, so it works with Claude Code, Antigravity CLI and
the lab.

## Layout

| Path | What |
| :--- | :--- |
| `code/mmo/` | the program and its command `mmo`: `core/` (topics, sources), `ingest/` (OCR, page numbers, reading order, segments) |
| `topics/<slug>/` | research topics - the only place for research data: sources, OCR results, segments, graph |
| `methods/` | method modules (grounded theory, thematic analysis, ...) |
| `ontology/` | LinkML schema and mapping to standards |
| `docs/` | brief, spec, plan, answers, progress, ADRs |

## Quick start

```bash
uv sync && uv run pytest
cp .env.example .env            # fill in the gateway URL, key and a vision model
sudo apt install tesseract-ocr tesseract-ocr-ces

uv run mmo topic new my-topic --title "My topic"
# put page scans into topics/my-topic/sources/my-book/files/
uv run mmo source scan my-topic my-book
uv run mmo ocr run my-topic my-book --backend tesseract --scans 1-10
uv run mmo ocr run my-topic my-book --backend openai --model <vision-model> --scans 1-10
uv run mmo ocr run my-topic my-book --backend fabric --workers 2   # the homelab OCR service (ADR 0005)
uv run mmo ocr compare my-topic my-book          # add sources/my-book/ground-truth/scan-0001.txt for real CER
uv run mmo ocr numbers my-topic my-book                  # printed page numbers from the page edges
uv run mmo ocr order my-topic my-book --variant fabric   # reading order by printed page numbers
uv run mmo ocr book my-topic my-book --variant fabric    # whole text in reading order -> text/fabric.md
uv run mmo segment my-topic my-book --variant tesseract
```

`uv run python -m mmo` starts the health endpoint used by the lab preview (`/healthz`).

## OCR through the homelab (backend `fabric`)

The owner's AI Fabric runs an OCR service (dots.ocr for photos and scans, the main model for page numbers). This
project uses it through its client library `fabric-ocr`, vendored in `vendor/wheels/` (ADR 0005), so installing the
project needs no homelab access (CI on GitHub's runners works); **calling** the service works only from the owner's
LAN or VPN.

| Step | Command | Result |
| :--- | :--- | :--- |
| page text | `uv run mmo ocr run <topic> <source> --backend fabric --workers 2` | `sources/<source>/ingest/ocr/fabric/scan-NNNN.json` |
| page numbers | `uv run mmo ocr numbers <topic> <source>` | `sources/<source>/ingest/page-numbers.json` |
| reading order | `uv run mmo ocr order <topic> <source> --variant fabric` | `sources/<source>/ingest/order/fabric.yaml` + a report of gaps, duplicates and pages without a number |
| whole text | `uv run mmo ocr book <topic> <source> --variant fabric` | `sources/<source>/text/fabric.md` in reading order |

Every step saves page by page; a rerun reads only what is missing, so an interrupted run is simply started again.
Fix page numbers by hand with `printed_pages: {<image>: <page>}` in `source.yaml`, then rerun `order` and `book`.
How it works: `docs/spec.md` (Ingest pipeline); the first book: `docs/progress.md` (T2a).

**Setup on the owner's Windows computer:**

1. **uv 0.13 or newer** - older uv (0.6.8 was installed) cannot resolve the relative flat index `./vendor/wheels` and
   `uv sync` fails. Run `uv self update`, or call `uvx --from uv==0.13.5 uv ...`.
2. **Keep the virtual environment off Google Drive** - creating `.venv` on `G:` is very slow. Set
   `UV_PROJECT_ENVIRONMENT` to a folder on `C:` (e.g. `C:/Users/<you>/.venvs/mmo`).
3. **Address and token** come from `~/.config/fabric-ocr/env` (`FABRIC_OCR_URL`, `FABRIC_OCR_TOKEN`; the owner's is
   already set, token `cli-vlastnik`), or from `FABRIC_OCR_URL` / `FABRIC_OCR_TOKEN` in `.env` (`.env.example`).

**Known gap:** the skill `.agents/skills/ingest-sources` still describes only the `tesseract` and `openai` backends.
It is a protected path, so it was not changed in T2a; updating it with the `fabric` steps above is a good first task,
so that agents in this project know the workflow without reading the spec.
