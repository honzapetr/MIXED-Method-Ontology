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
| Segment | A span of source text with an exact position (source, page, paragraph, character offsets). |
| Method | A declarative description of an analytical method (`methods/*.yaml`): phases, code types, relation types, outputs. |
| Analysis run **(planned)** | Method × questions × selected segments → proposals in the graph. |
| Proposal **(planned)** | A code, category, theme, relation or memo with status `proposed` / `confirmed` / `rejected`, author and provenance. |

## Repository layout

`code/mmo/` the program (ADR 0007: `core/` topic and sources, later graph and analysis; `ingest/` OCR, page
numbers, reading order, segments) · `topics/` research data, the only data folder · `methods/` method modules ·
`ontology/` schema and mapping · `docs/` project memory · `tests/` · `tools/`.

## Topic folder

Source-centric (ADR 0006, built in T2c): everything about one source is in its folder, and what the researcher
writes is kept apart from what the machine produces.

```
topics/<slug>/
  topic.yaml                  # title, questions, goals, sources: [<id>, ...]
  memos/                      # topic memos, research journal (written by the researcher)
  graph/                      # (planned) sorted Turtle per named graph
  sources/<id>/
    source.yaml               # RESEARCHER: metadata, attributes, links, page-number fixes
    notes.md                  # RESEARCHER: context memo - why the source is here, how it came about
    files/                    # original files (page images git-ignored)
    text/<variant>.md         # READ: whole text of one variant in reading order
    segments/<variant>.jsonl  # segments of one variant
    ground-truth/scan-NNNN.txt  # optional hand-corrected scans for OCR evaluation
    ingest/                   # MACHINE: never edited by hand
      files.yaml              #   every original file: scan number, name, SHA-256
      ocr/<variant>/scan-NNNN.json
      page-numbers.json       #   printed page numbers read from the page edges
      order/<variant>.yaml    #   reading order report: gaps, duplicates, pages without a number
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
| `note` | one line; longer context goes to `notes.md` |

Page images stay out of git; `ingest/files.yaml` lists each file with its SHA-256 so results stay traceable.

**Supplementary information** (reviews, interviews with the author, context documents) is a source of its own with
`role: context` and `about`, ingested and segmented the same way, so statements drawn from it are traceable too.

## Ingest pipeline

1. **Add and inspect** – `mmo source add` creates the source (`--role context --about <id>` for supplementary
   material); the agent lists its files and proposes a parsing plan (skill `ingest-sources`). `mmo ingest` then
   runs steps 2, 3 and 5 for it in one go (resumable) and ends with what to review; text files (`.txt`, `.md`)
   skip OCR and become the variant `original`, in file-name order. `mmo source check` lists what a source
   still lacks: citation, attributes, questions, `about`, the memo, unreviewed reading-order problems.
2. **OCR** – `mmo ocr run` sends every page image to one backend and stores one JSON per page:
   `scan`, `image`, `image_sha256`, `backend`, `model`, `prompt_version`, `text`, `confidence` (if known),
   `quality` and `warnings` (if the backend reports them), `seconds`, `created`. Results of different backends live
   side by side, so variants can be compared. `scan` (formerly `page`) is the **scan number** (file-name order), the identity of an
   image; `--workers N` reads N pages at once, and a failed page does not stop the others (a rerun retries it).
3. **Order** – `mmo ocr numbers` reads the printed page number from the top and bottom edge of every image (the
   strips go to the fabric service's Extract: OCR models leave headers and footers out of the page text, Tesseract
   cannot read a lone number from a photo); results in `ingest/page-numbers.json` of the source, resumable. `mmo ocr order` takes
   that number, else a line that is only a number among the first or last three lines of the OCR text, and sorts the
   pages by it. A page without a number between two pages two apart gets
   the number between them (`inferred`); a number set by hand in `source.yaml` (`printed_pages: {<image>: <page>}`)
   wins (`manual`); other pages stay `unknown` and follow the page photographed before them. The report lists missing
   pages, numbers found twice (a retaken photo or a misread number) and unknown pages. `mmo ocr book` writes the whole
   text in that order, each page under a comment with its printed number, scan number and image.
4. **Compare** – `mmo ocr compare` reports the character error rate (CER) of each backend against ground truth when
   it exists, otherwise between two backends.
5. **Segment** – `mmo segment` joins the text of one backend's pages in reading order, repairs words hyphenated across line ends and
   splits paragraphs into segments with ids `<source>:s<scan>:<n>` and character offsets into the scan's text.

### OCR backends

| Backend | How | Notes |
| :--- | :--- | :--- |
| `tesseract` | local `tesseract` binary, language `ces` by default | free, offline baseline; needs `tesseract-ocr-ces` |
| `openai` | OpenAI-compatible `chat/completions` with the image as a data URL | the homelab LiteLLM gateway, Ollama or vLLM; Claude can sit behind the same gateway |
| `fabric` | the homelab AI Fabric's OCR service through its client library `fabric-ocr` (ADR 0005) | the service turns photos upright, reads them with its OCR model (started on demand) and falls back to Tesseract (`quality: basic`); `--mode fast` = CPU only; 2 pages at once |

Backends are registered in `code/mmo/ingest/ocr/`; a new one implements `OcrBackend.recognize()`.

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

## Graph and versioning (planned)

- The graph is RDF. Files of record are sorted Turtle per named graph in `topics/<slug>/graph/`; an Oxigraph store is
  a rebuildable index for SPARQL queries.
- Git gives versions: `main` = confirmed state of the topic, a branch = another angle, another method or a new batch
  of material before review; merge = accept. PROV-O records why something changed.
- Every model call stores the model, prompt version and input segments.

## Human steering (planned)

Framing (questions, goals, sensitising concepts, seed codebook) · review of proposals (confirm, edit, merge,
reject with reason) · steering memos fed into later steps · choice of data for the next round · locking the
codebook (deductive mode). Gates between method phases: the next phase starts from confirmed state only.

## Out of scope now

Analysis engine, graph store, exports, MCP server, UI – see `docs/plan.md`.
