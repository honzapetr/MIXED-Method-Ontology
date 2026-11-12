# Progress

> One entry per finished step, newest last: what was done, how it was verified, what the next session must know.

## T1 – 2026-11-06
- Done: repository rendered from the Project Lab template (`honzapetr/aiops-homelab`, `fabric/services/project-lab`,
  language python) and extended: `mmo` CLI (topics, source manifest, OCR with `tesseract` and OpenAI-compatible
  backends, CER comparison, segmentation), LinkML draft `ontology/schema/mmo.yaml` + `ontology/mapping.md`, method
  modules `methods/grounded-theory.yaml` and `methods/thematic-analysis.yaml`, skill `ingest-sources`, sample topic
  `topics/sample-masaryk-suicide`, brief, answers, spec, plan, ADRs 0002-0004.
- Verified: `uv run pytest` (27 passed), `ruff check`, `ruff format --check`, `tools/agents_sync.py --check`.
  OCR backends were tested with fakes only: no Tesseract binary and no homelab access in the cloud session.
- Next: T2 on the owner's computer – install `tesseract-ocr tesseract-ocr-ces`, fill `.env` from `.env.example`
  (gateway URL, key, a vision model), put sample scans into `topics/<topic>/sources/<id>/` and follow the
  `ingest-sources` skill. `.copier-answers.yml` was not kept (it pointed to a temporary path); the lab import adds
  what it needs. Project Lab requires the default branch `main`.

## T2a – 2026-11-12
- Done: OCR backend `fabric` (the homelab OCR service through the vendored `fabric-ocr` 0.2.0 wheel, ADR 0005),
  `--workers`, a failed page does not stop a run; `mmo ocr numbers` (printed page numbers read from the top and bottom
  edge of each photo through the service's Extract), `mmo ocr order` (printed / inferred / corrected / manual /
  unknown, gaps, duplicates), `mmo ocr book`; segments follow the reading order. Topic `nazi-v-dobe-ai`, source
  `kniha`: 213 phone photos (moved from `data/`).
- Verified: `uv run pytest` (43 passed), `ruff check`, `ruff format --check`. Live: all 213 pages read by dots.ocr
  (quality `full`, ~8.5 s per page with 2 workers); numbers: 200 of 213 pages placed (193 read, 5 inferred,
  2 corrected), 13 without a number.
- Found: dots.ocr leaves page headers and footers out of the text (only 15 of 213 page numbers were in it), hence the
  separate edge reading. The OCR service turned most upright pages before reading (its orientation question; fixed in
  the homelab 12. 11.) - the text was still read correctly.
- Next (owner): review `work/order/fabric/kniha.yaml` - numbers found twice (31, 51, 57, 63, 68, 99: a retake or a
  misread), the 13 pages without a number and the missing ranges (3-12, 14, 16-18, 52-54, 59-60, 84, 88, 105-106,
  124, 134-137, 148-155, 158-160, 196, 219 - some may be the unknown pages, some not photographed); set
  `printed_pages` in `source.yaml` and rerun `mmo ocr order` / `mmo ocr book`. Compare a few pages with the photos
  (`mmo ocr compare` with ground truth) before analysis.
