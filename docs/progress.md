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
- Next session must know: the OCR setup on Windows (uv >= 0.13, `UV_PROJECT_ENVIRONMENT` off `G:`, token from
  `~/.config/fabric-ocr/env`) and the known gap of the `ingest-sources` skill are in README, section "OCR through the
  homelab". The branch `task/T2a-fabric-ocr-reading-order` is local only: the owner pushes it from this project.

## T2b – 2026-11-12
- Done: the program moved from `src/mixed_method_ontology/` to `code/mmo/` (`git mv`, history kept; ADR 0007):
  `core/topic.py`; `ingest/ocr/`, `ingest/page_numbers.py`, `ingest/order.py`, `ingest/segment.py`,
  `ingest/compare.py` (was `metrics.py`). Package `mmo`, command `mmo` unchanged. Tests split into `tests/core/` and
  `tests/ingest/`. `pyproject.toml` (hatch package path, ruff `src`), `Dockerfile`, README, spec and `AGENTS.md`
  (protected, approved by the owner in the plan) name the new path. The empty `data/` folder was removed.
- Verified: `uv run pytest` (43 passed), `ruff check`, `ruff format --check`, `uv run mmo --help`. The Docker image
  was not built (no Docker run on the owner's computer in this session).
- Next: T2c (source-centric topic layout). Planning of T2b-T2d is in the same branch (docs commits before T2b).

## T2c – 2026-11-12
- Done: source-centric topic layout (ADR 0006). Paths come from `Source` (`files/`, `ingest/`, `text/`,
  `segments/`, `ground-truth/`); `source.yaml` keeps only researcher fields, image hashes are in
  `ingest/files.yaml`; `topic.yaml` lists its sources. OCR records use `scan` (`scan-NNNN.json`), segment ids
  `<source>:s<scan>:<n>` and segments carry the printed `page` for quoting; old `page` records still load.
  `--scans` replaces `--pages` (kept as an alias). New `mmo topic migrate`; commands refuse an old-layout topic and
  say how to migrate. Both topics migrated; the 213 photos of `kniha` moved to `files/` on the owner's disk.
- Verified: `uv run pytest` (47 passed), `ruff check`, `ruff format --check`. `mmo ocr order` / `mmo ocr book` rerun
  after the migration: the order report and the whole text are identical to the ones before (ignoring line ends).
- Found: Google Drive keeps just-emptied folders (`topics/nazi-v-dobe-ai/work/ocr/fabric`, `.../order/fabric`)
  as undeletable ghosts for a while; git ignores empty folders and the migration check ignores them. Delete
  `topics/nazi-v-dobe-ai/work/` by hand once Drive lets go.
- Next: T2d (one-step source ingest, context sources, `ingest-sources` skill).

## T2d – 2026-11-12
- Done: `mmo source add` (creates `source.yaml`, `notes.md`, `files/`, lists the source in `topic.yaml`; `--role
  context --about <id>` for supplementary material, validated), `mmo ingest` (`code/mmo/ingest/pipeline.py`: file
  hashes, OCR, page numbers with `--backend fabric`, reading order, text, segments; resumable; ends with what to
  review), text files (`.txt`, `.md`) taken without OCR as the variant `original` (numbered apart from images, redone
  only when changed), `mmo source check` (`code/mmo/core/check.py`: citation, attributes, questions, `about`,
  memo, files, ingest, reading-order problems). Skill `ingest-sources` rewritten for this workflow incl. `fabric`
  (protected path, approved in the plan; `.claude/` copy regenerated). README quick start and spec updated.
- Verified: `uv run pytest` (57 passed), `ruff check`, `ruff format --check`, `python3 tools/agents_sync.py --check`.
  `mmo source check nazi-v-dobe-ai` on the real book lists: citation, attributes, questions, memo, 13 pages without
  a number and 6 numbers twice. `mmo ingest` was not run on the real book against the homelab (nothing new to read).
- Next (owner): fill in `topics/nazi-v-dobe-ai/sources/kniha/source.yaml` (citation, attributes, questions),
  `notes.md` and the research questions in `topic.yaml`; review the reading order. Small leftovers outside this
  task's paths: the sample source `masaryk-sebevrazda/source.yaml` still uses `creator`/`published` instead of
  `citation` and its note says to put scans next to the file; `AGENTS.md` lists the CLI commands of T1 only.
  The README still shows the OCR client's token name (`cli-vlastnik`) - asked the owner whether to remove it.

## T2e – 2026-11-13
- Done: `code/mmo/ingest/clean.py` and `mmo ocr clean` (rules `clean-v1`: separator lines, runs of number-only lines,
  a long line repeated within a page, a phrase repeated within a line; every removed or shortened line kept in
  `cleaning.removed` of the record; loops marked in `cleaning.stuck`; `--fallback W` takes the text of every scan that
  variant `W` has). `mmo ocr import` stores `scan-NNNN.txt` transcriptions as an OCR variant with image hash, model,
  prompt version and time. `mmo source check` lists stuck pages without a new reading.
- Book `kniha`: 37 of 213 scans had looped or stopped early in `fabric` (counting columns, a line repeated up to 108
  times, a phrase up to 180 times). The OCR service was unavailable, so the owner approved reading them with a cloud
  model: variant `claude` (`claude-opus-5-5`, prompt `ingest/ocr/claude/PROMPT-reread-v1.md`), no unreadable word.
  `fabric-clean` = `fabric` cleaned + those 37 pages: 4814 lines removed or shortened, text 620 kB -> 445 kB, 15090
  -> 5862 lines; `text/fabric-clean.md` and `ingest/order/fabric-clean.yaml` built. `fabric` is unchanged.
- Verified: `uv run pytest` (66 passed), `ruff check`, `ruff format --check`, `mmo ocr clean ... --fallback claude`
  (213 scans, 37 replaced, none stuck left), `mmo source check` (no stuck OCR).
- Found: the photos are stored upright; `fabric` reports "rotated 90/180/270 degrees" for 144 of them, which does not
  match the stored pixels - possibly why some pages looped (not tested). Scan 38 (`IMG_20260902_200508.jpg`) reads as
  page 53 on the photo, page 53 is missing and page 63 is counted twice - likely a misread number.
- Left: running headers ("NAZÍ V AI DOBĚ", chapter titles) and page numbers are still in the text (needed for the
  order; dropping them from segments is T3). Closing quotes: `"` on scans 96, 122, 125, `“` elsewhere in `claude`.
  The 13 pages without a number and 6 duplicates of the reading order are unchanged (owner review).
