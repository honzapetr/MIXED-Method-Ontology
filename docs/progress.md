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

## T2f – 2026-11-13
- Model test (7 scans, 5 with an Opus reading as reference, `scratch/T2f/model-test/`): character error rate
  `claude-haiku-5-5` 0.68 % (left out a phrase, replaced words silently), `claude-sonnet-5-5` 0.04 %. Owner chose
  Sonnet and approved the cloud model for the whole book. About 7 000 tokens per scan in batches of 10.
- Done: variant `sonnet` (176 scans, `claude-sonnet-5-5`, prompt `ingest/ocr/sonnet/PROMPT-read-v1.md`);
  `mmo ocr import` stores a first line `ROTATION: …` in `rotation` (16 photos sideways, 1 upside down);
  `mmo ocr merge` (variant `book` = `claude` 37 + `sonnet` 176, `merged_from` per page); in the reading order the
  number of an imported whole-page transcription goes before the edge number of `fabric` (10 edge numbers were
  wrong, e.g. 19 for 137); `printed_pages` in `source.yaml` for 4 photos (retakes of 29 and 134, pages 16 and 59).
  `text/book.md` built (441 kB, 11 `[?]`).
- Verified: `uv run pytest` (70 passed), `ruff check`, `ruff format --check`, `mmo ocr order … --variant book`
  (201 printed, 5 inferred, 2 corrected, 4 manual, 1 unknown = the cover).
- Missing from the photos: pages 1-14 (front matter and the start of the introduction: page 15 begins mid-sentence),
  148 (text breaks mid-sentence), 219 (notes/bibliography), anything after 235 (the bibliography goes on); 17-19,
  56, 84, 105-106, 124, 160, 196 fall between the end of a chapter's notes and a new chapter - probably blank or
  title pages, owner to check. Asked the owner for photos.
- Left: retakes (pages 29, 31, 134 twice) are both in `book` and its text - the analysis should use one of each.
  Pages to look at: 86 (footnote numbers 17-37 filled in from the sequence), 115, 117, 130, 131 (passages the
  model was unsure of), 23 (header "TANEC SLUNCÍ"). `fabric` orders were not rebuilt. One-off scripts kept in
  `scratch/T2f/` (`prep.py` images, `numbers.py` edge vs text numbers, `model-test/compare.py`).
- Follow-up (same day, owner's answers): pages 1-14, 17-19, 219 and the notes/sources pages 56, 84, 105-106, 124,
  160, 196 are lost; page 235 ends the book (recorded in `source.yaml`). Page 148 was there all along: in the model
  test the images of scans 114 and 128 were swapped by mistake and the test output was taken over, so `sonnet`
  scan 128 carried the text of page 134 - removed; the wrong `printed_pages` entry for it too. New `retakes` in
  `source.yaml` (second photo -> photo kept), left out of order, text and segments: pages 29 and 31. Variant
  `opus-check` (`claude-opus-5-5`, `PROMPT-check-v1.md`): page 148 transcribed, 7 scans corrected after checking
  crops of the photos (23, 66, 90, 115, 130, 181, 206); 86, 117, 131 confirmed. `book` = `opus-check` + `claude` +
  `sonnet`: 211 pages, 4 `[?]` left (a word under a finger on page 21, two blurred words on page 88, two cut-off
  page numbers whose value the order knows). Scripts: `scratch/T2g/` (`crops.py`, `fix.py`).

## T2g – 2026-11-13
- Owner's decision: the analysis starts with the incomplete text; OCR is a side task and must not mix with it. One
  final text per source, a separate skill for finishing the transcription.
- Done: `sources/<id>/text.md` is the final text, built by `mmo source finalize` from the variant named in
  `text: {variant: ...}` of `source.yaml`, with a header of what it lacks. Working variant texts moved to
  `ingest/text/` (`git mv`). `mmo source check` reports a missing choice or an unbuilt `text.md`. `mmo ocr images`
  replaces `scratch/T2f/prep.py`. New skill `transcribe-pages` (+ `read-v1.md`, the tested Sonnet instructions);
  `ingest-sources` points to the new paths and to it.
- `kniha/text.md`: variant `book`, 211 pages (printed 15-235), missing 1-14, 17-19, 56, 84, 105-106, 124, 160, 196,
  219; scan 213 (cover) without a number at the end; 6 `[?]` marks in 4 places; read by Opus 45 pages, Sonnet 166.
- Next: the analysis role should read `text.md` (and later segments of the final variant), not `ingest/`. Segments
  of `book` are not built yet: running headers and page numbers are still in the page text (T3). The cover (scan
  213) stays in `text.md` until the owner says otherwise.


## T7 – 2026-11-13
- Owner: OCR is a tool of the project, like any other; the instructions and the plan must not be built around it.
  Agents had read OCR as the main line because the brief's first-phase scope named it and most of the plan and
  progress were OCR tasks.
- Done: OCR detail moved from `docs/spec.md` (Ingest pipeline, OCR backends) and `README.md` (single steps, OCR
  through the homelab) to `docs/source-preparation.md`, unchanged; spec and README point there. Brief scope: the
  analysis environment is the current focus, source preparation listed under tools. AGENTS.md (owner approved): source preparation
  described as a tool, CLI line without `ocr`, "Nothing is final yet" without OCR. Plan: only the building of
  the analysis environment; OCR tasks T2-T3 removed (their record is here), a concrete analysis lives in its topic.
  T3 (running headers out of the segments of `kniha`) comes back as a new task when the analysis needs segments. Skill `ingest-sources` links the new doc.
  No code or data removed.
- Next: define with the owner how the qualitative analysis with AI works (approaches, connections, theme maps)
  before T4-T6 are specified; research questions of `nazi-v-dobe-ai` are still empty.

## T8 – 2026-11-13 (in progress)
- Owner: the environment is built by walking one study (SKAD on `nazi-v-dobe-ai`); we record and set up, we do not
  analyse yet. Theory and research questions are part of the process and tie back to the purpose of the study.
- Done: `docs/research-design.md` - how methods link purpose, questions and theory (Maxwell, GT, reflexive TA,
  SKAD, CDA, mixed methods), proposal for the environment, sources with links. `research_design` block in
  `methods/grounded-theory.yaml` and `methods/thematic-analysis.yaml`, required by `tests/test_ontology_and_methods.py`.
  Answers in `docs/answers.md`. Active GitHub account switched to `honzapetr` (owner's request); git user is still
  `Jan-dolphin`.
- Verified: `uv run pytest` (72 passed), `ruff check`, `ruff format --check`.
- Next: SKAD method module (`methods/skad.yaml`) after reading the OAPEN volume; purpose of the study with the owner
  while going through SKAD; AI role scenarios to test.
- Two lines kept apart (owner): building the environment (`docs/`, `methods/`, `ontology/`, `code/`) and the
  concrete analysis with its sources (`topics/<slug>/`). Information about the book and its context sources lives
  in the topic, not here.
- Topic renamed to the printed title: `nazi-v-dobe-ai` -> `nazi-v-ai-dobe`, "Nazí v AI době" (owner); `text.md`
  rebuilt (only the title changed). Older entries above keep the old name. Scripts in `scratch/T2f`, `scratch/T2g`
  still point to the old path.
- Book found on the web: `citation` and `attributes` in `kniha/source.yaml`; 7 context sources added with
  `mmo source add --role context --about kniha` (annotation, 3 reviews, debate report, launch announcement,
  catalogue record), each with URL and access date; pages not saved or read yet.
- First memo in the proposed format (`docs/research-design.md`, section Memos): `topics/nazi-v-ai-dobe/memos/`.

## T9 – 2026-11-14
- Done: methods as folders (ADR 0008): `methods/skad/` (new, the method of the first study), `grounded-theory/`,
  `thematic-analysis/`, each with `method.yaml` (now with `status` and `memos` per phase), `research-design.md`,
  `procedure.md`, `agent-rules.md`, `applications.md`, `sources.md`; `methods/_template/`; `methods/foundations.md`
  (shared overview). `docs/research-design.md` removed after its content went to `methods/foundations.md`, the
  method folders, `docs/spec.md` (Research design in a topic, planned) and `docs/environment/memos.md`.
  `docs/source-preparation.md` -> `docs/environment/`. New `docs/development.md` (two lines, what goes where),
  `docs/README.md`, `docs/owner-notes.md` (owner's notes, Czech; first note on programming habits vs. precision of
  methods). AGENTS.md (owner approved): work item 7, layout, precision rule, link. Skill `ingest-sources`: link.
  `tests/test_ontology_and_methods.py` split into `test_ontology.py` and `test_methods.py` (folders, documents,
  status, memo types). `topics/nazi-v-ai-dobe/topic.yaml`: `methods: [skad]`.
- Verified: `uv run pytest`, `ruff check`, `ruff format --check`, `python tools/agents_sync.py --check`.
- Next: read the SKAD volume (OAPEN) and correct `methods/skad/` where the summaries were wrong; framing of the
  study (purpose, questions) with the owner, going through SKAD phase 1.

## T10 – 2026-11-14
- Done: `methods/reflexivity.md` (positionality vs. reflexivity, forms, techniques, the model as a positioned
  analyst, differences by method, sources); `reflexivity.md` in `skad/`, `grounded-theory/`, `thematic-analysis/`
  and `_template/`; agent rules of each method: profile first, positionality memo, notes on triggers; SKAD
  procedure, framing: both analysts' positionality memos. `docs/environment/analysts/` (README with roles, where
  notes go, triggers for model and researcher, gate questions; templates; profile and journal of
  `claude-opus-5-5`). ADR 0009. AGENTS.md: reflexivity rule (owner asked for the instructions). Memos, development
  rules, docs map, spec (point 7) updated. Study: `memos/2026-11-14-position-claude-opus-5-5.md` (proposed, with
  expectations before reading) and `memos/2026-11-14-position-researcher.md` (questions only, for the owner).
- Verified: `uv run pytest`, `ruff check`, `ruff format --check`, `python tools/agents_sync.py --check`.
- Next: the owner writes their researcher profile and positionality memo; then the SKAD volume (OAPEN) and framing.
  Sources marked "general knowledge" in `methods/reflexivity.md` (incl. Finlay's five variants) are to be checked.

## T11 preparation – 2026-11-14
- Owner: the builder and analyst roles mix in one folder, and trying the analysis changes the environment. Approved
  preparing the split into two repositories (environment, study); both stay on Google Drive; analyst profiles and
  GitHub for the study later.
- Done: answer in `docs/answers.md`; ADR 0010 (proposed) with the sources found; T11 (`mmo study init`, simulated
  test study, sandbox) and T12 (move `nazi-v-ai-dobe` out) in `docs/plan.md`; journal note in the model's profile.
- Next: the owner confirms T11-T12, then T11 on branch `task/T11-study-split`.

## T11 – 2026-11-15
- Done: `mmo study init <path> --title --method` (`code/mmo/core/study.py`) creates a study next to the
  environment: topic files with `purpose`, `methods` and `environment` (relative path, commit, uncommitted
  changes), `AGENTS.md` for the analyst, `CLAUDE.md` importing it and the method's `agent-rules.md`, `feedback.md`,
  `pyproject.toml` (`mmo` as an editable path dependency, not a package), `.gitignore`, `git init`. It refuses a
  non-empty folder, a folder inside the environment and an unknown method. Every `mmo` topic argument also takes a
  path to a study or, inside a study, its own name (`.` works). Simulated study `tests/fixtures/mini-studie/`
  (invented material), `tests/core/test_study.py`. `docs/environment/studies.md`; ADR 0010 accepted.
- Found: uv resolves a relative flat index against the folder it runs in, also for a path dependency and for
  `uv run --project` (uv 0.6.8 and 0.13.8), so a study could not install `fabric-ocr`. Owner approved pinning the
  wheel by file path (`pyproject.toml`, `uv.lock`, `vendor/wheels/README.md`, ADR 0005 amendment); the lock no
  longer holds an absolute `file:///G:/...` path. uv 0.6.8 now syncs the environment as well.
- Sandbox `../studie/piskoviste/` made with `mmo study init`, synced and tried (source add, ingest, check); not in
  git of the environment, nothing committed in it.
- Verified: `uv run pytest` (86 passed), `ruff check`, `ruff format --check`.
- Next: T12 – move `nazi-v-ai-dobe` out with `mmo study init` and `git subtree split`, delete
  `sample-masaryk-suicide`, update references to `topics/` (protected paths need approval). A study's `.venv` is on
  Google Drive (slow to create); `UV_PROJECT_ENVIRONMENT` must not be one folder shared by the environment and a
  study. `scratch/T11/` (copy used to test the wheel pin) can be deleted.

## T11 review – 2026-11-15 (owner's correction, session ended)
- The owner wanted **workshop vs. research environment** (`docs/answers.md`, 2026-11-15), not environment vs. one
  study. T11 built `mmo study init` (one study = one repository) and ADR 0010 on the wrong reading.
- Keep from T11: simulated test study `tests/fixtures/mini-studie/`, the `fabric-ocr` wheel pinned by path, `mmo`
  topic argument accepting a path. Review: `mmo study init`, `docs/environment/studies.md`, ADR 0010 (mark
  superseded by a new ADR), sandbox `../studie/piskoviste/` (can be deleted).
- Next session: get answers to the two open questions, then write a new ADR and plan the split (workshop /
  research environment) with the owner; restate the structure in the owner's words before planning.
- GitHub account for pushing not chosen yet; nothing pushed.

## T12 – 2026-11-15
- Owner answered the open questions: `mmo` belongs to the workshop; studies live inside the research environment;
  test environments stay, without git; roles must not stack through the folder tree; methods and ontology belong to
  the research environment (the analyst needs them), changes to them are agreed with the builder in the workshop.
  Workshop keeps the folder name, research environment `vyzkum/` with a fresh history; GitHub account `honzapetr`.
- Done: ADR 0011 (layout of files of the workshop, `vyzkum/` and `zkusebna/`), ADR 0010 superseded, answer in
  `docs/answers.md`, T12-T16 in `docs/plan.md` (replacing the old T12).
- Next: T13 (test environments, remove `mmo study init`) on branch `task/T13-test-environments`. Sandbox
  `../studie/piskoviste/` and `scratch/T11/` can be deleted in T13.
- Owner changed the names: workshop `MIXED-Method-Ontology-vyvoj/` (renamed, keeps history), research environment
  `MIXED-Method-Ontology/` (new). Split first: T13 rename, T14 create the research environment, T15 clean the
  workshop; test environments and releasing `mmo` later. ADR 0011 rewritten with the file layout table; the owner
  will correct it.

## T13 – 2026-11-15
- The owner made `2026/MIXED-Method-Ontology/MIXED-Method-Ontology-vyvoj/`; the whole repository (with `.git`,
  git-ignored page images and `scratch/`) moved there from `MIXED-Method-Ontology/`; `.venv` and caches recreated,
  not moved. Claude Code's memory moved to the new path's key; the old key keeps no memory, so the analyst in
  `MIXED-Method-Ontology/` starts empty.
- Verified in the new folder: `git status` clean, `git fsck` clean, `uv sync`, `uv run pytest` (86 passed).
- Next: start Claude Code in `MIXED-Method-Ontology-vyvoj/`; the owner corrects the file layout in ADR 0011, then
  T14 (create the research environment in `MIXED-Method-Ontology/`, which now holds only the old `.venv` and caches
  to delete).

## T14 – 2026-11-15
- Owner confirmed the file layout of ADR 0011 and the three open points (copy `tools/agents_sync.py` and
  `.claude/settings.json`, analyst profiles move whole); recorded in ADR 0011, `docs/answers.md`, T14 criteria.
- Correction of the T11 entries above: `scratch/T11/` did not exist; only the sandbox `../studie/` is to be deleted.
- Done: research environment `../MIXED-Method-Ontology/` (git, branch `main`, first commit `baac630`, names
  workshop commit `dfc4c6d`): `methods/`, `ontology/`, `analysts/`, `docs/` (memos, source preparation),
  `topics/README.md` and `topics/nazi-v-ai-dobe/`, skills `ingest-sources` and `transcribe-pages` (+ generated
  `.claude/skills/`), `tools/agents_sync.py`, `.claude/settings.json`; new `AGENTS.md` (analyst only, no reference
  to the workshop), `CLAUDE.md`, `README.md`, `pyproject.toml` (editable path dependency on the workshop, lock with
  a relative path). Paths of moved files rewritten; references to files that stay here (spec, plan, progress,
  owner's notes, ADRs, tests, code) replaced; records of source preparation now go to a `methodological` memo of
  the topic (provisional). Study memos and the model's journal left as they were (records). No `.env` there yet;
  the owner starts a new one. The workshop still holds all of it until T15.
- Verified: 213 page images match `ingest/files.yaml` (sha256); in the research environment `uv sync`,
  `uv run mmo source check nazi-v-ai-dobe` (exit 0, same output as in the workshop), `agents_sync.py --check`.
  Not yet: the owner starts Claude Code there and checks `/memory`.
- Next: the walk through the analysis continues in the research environment, in a new thread: the analysts'
  personal journals and own biases (researcher profile, positionality memos of `nazi-v-ai-dobe`). T15 (clean the
  workshop) after that check; nothing pushed yet (account `honzapetr`).

## T16 – 2026-11-15
- Owner asked whether the text on what shapes the model covers filters and training; it covered training data and
  post-training without sources, not filters or the hidden system prompt. Found: system card of Opus 5.5 (too large
  for fetch; downloaded and read in the session scratchpad, not kept), constitution, maker's posts on political
  bias and filters, Durmus et al. 2023, selective refusal bias. Owner chose the scalable way (`docs/answers.md`).
- Done in the research environment, branch `task/T16-model-profiles` (commit there): skill `profile-model`,
  template by layers with certainty marks and "What follows for the analysis", `AGENTS.md` (read your profile every
  session; without one run the skill), `analysts/README.md`, profile `claude-opus-5-5` rewritten (status
  `proposed`, journal kept, new entry), `methods/reflexivity.md` §2 and sources.
- Verified: `agents_sync.py --check` in the research environment.
- Next: the owner tests the first start in a test copy of the research environment: delete
  `analysts/claude-opus-5-5.md` in the copy (or start another model) so the skill is triggered; then confirms the
  profile. Branch to be merged into `main` there after the test. T15 still waits.

## 2026-11-15 – T17 test copies in `zkusebna/`

- `tools/new_test_env.py` (standard library; run with `python` from the workshop) makes `../zkusebna/test<N>/` or a
  named folder from `../MIXED-Method-Ontology/` as git sees it, including uncommitted changes; leaves out `.env`,
  `.venv/`, caches, `scratch/`, `.git/` and page images (`--with-source-files` adds them). `--without-profile <id>`
  simulates a model's first start; `--git` gives the copy its own repository; `--dry-run` lists the files. The
  workshop path in `pyproject.toml`/`uv.lock` is rewritten so `uv sync` works; each copy is logged in
  `zkusebna/_log.tsv` (outside the copy, so the analyst does not see it).
- Verify: `uv run pytest` 90 passed; ruff clean. Dry run on the real environment: 960 files (1173 with sources).
- By default the copy holds only what the agent reads; dotfiles other than `.agents/` and `.claude/`, `pyproject.toml`,
  `uv.lock` and `tools/` come with `--with-project-files` (owner: for testing the agent, versioning and setup are
  not needed now).
- Next: the owner runs the first-start test in `zkusebna/test2/` (`--without-profile claude-opus-5-5`).

## 2026-11-15 – T18 the analyst's role (research environment)

- Branch `task/T18-analyst-role` in `../MIXED-Method-Ontology/` (from `task/T16-model-profiles`), commit e810100 and a
  fix. Skill `frame-role`: profile (by `Version`) × method (`methods/<id>/reflexivity.md`, agent rules) × topic →
  role memo `topics/<slug>/memos/<date>-role-<model-id>.md`, written before the data are read, owner confirms;
  framed again on a new profile version or a change of the method's reflexivity. `AGENTS.md`: three steps every
  session (who am I, what do I work on, what is my role here) and "act from the role whenever you weigh
  information". Profile template and `profile-model`: Role (first person, 5–8 sentences) and Version. Role written
  in the profile of `claude-opus-5-5` (still `proposed`); `frame-role` requires a confirmed profile.
- The positionality memo of `nazi-v-ai-dobe` (2026-11-14) stays as history; the role memo will supersede it.
- First test (`zkusebna/test2/`, before T18): `profile-model` started on its own; the model also read the old
  positionality memo of the study, so it did not start from nothing.
- Next: the owner tests in a new copy; then confirms the Opus profile and the role for `nazi-v-ai-dobe` is framed.

## 2026-11-16 – T19 GitHub account asked when needed

- Test in `zkusebna/test3/` (T18): the first answer followed the three steps (model id from the harness, missing
  profile → `profile-model` proposed, one study, role memo missing → `frame-role` after the profile, no analytic
  step); it called the old positionality memo an inconsistency.
- `AGENTS.md` (workshop and research environment): no account names; the account is checked with `gh auth status`
  and confirmed by the owner only before the first push, pull request or `gh` command; git identity checked before
  the first commit. Branches `task/T19-github-account` in both repositories (research one from T18).
- The positionality memo `2026-11-14-position-claude-opus-5-5` of `nazi-v-ai-dobe` is deleted (owner); the role
  memo from `frame-role` will be the model's only position in the study. The researcher's positionality memo stays.
- Next: the owner tests in a new test copy; then T18 and T19 are merged in the research environment.

## 2026-11-16 – T20 analysts are the profile files

- Test in `zkusebna/test4/` (T19, without the Opus profile): no GitHub question at the start; `profile-model` ran,
  looked the model up on the web (system card, constitution, one independent sycophancy test), reported findings and
  asked for approval before writing, and for the owner's approval of a cloud model. Error: `analysts/README.md`
  listed `claude-opus-5-5.md (proposed 2026-11-15)` although the copy had no profile; the model also looked into the
  sibling copy `test3/` to find it (outside its folder).
- Fix in `../MIXED-Method-Ontology/`, branch `task/T20-analysts-from-files` (from T19): the hand-kept table is gone;
  the analysts are the files in `analysts/`, status and version in each profile; `profile-model` adds no row.
  `agents_sync --check` passes.
- Next: test copy with the Opus profile (still `proposed`) to try `frame-role`; the owner confirms the profile in
  the test.

## 2026-11-16 – T21 positions apart from memos

- Test in `zkusebna/test5/` (profile included): the model stayed in its folder and did the three steps; it still
  saw the profile's journal of building the environment.
- Research environment, branch `task/T21-positions` (from T20), commit 822b2f4: positions in
  `topics/<slug>/positions/`; `frame-role` → `state-position`; profile Role → Position; Opus profile without task
  references, journal empty, "Used for" research only; researcher's draft → `positions/owner.md`; `AGENTS.md` step 2
  says an undefined study is a discussion with the researcher. `agents_sync --check` passes; no leftovers of
  "role memo", `frame-role` or "positionality memo".
- Next: T22 (hooks); a new test copy with the profile.

## 2026-11-16 – T22 guards for the analyst

- Workshop: `mmo-guard` (`code/mmo/guard.py`, script in `pyproject.toml`): `session-start` gives only step 1 (model
  id when the harness passes it, its profile with status and version, `Guards: on`); `pre-tool-use` denies paths
  outside the environment (temp and the project's own `~/.claude/projects/<dir>` allowed), denies study data
  (`sources/<id>/text.md`, `segments/`, `ingest/`, `files/`, `ground-truth/`, `work/`) and content searches over
  them until a model has a confirmed profile and a confirmed position from the current profile version, and asks
  the owner when a profile or a position becomes `confirmed`. Bash checks are heuristics on the command line.
  `tools/new_test_env.py`: project files and `uv sync` by default. `uv run pytest` 101 passed; ruff clean.
- Research environment, branch `task/T22-guards` (from T21): hooks in `.claude/settings.json`; `AGENTS.md` says
  what `Guards: on` means and that without it no analytic step is done. Run end to end there: the book text denied
  (profile proposed), `../zkusebna/test3` denied, the profile allowed; about 1 s per guarded call.
- Unknown until tested in a session: whether the harness passes the model id to SessionStart (if not, the hook
  lists the profiles and the model takes its id from the harness); whether an `ask` decision prompts in auto mode.
- The research environment needs `uv sync` once to install `mmo-guard`.
- Fix after the test in `zkusebna/test7/`: `2>/dev/null` was read as the path `G:\dev\null` and the whole command
  denied; shell devices (`/dev/...`, `nul`) are skipped and Git Bash `/tmp` maps to the temp folder; test added.

## 2026-11-17 – T23 Input documents of a study out of git
- Research environment: `topics/.gitignore` lists `nazi-v-ai-dobe/sources/`; 895 files left the index (`git rm
  --cached`) and stay on disk; `topic.yaml`, `positions/`, `memos/` stay in git; rule in `topics/README.md`. The
  sources are still in the earlier commits (nothing pushed); they now need a backup of their own (the shared drive).
- `tools/new_test_env.py` also copies untracked files under `topics/` ignored only by `topics/.gitignore`; the root
  rules (scans) still apply; test added. 102 passed, ruff clean.

## 2026-11-17 – T24 The final text as the contract; segments of text.md; quotations
- Owner: the OCR work was meant to get the book's text, not to fix the input of the analysis; now decided
  (`docs/answers.md`, ADR 0012): every source ends as the same `text.md` (converted by the program, no AI, OCR only
  without a text layer); segments are paragraphs of `text.md`; the analysis points to quotations (exact words +
  offsets in `text.md` + pages; not "anchor", which collides with Mayring).
- Code: `segment.py` cuts `text.md` (location comments, paragraphs, offsets into `text.md`, `text` = exact slice,
  `continues`); `mmo source finalize` writes `text.md` (hyphenation joined, `\n` line ends) and
  `sources/<id>/segments.jsonl`; `mmo ingest` no longer segments and asks to choose the variant; `mmo segment` takes
  no variant; `mmo source check` reports missing or stale segments; `mmo topic migrate` drops old segments; the guard
  gates `segments.jsonl`. Tests rewritten for the new behaviour; 104 passed, ruff clean.
- Docs: `docs/source-pipeline.md` (all steps built / planned, the `text.md` format, segments, planned quotations,
  walk-throughs for photos, PDF and web pages); ADR 0012; spec, README, `AGENTS.md` (traceability to quotations);
  plan: T24 and a new Analysis section T25-T31 replacing T4-T6.
- Research environment, branch `task/T24-text-quotations`: `AGENTS.md`, `docs/source-preparation.md` (section on the
  final text, segments and quotations), `docs/memos.md`, skill `ingest-sources` (+ `.claude/`), method texts
  (evidence segments -> quotations in SKAD, GT, TA; GT's own "segments" and the units a model reads kept), ontology
  `Quotation` (also copied to the workshop's copy, which the ontology test reads until T15).
- Tried on a copy of `kniha/text.md` (not rebuilt): 1,581 segments over 211 pages, all exact slices; 208 continue
  over a page break; 478 shorter than 40 characters - running heads (`NAZÍ V AI DOBĚ` 89x, chapter titles) and lone
  page numbers, which also stand before the first paragraph of a page -> T25. Script kept:
  `scratch/T24/try_segments.py <text.md>`.
- Not done: `kniha/text.md` and its segments are not rebuilt in the research environment (the owner decides,
  best after T25); the workshop's stale copies of `methods/` and `docs/environment/` are left for T15.
- Next: owner's review of both branches; open decision on who drives the analysis (agent / `mmo` with the gateway /
  both); then T25 (page furniture) or T26 (quotations).

## 2026-11-17 – T25 Page furniture out of the final text
- Owner approved T24 (protected paths included) and decided that both an agent and `mmo` drive the analysis
  (`docs/answers.md`).
- Probe of the variant `book` of `kniha`: the running head is the first line of a page (103x the book's title on odd
  pages, chapter titles on even pages), the printed number the last line (201 pages); the variant `fabric` hardly
  has them (the OCR service leaves headers and footers out). Chapter openings start with `KAPITOLA II.` and a
  `## …` heading, which occur once.
- Built: `code/mmo/ingest/furniture.py` - a page number is a first or last line equal to the page's printed number;
  a running head is a first line (not a heading, <= 80 characters) opening >= 3 pages, or nearly the same (>= 0.9,
  `TANEC SLUNCÍ`). `finalize` leaves them out of photo pages only, writes `ingest/furniture/<variant>.yaml` and the
  header field `left_out`; the note of `text.md` says so. Tests `tests/ingest/test_furniture.py` with samples from
  `kniha`; pipeline tests updated (page numbers are no longer segments). 112 passed, ruff clean.
- Tried on a copy (`scratch/T25/`): 203 running heads, 200 page numbers left out; segments 1,581 -> 1,240; shorter
  than 40 characters 478 -> 140 (headings, footnotes, `[?]`); "continues" 208 -> 131. Bibliography page 219 missing
  among the photos, so the bibliography has no heading.
- Docs: `docs/source-pipeline.md` step 4 and header; research environment `docs/source-preparation.md` (branch
  `task/T25-page-furniture`).
- Not done: `kniha/text.md` in the research environment not rebuilt - waits for the owner. Footnotes and the one
  reader's note `[note: …]` stay in the text.
- Next: rebuild `kniha` (owner), then T26 (quotations).
- 2026-11-17, owner approved: `kniha/text.md` rebuilt in the research environment with `mmo source finalize`
  (`left_out`: 203 running heads, 200 page numbers; 1,240 segments, all exact slices; `mmo source check` reports
  nothing about the final text or segments). The previous `text.md` is kept in
  `scratch/T25/kniha-text-before-T25.md` (sources are out of git since T23).

## 2026-11-17 – T25a Carrying the study work between test copies
- Owner: the framing done in `zkusebna/test7` (questions, positions of the owner and the model, memos, confirmed
  profile) should go on in the next copy on the new environment, and the work should keep growing copy by copy.
- `tools/new_test_env.py --carry <copy> [--on-conflict copy|env]`: compares the earlier copy (blob ids, line ends
  normalised) with the environment commit recorded for it in `_log.tsv`; carries the study state it created,
  changed or deleted; lists environment files it changed (feedback, not carried); stops on conflicts; warns when a
  position no longer matches the profile version; with `--git` a second commit "study work carried from …".
  Tests: carrying, deleting, growing over three copies, conflicts both ways, version warning. 117 passed, ruff clean.
- Made `zkusebna/test8` from the research environment `task/T25-page-furniture` 37c1bb2 with `--carry test7 --git`:
  6 files carried (`topic.yaml`, both positions, two memos of 2026-11-17, the confirmed profile), no conflicts, no
  environment changes in test7; the guard opens `nazi-v-ai-dobe` to `claude-opus-5-5`; `text.md` is the rebuilt one
  (1,240 segments).
- Docs: `docs/test-copies.md` (making copies, `--carry`, growing over time, from a test to the research).
- Next: the owner continues the study in `test8`; T26 (quotations).

## 2026-11-19 – T25b Design of the analytic layer (ADR 0013)
- Owner: the analysis must stay free; the first proposal (a method-enforcing engine: unknown code types refused,
  phase gates) mixed integrity with framing and was dropped.
- ADR 0013: a fixed core of integrity, a free toolbox of qualitative operations, the method as orientation
  (`model_role` binds models only), strictness per study in `topic.yaml`; text files in `analysis/` as the source of
  truth, graph, graph browser and REFI-QDA export as views.
- `AGENTS.md` of both repositories: traceability rule made precise, rule "the analysis is free" added (approved).
- Plan: Analysis rewritten - T32 store and toolbox, T33 method as orientation and study settings, T29 proposals of
  models, T36 outline and orientation reading (key for passages open), T34 REFI-QDA export, T30 graph, T35 graph
  browser, T31 model backends. Order: T26, T32, T33, T29, T36, T34, T30, T35, T31.
- Owner decided T36: structural start searched by the research questions, then reception and contrast; the model reads the whole book first as impressions; the researcher's reading is never a condition for the model's.
- Next: T26 (quotations).

## T26 – 2026-11-19
- Done: `code/mmo/analysis/quote.py` and `mmo quote find <topic> <source> "<words>" [--page n | --segment id]
  [--format yaml|json]`, `mmo quote check <topic> [--update]`. Words are compared on a view of `text.md` (location
  comments left out, whitespace as one space; header and title not searchable); refused when not found or found more
  than once without a hint. The record carries `source, start, end, pages, scans, exact, prefix, suffix,
  text_sha256`; `check` reads YAML/JSON/JSONL and Markdown front matter of a study (not `sources/`, `work/`,
  `topic.yaml`), reports ok / moved / gone / ambiguous / no text, `--update` stores the new place of moved ones.
  Ontology `Quotation` slots aligned (both copies). Guard: `mmo quote` on a study is denied to a model exactly when
  reading its `text.md` is. `mmo` prints UTF-8 (the Windows console garbled Czech). Docs: `docs/source-pipeline.md`
  step 7, research environment `docs/source-preparation.md`.
- Tried on `kniha`: "My Američané jsme zvláštní, vyvolený národ" -> page 57, scan 41, 3.5 s; "AI" refused (630
  times, pages listed).
- Verified: `uv run pytest` – 125 passed; `uv run ruff check . && uv run ruff format --check .` clean.
- Next: T32 (analysis store and the free toolbox) - its layout decides where quotations live; `mmo quote check`
  already finds them in any YAML/JSON there. `AGENTS.md` CLI lines do not list `quote` yet (protected path).

## 2026-11-19 – Plan: T37 similarity index, T38 graph procedures
- Owner approved: T37 (embeddings of segments as a finder of candidates, after T29) and T38 (graph procedures over
  the confirmed analysis, after T30); classic RAG not used for interpretation. Order in the plan's Analysis note.
- T26 merged (PR #2, b55a4a6); research environment `main` moved without a checkout (b27eb43).
- Git on Google Drive: a stale `.git/index.lock` and index entries with a wrong size (16384 instead of the file's
  size) made identical files look modified; fixed by removing the stale lock and `git add` of the identical files.
- Next: T32 (analysis store and the free toolbox).

## T25c – 2026-11-19 – The plan checked as a whole
- Found and resolved contradictions with ADR 0013: phase gates and the graph as files of record in `docs/spec.md`,
  three vocabularies of proposal statuses, memos in `analysis/`, "gates" in the method texts; gaps: setting the phase
  (`mmo phase`, T33), machine indexes in git and `--carry` (T30, T37), hand edits (T32), offsets in the REFI-QDA
  export (T34).
- Workshop: `docs/spec.md` (concepts, topic folder, analysis and graph, human steering), ADR 0013 amendment, plan,
  ontology `ProposalStatus` (both copies). Research environment: `researcher_decides` in every `method.yaml`,
  "Researcher decides:" in the procedures, "decision of the researcher" in the reflexivity texts, analysts' README
  and template, skill `state-position` (synced); the confirmed profile of `claude-opus-5-5` is left as it is, a note
  in `methods/reflexivity.md` explains the old word.
- Next: T15 (clean the workshop; `tests/test_methods.py` then reads the research environment and its
  `researcher_decides`), then T32.

## T15 – 2026-11-19
- Done: the workshop holds no research. Removed `methods/`, `ontology/`, `topics/`, `docs/environment/` and the
  analyst skills `ingest-sources`, `transcribe-pages` (all in the research environment; the workshop-only sample
  topic `sample-masaryk-suicide` and two old position memos stay in git history). Untracked leftovers of `topics/`
  (all present in the research environment) and the empty sandbox `../studie/` moved to `scratch/T15/`, not
  deleted - can go when the owner agrees. `mmo study init` and `code/mmo/core/study.py` removed; the tests of the
  topic argument as a path kept (`tests/core/test_study_folder.py`, fixture `mini-studie`). `tests/test_methods.py`
  (now `researcher_decides`) and `tests/test_ontology.py` read `../MIXED-Method-Ontology/` and skip without it.
  Rewritten for the builder: `AGENTS.md` (two repositories, layout here, CLI with `quote`), `README.md`,
  `docs/README.md`, `docs/development.md`, `docs/spec.md` (layout), link in `docs/brief.md`. `CLAUDE.md` needed no
  change.
- Verified: `uv run pytest` – 119 passed; `uv run ruff check . && uv run ruff format --check .` clean;
  `python tools/agents_sync.py --check` clean.
- Next: merge T25c + T15 (both repositories), then T32.

## T32 – 2026-11-19
- Done: the analysis store `topics/<slug>/analysis/` (`codebook.yaml`, `codings.jsonl`, `relations.yaml`,
  `history.jsonl` with the files' state after every operation; field names = ontology slots) and the free toolbox:
  `mmo code add|apply|rename|merge|split|recode|withdraw|list`, `mmo relation add`, `mmo memo add` (memos stay in
  `memos/`, format of `docs/memos.md`), `mmo analysis check [--record --by]` (authors, references, quotations, edits
  by hand). Only integrity is refused: words not in `text.md`, no author, a model without `--prompt-version`, a
  reference to nothing. A model's record is `proposed`, the researcher's `accepted`; nothing is deleted (superseded,
  withdrawn). `--quote`/`--evidence` take `<source>@<page>`. `mmo quote check --update` records itself so it is not
  taken for a hand edit. Guard: a model writes `analysis/` only through `mmo` (Write/Edit and shell writes denied),
  only under its own id; `mmo quote|code|relation|memo|analysis` closed like `text.md`. Ontology: status
  `withdrawn`, slot `method`.
- Tried on a copy of `kniha` in `scratch/T32/env`: codings on p. 57 and 77, a relation, a model's memo with a
  quotation on p. 57 ("vyvolený národ" occurs 3 times - refused without the page); checks clean.
- Verified: `uv run pytest` – 128 passed; `uv run ruff check . && uv run ruff format --check .` clean.
- Waiting for the owner: the research environment's `AGENTS.md` (protected) should list the new commands and
  `docs/analysis.md`; the change was blocked without approval. Same for the workshop's `AGENTS.md` CLI line.
- Next: T33 (method as orientation, `mmo phase`, study settings).

## T33 – 2026-11-19
- Done: the method as orientation. `mmo method check` (schema of `method.yaml`: version, phases with
  `researcher_decides`, known memo types, relations among `relation_types`, optional versioned `prompt` per phase);
  SKAD, GT, TA and the template pass, each now has `version: "2026-11-19"`. Study settings `analysis:` in
  `topic.yaml` with free defaults (codebook, own_types, phases, model.phases/alternatives, team,
  quotation_required.memos); what a study asks for is kept by the toolbox (fixed codebook, sequence of phases, models
  only in some phases, quotations in some memo types, reminders on own types). `mmo phase` (the researcher only,
  per method, recorded in the history; denied to a model by `mmo` and the guard), `mmo status` (map of phases, where
  the study is, model role and researcher's decisions there, what was made, proposals waiting, reminders). Several
  methods in one study; tests with a toy method.
- Tried on the research environment: `mmo method check` - 4 ok; `mmo status nazi-v-ai-dobe` - SKAD's 7 phases, no
  phase set yet, 1 proposal waiting (the model's first-impression memo of 2026-11-13).
- Verified: `uv run pytest` – 140 passed; `uv run ruff check . && uv run ruff format --check .` clean.
- Next: T29 (proposals of models and their review); the owner sets the phase of the study (`mmo phase`).

## T29 – 2026-11-19
- Done: proposals of models and the researcher's review. A proposal is a record of the toolbox with
  `status: proposed`, decided in place by `mmo review accept|edit|reject` (edit keeps old and new values, reject
  needs a reason; `decided` on the record, `review` in the history; cascades: a coding takes its proposed code, a
  rejected code its proposed codings). Only a person decides (mmo and guard). What a model may propose follows
  `model_proposes` of the current phase (new optional field of `method.yaml`; SKAD filled from its `model_role`,
  version `2026-11-19.2`); codebook changes are the researcher's; a model withdraws only its own waiting proposals;
  `analysis.model.alternatives` asks a model's analytic memo for `--alternative`.
- Decision to note for the owner: no `analysis/proposals/` folder as the plan said - proposals stay in the same
  files with their status, so an accepted proposal is the same record with its provenance.
- Docs: `docs/analysis-store.md`; research environment `docs/how-it-works.md` (the whole way through, linked from
  its README), `docs/analysis.md` (review), `methods/README.md` (`model_proposes`).
- Tried on a copy of `kniha` with SKAD (`scratch/T29/env`): a model's coding refused in framing, proposed in fine
  analysis (p. 57), a memo with an alternative reading; accepted (with its code) and a memo marked edited; status
  shows 0 waiting.
- Verified: `uv run pytest` – 148 passed; `uv run ruff check . && uv run ruff format --check .` clean.
- Next: a new test copy from the start (owner); then T36 (outline and orientation reading).

## 2026-11-19 – Test 9 made; plan brought up to date
- T29 merged (PR #6; workshop 873d1e4, research environment `main` cde59c7).
- `zkusebna/test9` made with `python tools/new_test_env.py test9 --git` from the research environment `main`
  cde59c7, without `--carry` (from the start): 966 files, `uv sync` done, git commit eedb2b3. Checked in the copy:
  `Guards: on`, `kniha/text.md` the rebuilt one (`left_out` 203/200, 1,240 segments), `mmo method check` 4 ok,
  `mmo status nazi-v-ai-dobe`: SKAD 2026-11-19.2, no phase set, 1 proposal waiting (the model's first-impression
  memo of 2026-11-13), the researcher's position `positions/owner.md`, the profile `analysts/claude-opus-5-5.md`
  present (a model's first start would need `--without-profile claude-opus-5-5`).
- Plan: section "Where we are" (what is built, test 9 and what it should walk, the order after it); new tasks T39
  (prompts per phase, versioned), T40 (`model_proposes` for GT and TA), T41 (clean scratch folders).
  `docs/test-copies.md` records test 9.
- Next: the owner walks test 9; findings become tasks; then T39, T36, T28, ... as in the plan.

## T42 – 2026-11-24
- Test 9 walked by the owner (2026-11-23/24): `nazi-v-ai-dobe` from position to the final report in `zkusebna/test9`
  with claude-opus-5-5, gemini-4-neon as a critic through the Antigravity CLI. The copy's `.git/index` was missing
  (a stale `index.lock` of 2026-11-19 on Google Drive); removed and the index rebuilt from HEAD, files unchanged.
- Record in `scratch/test9/` (kept for later analysis): `session-2026-11-23.jsonl` (Claude's session, copied
  2026-11-24 14:49) and `.md` transcript (`to_md.py`); `gemini/` with the Antigravity conversation database, its
  `history.jsonl` and a decoded `conversation.md` (`gemini_to_md.py`, protobuf strings, raw).
- Findings: context 540k tokens, two thirds `text.md` of the book; a compaction right after the whole-book reading;
  closed loop of the model's own map (missed chapters, S6 overstated, S7 missed); the critic corrected 4 of 6 places
  with text the lead had not read; the critic's instructions were written by the model it criticised, it ran without
  the guard and outside the record; the corpus grew only on the owner's push.
- Done: ADR 0014 (lead analyst, subagents, critic of another maker through `agy`), ADR 0015 (context search by the
  method and the questions); spec sections "Analysts and roles", "Context search"; plan: test 9 recorded, T42-T47
  and test 10, T39 extended to roles, T36 to coverage, T31 narrowed; owner's decisions in `docs/answers.md`; the
  owner's two notes of 2026-11-23 in `docs/owner-notes.md`.
- `agy` (Antigravity CLI) can run in print mode (`-p`, `--model`, `--output-format stream-json`, `--sandbox`,
  `--settings`); whether it runs hooks for the guard is open (T46). It also serves Claude models.
- Next: T43 together with T39.

## T43 + T39 – 2026-11-24
- Done (workshop): `code/mmo/analysis/roles.py` - roles from `.agents/roles/<role>.md` of the environment (`version`,
  `writes`), runs as `op: run` events of `history.jsonl`; `mmo role list`, `mmo run start|list`, `--run` on every
  write command (the run gives role and prompt version; `generated_by` gets `role`, `run`; the role's `writes` limits
  what is written); a role must be listed in the analyst's position (`roles:`); `analysis check` reports records
  whose run is missing or differs; the guard gates `mmo run` like other study commands. T39: `prompt_version()` of a
  phase, `mmo status` shows the phase's prompt and the `--prompt-version` to use, `roles:` of `method.yaml` checked by
  `mmo method check`. Docs: `docs/analysis-store.md`.
- Done (research environment, branch `task/T43-roles`, not committed to `main`): six roles in `.agents/roles/`
  (chapter-reader, instance-finder, context-searcher, source-preparer, blind-probe, critic; copies in
  `.claude/agents/`), skill `lead-analyst`, `state-position` with `roles:` and a section "Roles", SKAD prompts
  `prompts/context-analysis.md` and `prompts/fine-analysis.md` (version 2026-11-24, from test 9), SKAD version
  2026-11-24; `AGENTS.md` (protected), `docs/how-it-works.md` (section 7a), `docs/analysis.md`, `methods/README.md`.
- Decisions made in the task: a subagent writes under the model's own id with `--run` (no composite ids, so the
  guard's own-id rule and the profile stay as they are); role prompts that do not depend on the method live in the
  role files, method-specific ones (the critic's template, T46; context search, T44) in `methods/<id>/prompts/roles/`.
- Tried on a copy of `nazi-v-ai-dobe` in `scratch/T43/env` (deleted): position with roles, two chapter readers
  (memos on pp. 101 and 145 with quotations), an instance finder coding the existing code; refused: a chapter reader
  coding, a role not in the position, a finder adding a new code; `run list` shows what each run wrote;
  `analysis check` clean; `status` shows the phase prompt and the runs. Real Claude Code subagents were not run; that
  is the first step of test 10 (or a run in a test copy before it).
- Verified: `uv run pytest` - 157 passed; `uv run ruff check . && uv run ruff format --check .` clean; in the
  environment `mmo method check` 4 ok, `mmo role list` 6 roles, `python3 tools/agents_sync.py --check` clean.
- Open for the owner: approve the prompts and roles (protected `.agents/`, `AGENTS.md`); the critic's role is also
  generated as a Claude Code subagent, but it is meant for another maker (T46 enforces it); prompts for the other
  SKAD phases (content structure, speakers and effects, synthesis) when they are needed; the workshop's `AGENTS.md`
  CLI line does not list `role`, `run` (protected).
- Next: T44 (context search by method).

## 2026-11-24 – Handover (session ends with a compaction)
- Where we are: test 9 analysed (record `scratch/test9/`, kept); what it taught is decided (ADR 0014 lead analyst,
  subagents, critic of another maker; ADR 0015 context search by method and questions) and the first part is built
  (T43 + T39). The direction: one system of analysts in roles with the single view kept in the record, then test 10
  comparing one agent with the orchestrator on a new source.
- Not merged: workshop `task/T43-roles` = 1fc676b (plan after T29) + c8c570c (T42) + 4ccedc6 (T43, T39) on `main`;
  research environment `task/T43-roles` = 0c450a6. Nothing pushed. Before a push or PR: `gh auth status` and the
  owner's confirmation (AGENTS.md).
- Waiting for the owner: approval of the six roles, the skill `lead-analyst`, the `state-position` change, the SKAD
  prompts (`methods/skad/prompts/`) and `AGENTS.md` of the research environment (protected); then the pull requests.
- Open points: the critic role is also generated as a Claude Code subagent although it is meant for another maker
  (T46 enforces); prompts of the other SKAD phases; the workshop's `AGENTS.md` CLI line lacks `role`, `run`
  (protected); `zkusebna/test9` had a stale `.git/index.lock` from Google Drive (fixed) - watch for it in new copies.
- Next session: T44 (context search by method) on a new branch from `task/T43-roles` (or from `main` after merge).

## T44 – 2026-11-24
- Done: context search by the method and the research questions (ADR 0015).
  - Workshop: `code/mmo/analysis/context.py` (search plans = memos of type `search-plan`, rounds, requests to the
    researcher, summary for `mmo status`), `code/mmo/core/provenance.py` (`provenance` of `source.yaml`, reported by
    `mmo source check` for context sources), `mmo context round|request|close|list`, `mmo source provenance`,
    `analysis.web_search` (study setting), `web` recorded on every run, `check_context_search` in `mmo method check`,
    `mmo-guard` denies `WebSearch`/`WebFetch` unless a study lists the model in `analysis.web_search`.
  - Research environment (branch `task/T44-context-search` on `task/T43-roles`): `context_search` in the method.yaml
    of SKAD (version 2026-11-24.1), grounded theory, thematic analysis and the template (2026-11-24); SKAD role prompt
    `prompts/roles/context-searcher.md` mapped by `roles:`; docs (`analysis.md` "Context search", `how-it-works.md`
    7b, `memos.md`, `topics/README.md`, `methods/README.md`). Protected, for the owner's approval:
    `.agents/roles/context-searcher.md` (+ generated copy), `.claude/settings.json` (hook matcher gets
    `WebSearch|WebFetch`), `AGENTS.md` (commands row).
- Verified: `uv run pytest` 163 passed; `uv run ruff check .` and `ruff format --check .` clean; `mmo method check`
  4 ok; `agents_sync --check` clean. Trial in `scratch/T44/env` (metadata of test 9's `nazi-v-ai-dobe`, no texts):
  a plan for q3 was refused for a round while proposed, accepted, round 1 recorded, a context-searcher run said
  "web search: not approved", a request for Newton/Anopress listed by `mmo status`, provenance of
  `recenze-iliteratura` recorded; `mmo context list` showed 13 of 14 context sources without provenance (they came
  before T44).
- Next: the owner approves the protected paths and the method changes; a real context searcher (with or without web)
  runs in test 10. Open: the guard opens web tools for the whole environment when one study approves (it sees no
  study); the context sources of test 9 have no provenance - fill them when the study is carried over. Next task T45
  (blind probe). `scratch/T44/` can be deleted (trial only).
