---
name: ingest-sources
description: Add a new source to a topic (primary material or supplementary context about another source), propose how to parse its files and run the ingest with the mmo CLI. Use when the owner brings new material (scans, photos, text, transcripts) for a topic or when files appear in topics/<slug>/sources/<id>/files/.
---
# Ingest sources of a topic

Layout and fields: `docs/spec.md`, section Topic folder (ADR 0006). Everything about a source is in
`topics/<slug>/sources/<id>/`: the researcher writes `source.yaml`, `notes.md` and puts originals into `files/`; the
machine writes `ingest/` (including the text of every variant, `ingest/text/`), `segments/` and `text.md`, the final
text the analysis reads (`mmo source finalize`, from the variant chosen in `text` of `source.yaml`). Never commit
page images; they are git-ignored.

1. **Create the source** (skip if it exists), then ask the owner to put the originals into `files/`:
   - primary material: `uv run mmo source add <slug> <id> --kind book --title "..." --language ces`
   - supplementary information about another source (a review, an interview with the author, a context
     document): `uv run mmo source add <slug> <id> --kind article --role context --about <source id>`
   Kinds: `book`, `interview`, `field-note`, `document`, `article`, `web`, `dataset`.
2. **Look at the files** in `files/` (type, count, size, naming) and propose a parsing plan to the owner; wait for
   approval before long runs:
   - **Text** (`.txt`, `.md`): taken as it is, no OCR (variant `original`).
   - **Page photos / scans:** the homelab OCR service is the default:
     `uv run mmo ingest <slug> <id> --backend fabric --workers 2` (reachable only from the owner's LAN or VPN; if
     it fails elsewhere, report `blocked`). It reads the text, the printed page numbers from the page edges, sorts
     the pages, writes `ingest/text/fabric.md` and the segments. To compare variants first, OCR a sample:
     `uv run mmo ocr run <slug> <id> --backend tesseract --scans 1-10` and the same with `--backend fabric`, ask the
     owner to correct 2-3 scans into `ground-truth/scan-NNNN.txt`, then `uv run mmo ocr compare <slug> <id>`.
   - **Other formats** (PDF with a text layer, EPUB, DOCX, audio, CSV): not supported yet - propose a task for
     `docs/plan.md` instead of improvising a parser.
3. **Run** `uv run mmo ingest <slug> <id> [--backend ...]`. It is resumable: after an interruption run it again.
   It ends with what to review.
4. **Reading order** (page images): go through `ingest/order/<variant>.yaml` with the owner - pages without a
   number, numbers found twice, missing pages. Fixes go to `printed_pages: {<file>: <page>}` in `source.yaml`; then
   run `mmo ingest` again (no OCR is repeated).
5. **Metadata:** `uv run mmo source check <slug> <id>` lists what the source lacks (citation, attributes,
   research questions, `about`, the memo in `notes.md`). Ask the owner for it - it is research knowledge, do not
   invent it.
6. **Final text:** when a variant is good enough, the owner chooses it (`text: {variant: <variant>}` in
   `source.yaml`) and `uv run mmo source finalize <slug> <id>` writes `text.md`. Reading photos with a Claude model,
   or adding pages later: skill `transcribe-pages`.
7. **Spot-check** 3 random segments in `segments/<variant>.jsonl` against the originals (scan, page, quote) and
   record the result, the variant and its model in `docs/progress.md`.

Settings come from `.env` or the OCR client's config file (`docs/source-preparation.md`, section OCR through the homelab). Never read
or print `.env`.
