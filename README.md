# MIXED-Method-Ontology

Infrastructure for qualitative and mixed-methods research: sources of a research topic become segments, codes,
categories, themes and relations in a versioned knowledge graph. The model proposes, the researcher decides, and
every statement leads back to an exact place in a source.

Status: early. The first source (a book) is ready as text. The environment for qualitative analysis is next; the
ontology and method modules are drafts (`docs/plan.md`).

Agents follow [`AGENTS.md`](AGENTS.md); the project's memory is in [`docs/`](docs/) (brief, spec, plan, answers,
progress, ADRs). The repository follows the Project Lab template, so it works with Claude Code, Antigravity CLI and
the lab.

## Layout

| Path | What |
| :--- | :--- |
| `code/mmo/` | the program and its command `mmo`: `core/` (topics, sources), `ingest/` (bringing sources in: OCR, reading order, segments) |
| `topics/<slug>/` | research topics - the only place for research data: sources, their text and segments, graph |
| `methods/` | one folder per method: research design, procedure, rules for agents, applications, sources (SKAD, grounded theory, thematic analysis) |
| `ontology/` | LinkML schema and mapping to standards |
| `docs/` | brief, spec, plan, answers, progress, ADRs |

## Quick start

```bash
uv sync && uv run pytest
cp .env.example .env            # fill in the gateway URL and key

uv run mmo topic new my-topic --title "My topic"
uv run mmo source add my-topic my-book --kind book --title "My book" --language ces
# put page photos or text files into topics/my-topic/sources/my-book/files/
uv run mmo ingest my-topic my-book --backend fabric      # everything: OCR, page numbers, order, text, segments
uv run mmo source check my-topic                         # what the sources still lack (citation, memo, ...)

# supplementary information about a source is a source of its own
uv run mmo source add my-topic review --kind article --role context --about my-book

uv run mmo source finalize my-topic my-book   # text.md for the analysis, from `text: {variant: ...}` in source.yaml
uv run mmo segment my-topic my-book --variant <variant>
```

Source preparation (OCR of page photos, reading order, single steps, the homelab OCR service):
[`docs/environment/source-preparation.md`](docs/environment/source-preparation.md).

`uv run python -m mmo` starts the health endpoint used by the lab preview (`/healthz`).
