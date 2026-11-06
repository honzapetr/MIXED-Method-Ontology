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

## Topic folder

```
topics/<slug>/
  topic.yaml            # title, questions, goals, sources (versioned)
  sources/<source-id>/  # source.yaml (metadata) + page images (images are git-ignored)
  work/ocr/<backend>/<source-id>/page-NNNN.json
  work/segments/<source-id>.jsonl
  ground-truth/<source-id>/page-NNNN.txt   # optional hand-corrected pages for OCR evaluation
  graph/                # (planned) sorted Turtle per named graph
```

Page images stay out of git; `source.yaml` lists each image with its SHA-256 so results stay traceable.

## Ingest pipeline

1. **Inspect** – the agent lists the files of a source and proposes a parsing plan (skill `ingest-sources`).
2. **OCR** – `mmo ocr run` sends every page image to one backend and stores one JSON per page:
   `page`, `image`, `image_sha256`, `backend`, `model`, `prompt_version`, `text`, `confidence` (if known),
   `seconds`, `created`. Results of different backends live side by side, so variants can be compared.
3. **Compare** – `mmo ocr compare` reports the character error rate (CER) of each backend against ground truth when
   it exists, otherwise between two backends.
4. **Segment** – `mmo segment` joins the text of one backend's pages, repairs words hyphenated across line ends and
   splits paragraphs into segments with ids `<source>:p<page>:<n>` and character offsets into the page text.

### OCR backends

| Backend | How | Notes |
| :--- | :--- | :--- |
| `tesseract` | local `tesseract` binary, language `ces` by default | free, offline baseline; needs `tesseract-ocr-ces` |
| `openai` | OpenAI-compatible `chat/completions` with the image as a data URL | the homelab LiteLLM gateway, Ollama or vLLM; Claude can sit behind the same gateway |

Backends are registered in `src/mixed_method_ontology/ocr/`; a new one implements `OcrBackend.recognize()`.

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
