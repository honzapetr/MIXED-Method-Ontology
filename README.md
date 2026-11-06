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
| `src/mixed_method_ontology/` | package and CLI `mmo` |
| `topics/<slug>/` | research topics: sources, OCR results, segments, graph |
| `methods/` | method modules (grounded theory, thematic analysis, ...) |
| `ontology/` | LinkML schema and mapping to standards |
| `docs/` | brief, spec, plan, answers, progress, ADRs |

## Quick start

```bash
uv sync && uv run pytest
cp .env.example .env            # fill in the gateway URL, key and a vision model
sudo apt install tesseract-ocr tesseract-ocr-ces

uv run mmo topic new my-topic --title "My topic"
# put page scans into topics/my-topic/sources/my-book/
uv run mmo source scan my-topic my-book
uv run mmo ocr run my-topic my-book --backend tesseract --pages 1-10
uv run mmo ocr run my-topic my-book --backend openai --model <vision-model> --pages 1-10
uv run mmo ocr compare my-topic my-book          # add ground-truth/my-book/page-0001.txt for real CER
uv run mmo segment my-topic my-book --variant tesseract
```

`uv run python -m mixed_method_ontology` starts the health endpoint used by the lab preview (`/healthz`).
