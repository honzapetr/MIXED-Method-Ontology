# Specification

> Working specification. Parts marked **(planned)** are direction, not built yet; the owner will test variants
> before they are fixed.

## Concepts

| Concept | Meaning |
| :--- | :--- |
| Topic | A long-lived research project: research questions, goals, sources, analyses, graph. One folder in `topics/`. |
| Research question | A question of the topic. A topic usually has several. |
| Goal | What the author and the agent want to find out next; changes over time, every change recorded. |
| Source | A book, interview, field note, document or dataset, with metadata and provenance. |
| Page | One scanned image of a source, with its OCR results per backend. |
| Final text | `text.md` of a source: the one text the analysis reads, the same form for every kind of original (ADR 0012). |
| Segment | A paragraph of the final text with its place (source, scan, page) and character offsets in `text.md`; a rebuildable index for reading, batching and counting. |
| Quotation | What the analysis points to: the exact words of a passage with source, pages and offsets in `text.md`; any length, may cross a page break; made and checked by `mmo quote` (T26). |
| Method | An analytical method, one folder `methods/<id>/`: research design, procedure, rules for agents, applications, sources, and `method.yaml` (phases, code types, relation types, outputs) for agents and tests. |
| Analysis run **(planned)** | A step of a model: method phase × questions × chosen passages → proposals in `analysis/`. |
| Proposal **(planned)** | What a model writes - a code, reading, category, theme, relation or memo - with status `proposed` / `accepted` / `edited` / `rejected` / `superseded`, provenance and its quotations; the researcher's own records are not proposals (ADR 0013). |

## Repository layout

`code/mmo/` the program (ADR 0007: `core/` topic and sources, later graph and analysis; `ingest/` OCR, page
numbers, reading order, segments) · `topics/` research data, the only data folder · `methods/` method folders ·
`ontology/` schema and mapping · `docs/` project memory · `tests/` · `tools/`.

## Topic folder

Source-centric (ADR 0006, built in T2c): everything about one source is in its folder, and what the researcher
writes is kept apart from what the machine produces.

```
topics/<slug>/
  topic.yaml                  # title, questions, goals, methods: [<method id>], sources: [<id>, ...]
  memos/                      # memos of the study (researcher and models; Markdown with front matter)
  positions/                  # position of each analyst in the study (ADR 0009)
  analysis/                   # (planned, T32) source of truth of the analysis: codebook, codings, relations,
                              #   proposals, history - text files in git, written through mmo
  graph/                      # (planned, T30) a view: Turtle and index built from analysis/, not in git
  sources/<id>/
    source.yaml               # RESEARCHER: metadata, attributes, links, page-number fixes
    notes.md                  # RESEARCHER: context memo - why the source is here, how it came about
    files/                    # original files (page images git-ignored)
    text.md                   # FINAL: the text the analysis reads (from the variant chosen in source.yaml)
    segments.jsonl            # paragraphs of text.md with offsets in it (cut by mmo source finalize)
    ground-truth/scan-NNNN.txt  # optional hand-corrected scans for OCR evaluation
    ingest/                   # MACHINE: never edited by hand
      files.yaml              #   every original file: scan number, name, SHA-256
      ocr/<variant>/scan-NNNN.json
      page-numbers.json       #   printed page numbers read from the page edges
      order/<variant>.yaml    #   reading order report: gaps, duplicates, pages without a number
      text/<variant>.md       #   whole text of one working variant in reading order
```

**Scan and page.** `scan` is the position of a file in file-name order - the identity of an image. `page` is the
printed page number. Results are stored by scan; the reading order maps scans to pages.

**`source.yaml`** (all fields except `id` optional):

| Field | Meaning |
| :--- | :--- |
| `id`, `title` | identity and a human name |
| `kind` | `book`, `interview`, `field-note`, `document`, `article`, `web`, `dataset` |
| `role` | `primary` (default) or `context` - supplementary material about other sources |
| `about` | for `context`: ids of the sources it is about |
| `language` | ISO 639-3 (`ces`) |
| `citation` | `authors`, `year`, `title`, `publisher`, `isbn`, `url`, `accessed` |
| `attributes` | free key-value pairs (document variables / cases in QDA terms) |
| `questions` | ids of the topic's research questions the source serves |
| `printed_pages` | hand fixes `{<file>: <page>}` where reading the page number failed |
| `retakes` | `{<second photo>: <photo kept>}`: a page photographed twice; the second photo is left out of the reading order, the text and the segments |
| `text` | `{variant: <variant>}`: the OCR variant chosen as the final text; `mmo source finalize` builds `text.md` from it |
| `note` | one line; longer context goes to `notes.md` |

Page images stay out of git; `ingest/files.yaml` lists each file with its SHA-256 so results stay traceable.

**Supplementary information** (reviews, interviews with the author, context documents) is a source of its own with
`role: context` and `about`, ingested and segmented the same way, so statements drawn from it are traceable too.

## Source preparation

Every original (photos, PDF, web page, text file) becomes the same final `text.md`, its segments and, in the
analysis, quotations: converted by the program without AI, OCR only where there is no text layer (ADR 0012). The
whole pipeline – steps, formats, what is built and what is planned – is in `docs/source-pipeline.md`; the manual
with the commands and OCR backends is `docs/source-preparation.md` of the research environment.

## Homelab

The owner's infrastructure is described in the `honzapetr/aiops-homelab` repository. What matters here:

- **LLM gateway** (LiteLLM, OpenAI-compatible) is the single entry point for local models: `brain` (large model on
  the GPU server 3v1, started on demand by fabricd), `fast` (small model on the always-on Optiplex), `embed`
  (embeddings). Vision-capable models for OCR must be available there under some name.
- **fabricd** owns the GPUs and the power of 3v1. Long runs should hold a lease (planned; for now the owner makes
  sure the model is running).
- **ComfyUI** is for images and video; text analysis does not run there.
- Services are reachable only from the LAN or over WireGuard. Settings come from `.env` (see `.env.example`); no
  addresses or keys are hard-coded.

## Ontology (draft)

`ontology/schema/mmo.yaml` is a LinkML schema of the core classes. `ontology/mapping.md` maps them to SKOS, W3C Web
Annotation, PROV-O, DDI-CDI and REFI-QDA. Versions and exact scope of each standard must be verified before the
mapping is relied on.

## Analysis, graph and versioning (planned; ADR 0013)

- **Free analysis on a fixed core.** `mmo` checks integrity, never the method: a quotation is the exact words of
  `text.md`; every record has author and time (and model, prompt version for a model); what a model writes is a
  proposal until the researcher accepts, edits or rejects it; nothing disappears without a trace. A method's
  vocabulary and phases orient the work; strictness is set per study in `topic.yaml`.
- **Source of truth:** text files in `topics/<slug>/analysis/` (T32), plus `memos/` and `positions/`. Git keeps their
  history; acceptance is the status of a proposal, not a merge of branches.
- **Views**, built again at any time, never edited and not in git: the RDF graph (sorted Turtle and an Oxigraph
  index, T30) with its procedures (T38) and browser (T35), the REFI-QDA export (T34), the similarity index of
  segments (T37). Machine indexes are never carried between test copies.
- Every model call stores the model, prompt version and input quotations.

## Research design in a topic (planned)

How methods link purpose, questions and theory: `methods/foundations.md` and `research-design.md` of each method.
In a topic this means (proposal, T8):

1. **The purpose is recorded, not implied.** A topic states why it exists (problem, motive, for whom) and the
   researcher's position. Every question traces back to it.
2. **Questions are living objects.** Each research question has a type (qualitative, quantitative, mixed), an
   origin (from the purpose, from the framework, from a surprise in the analysis), a status (initial, refined,
   dropped, answered) and a history - which memo or finding changed it (Maxwell's "design in use").
3. **The conceptual framework is explicit:** sensitising concepts, prior theories, assumptions. The method says how
   the framework may be used.
4. **Theory is built from propositions.** A proposition connects confirmed concepts and relations, answers one or
   more questions, has evidence and counter-evidence (quotations) and a memo on how it was reached.
5. **Working with theory afterwards:** test it against new sources (confirms / extends / contradicts), compare it
   with prior theories, derive new questions - including quantitative ones (the mixed-methods link).
6. **Ontology:** today it has `ResearchQuestion` and `Goal`; it would need the purpose and position of the topic,
   a conceptual framework with sensitising concepts, and `Theory` / `Proposition` linked to questions and evidence.
7. **Reflexivity (T10):** every analyst of a topic – the researcher and each model – has a profile
   (`docs/environment/analysts/`) and a positionality memo at framing, writes reflexive notes when a trigger occurs
   and revisits the memo at synthesis (`methods/reflexivity.md`). The ontology would need `Analyst` (person or
   model version, PROV-O agent) linked to its profile, memos and steps.

Memos are part of every method; format and use: `docs/environment/memos.md`.

## Human steering (planned)

Framing (questions, goals, sensitising concepts, seed codebook) · review of proposals (accept, edit, reject with a
reason) · the researcher's own coding and memos, never gated · steering memos fed into later steps · choice of data for
the next round · a fixed codebook when the study asks for one (deductive mode). Phases of a method are a map: the
researcher says where the study is (`mmo phase`, T33) and moves freely; the phase decides only what a model may
propose. What the method calls the researcher's decisions (`researcher_decides`) are decisions, not locks.

## Out of scope now

Exports, MCP server, UI – see `docs/plan.md`. The analysis environment is the current focus; how it works is
defined with the owner before it is specified here.
