---
name: ingest-sources
description: Inspect the files of a topic's source, propose how to parse them (OCR variants, segmentation) and run the agreed steps with the mmo CLI. Use when new source files (scans, PDFs, transcripts, CSV) appear in topics/<slug>/sources/.
---
# Ingest sources of a topic

1. Read `topics/<slug>/topic.yaml` and `sources/<id>/source.yaml`. List the files of the source (type, count, size,
   naming). Never commit page images; they are git-ignored.
2. Run `uv run mmo source scan <slug> <id>` so `source.yaml` records every page image with its hash.
3. Propose a parsing plan to the owner and wait for approval before long or paid runs:
   - **Scans / photos:** OCR a sample first (5-10 typical pages incl. a difficult one) with at least two variants,
     e.g. `uv run mmo ocr run <slug> <id> --backend tesseract --pages 1-10` and
     `uv run mmo ocr run <slug> <id> --backend openai --model <vision model> --pages 1-10`.
     Ask the owner to correct 2-3 pages into `ground-truth/<id>/page-NNNN.txt`, then
     `uv run mmo ocr compare <slug> <id>` and recommend a variant by CER, speed and cost.
   - **Other formats** (PDF with text layer, EPUB, DOCX, transcripts, CSV): not supported yet - propose the task
     for `docs/plan.md` instead of improvising a parser.
4. Run the chosen variant on all pages, then `uv run mmo segment <slug> <id> --variant <variant>`.
5. Spot-check 3 random segments against the scans (page, paragraph, quote) and record the result, the chosen
   variant and its model in `docs/progress.md`.

Local models go through the OpenAI-compatible endpoint from `.env` (`MMO_OPENAI_BASE_URL`); the GPU server may need
to be switched on first (homelab: fabricd). Never read or print `.env`.
