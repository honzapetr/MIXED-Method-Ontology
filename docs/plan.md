# Plan

> Tasks `T<n>` with goal, acceptance criteria, verify command, paths and dependencies (`write-plan` skill).
> The next tasks build the environment for qualitative analysis; how it works is
> defined with the owner first, so the tasks under Analysis are direction, not decided. The plan holds the building of the environment;
> a concrete analysis lives in its topic (`topics/<slug>/`: questions, goals, memos). Finished tasks on source
> preparation (T2-T3) are recorded in `docs/progress.md`; the tool is described in `docs/source-preparation.md`.

### T1 – Repository, ingest scripts and drafts (done)
- Goal: agent-ready repository with OCR and segmentation scripts and the first ontology and method drafts.
- Acceptance criteria: Project Lab layout; `mmo` CLI with `topic new`, `source scan`, `ocr run` (tesseract, openai),
  `ocr compare`, `segment`; LinkML draft and standards mapping; GT and TA method modules; tests pass.
- Verify: `uv run pytest`
- Paths: everything (initial commit).

### T7 – Instructions centred on the analysis (done)
- Goal: instructions, docs and plan describe source preparation (OCR) as a tool of the project (owner's
  answer 2026-11-13).
- Acceptance criteria: OCR detail moved from `docs/spec.md` and `README.md` to `docs/source-preparation.md` (nothing
  lost); brief scope and AGENTS.md (**protected path, changed by this task with the owner's approval**) no longer
  frame the project around OCR; the done source-preparation tasks removed from the plan (record in `docs/progress.md`); no code or data removed; links updated.
- Verify: `uv run pytest && python tools/agents_sync.py --check`
- Paths: `AGENTS.md`, `README.md`, `docs/`, `.agents/skills/ingest-sources/`, `.claude/skills/ingest-sources/`
- Depends on: T2g

### T8 – Design of the analysis environment (done)
- Goal: record how methods link purpose, research questions and theory, and the layers of the environment (approach
  as analytic moves, connections, theme map, theory), by walking one study: SKAD on `nazi-v-ai-dobe`.
- Acceptance criteria: `docs/research-design.md` with sources; `research_design` in every method module, checked by
  the method test; owner's answers in `docs/answers.md`; no analysis output yet.
- Verify: `uv run pytest tests/test_ontology_and_methods.py`
- Paths: `docs/`, `methods/`, `tests/test_ontology_and_methods.py`
- Depends on: T7

### T9 – Method folders and the development rules (done)
- Goal: each method in its own folder with its research design, procedure, rules for agents, applications and
  sources; SKAD added; `docs/` separates how the environment is built from how it works (owner 2026-11-14).
- Acceptance criteria: `methods/<id>/` for SKAD, GT and TA with all six files and `methods/_template/`;
  `methods/foundations.md`; `docs/research-design.md` split without loss into `methods/` (method content),
  `docs/spec.md` (planned research design in a topic) and `docs/environment/memos.md`; `docs/development.md`,
  `docs/README.md`, `docs/owner-notes.md`; source preparation moved to `docs/environment/`; links updated, including
  `AGENTS.md` and the `ingest-sources` skill (**protected paths, owner approved**); ADR 0008; topic records its method.
- Verify: `uv run pytest && python tools/agents_sync.py --check`
- Paths: `methods/`, `docs/`, `tests/test_methods.py`, `tests/test_ontology.py`, `AGENTS.md`, `README.md`,
  `ontology/schema/mmo.yaml`, `.agents/skills/ingest-sources/`, `.claude/skills/ingest-sources/`,
  `topics/nazi-v-ai-dobe/topic.yaml`
- Depends on: T8

### T10 – Reflexivity of researchers and models (done)
- Goal: reflexive techniques of qualitative research recorded for the methods, and applied to both analysts: the
  human researcher and every model, which writes notes about itself and writes them whenever a reason arises
  (owner 2026-11-14).
- Acceptance criteria: `methods/reflexivity.md` with sources; `reflexivity.md` in every method folder and the
  template, required by `tests/test_methods.py`; agent rules of each method require a profile, a positionality memo
  and notes on triggers; `docs/environment/analysts/` with README (roles, where notes go, triggers, gate questions),
  templates for a model and a researcher, the profile of `claude-opus-5-5`; `AGENTS.md` rule (**protected path,
  owner asked for the instructions**); ADR 0009; in the study the model's positionality memo and a question
  skeleton for the researcher's memo.
- Verify: `uv run pytest && python tools/agents_sync.py --check`
- Paths: `methods/`, `docs/`, `tests/test_methods.py`, `AGENTS.md`, `topics/nazi-v-ai-dobe/memos/`
- Depends on: T9

### T11 – Study as a repository of its own: `mmo study init` and a test study (done)
- Goal: the environment can create and serve a study that lives in its own git repository next to it, so the
  builder and the analyst roles are separated by folder (ADR 0010, owner 2026-11-14).
- Acceptance criteria: `mmo study init <path> --method <id> --title ...` creates a study folder with its own git,
  `pyproject.toml` (`mmo` as an editable path dependency), `topic.yaml` at its root (title, purpose, questions,
  goals, method, environment path and commit), `sources/`, `memos/`, `feedback.md`, `.gitignore` for page images, and `AGENTS.md`/`CLAUDE.md`
  for the analyst built from `methods/<id>/agent-rules.md`; the other `mmo` commands work on a study folder;
  a simulated study in `tests/fixtures/` used by the tests; `studie/piskoviste/` created and tried by hand (not in
  git of the environment); `docs/environment/` describes how to start a study; ADR 0010 accepted.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/`, `tests/`, `docs/`; `pyproject.toml`, `uv.lock`, `vendor/wheels/README.md` (wheel pinned by
  path, owner approved 2026-11-15)
- Depends on: T10

> T11 was built on a wrong reading of the owner's request; ADR 0011 supersedes ADR 0010. T12-T16 replace the
> earlier T12 ("move `nazi-v-ai-dobe` out").

### T12 – Decision: workshop and research environment (done)
- Goal: the split into the workshop and the research environment is recorded (owner 2026-11-15).
- Acceptance criteria: ADR 0011 with the layout of files of both repositories and of the test environments; ADR
  0010 marked superseded; the owner's answers in `docs/answers.md`; T13-T16 planned.
- Verify: review by the owner
- Paths: `docs/`
- Depends on: T11

### T13 – Rename today's repository to the workshop (done)
- Goal: today's repository becomes the workshop `MIXED-Method-Ontology-vyvoj/` with its history, so the name
  `MIXED-Method-Ontology/` is free for the research environment (ADR 0011).
- Acceptance criteria: the owner renames the folder with VS Code and Claude Code closed; Claude Code's memory folder
  of the old path is moved to the new path's key; `uv sync`, `uv run pytest` pass in the renamed folder; no
  `AGENTS.md` or `CLAUDE.md` in `2026/MIXED-Method-Ontology/`.
- Verify: `uv sync && uv run pytest`
- Paths: the folder itself, `~/.claude/projects/` (memory)
- Depends on: T12

### T14 – Create the research environment `MIXED-Method-Ontology/` (done; `/memory` check by the owner)
- Goal: the research environment is a repository of its own with everything the analyst needs and the study.
- Acceptance criteria: the folders that move (ADR 0011 table) copied; git-ignored page images of `nazi-v-ai-dobe`
  copied and checked against the hashes in `ingest/files.yaml`; `sample-masaryk-suicide` not copied (deleted, owner
  2026-11-14); new `AGENTS.md`/`CLAUDE.md` for the analyst only, `README.md`, `pyproject.toml` (`mmo` as an editable
  path dependency on `../MIXED-Method-Ontology-vyvoj`), `.gitignore`, `.env.example`, `.editorconfig`,
  `.gitattributes`, `.claude/settings.json`, `tools/agents_sync.py`; references to moved files point to their new
  paths; `git init` and a first commit naming the workshop commit; the owner sees the analyst's `AGENTS.md` before
  the commit.
- Verify: in the research environment `uv sync && uv run mmo source check nazi-v-ai-dobe`; Claude Code started
  there shows only the analyst's instructions (`/memory`)
- Paths: new repository `../MIXED-Method-Ontology/`
- Depends on: T13

### T15 – Clean the workshop (done)
- Goal: the workshop holds no research and instructs only the builder.
- Acceptance criteria: `methods/`, `ontology/`, `topics/`, `docs/environment/` and the analyst skills removed;
  `mmo study init` (`code/mmo/core/study.py`, `tests/core/test_study.py`) and `docs/environment/studies.md` removed,
  the `mmo` topic argument keeps taking a path; `tests/test_methods.py`, `tests/test_ontology.py` read
  `../MIXED-Method-Ontology/`; `AGENTS.md`, `CLAUDE.md`, `README.md`, `docs/development.md`, `docs/spec.md`,
  `docs/README.md` rewritten for the builder (**protected paths, need the owner's approval**); sandbox `../studie/`
  deleted.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check . && python tools/agents_sync.py --check`
- Paths: `methods/`, `ontology/`, `topics/`, `docs/`, `code/mmo/`, `tests/`, `AGENTS.md`, `CLAUDE.md`, `README.md`,
  `.agents/`, `.claude/`
- Built (2026-11-19): research folders and the analyst skills removed (kept in the research environment and in
  git history); `mmo study init` removed, the path tests kept in `tests/core/test_study_folder.py`; method and
  ontology tests read `../MIXED-Method-Ontology/` and skip without it (CI); builder docs rewritten.
- Depends on: T14

### T16 – Model profiles from sources (research environment)
- Goal: a model working as an analyst knows what shapes its position and works with it; scalable to any model.
- Acceptance criteria: in `../MIXED-Method-Ontology/`: skill `profile-model` (identify the model from the harness,
  look for its profile, find sources, report to the owner, write with sources and certainty marks, status
  `proposed`, owner confirms; a local model's profile written by the session model); `analysts/_template-model.md`
  by the layers of `methods/reflexivity.md` §2 with "What follows for the analysis"; `AGENTS.md`: read your profile
  at the start of every session, without one run the skill first; profile of `claude-opus-5-5` rewritten from its
  system card and the maker's documents; `methods/reflexivity.md` §2 extended (filters, measured biases, hidden
  system prompt). Each profile complete on its own (owner, 2026-11-15).
- Verify: `python tools/agents_sync.py --check` in the research environment; the owner simulates the first start
  in a test copy
- Paths: `../MIXED-Method-Ontology/` (`.agents/skills/profile-model/`, `.claude/skills/`, `analysts/`, `AGENTS.md`,
  `methods/reflexivity.md`)
- Depends on: T14

### T17 – Test copies of the research environment in `zkusebna/` (done)
- Goal: one command makes a clean test copy of the research environment, e.g. to simulate a model's first start
  (owner 2026-11-15).
- Acceptance criteria: `tools/new_test_env.py` copies what git sees (tracked and untracked-not-ignored), never
  `.env`, `.venv/`, caches, `scratch/` or `.git/`; page images only with `--with-source-files`; `--without-profile`
  leaves out a model profile; no git unless `--git`; rewrites the workshop path in `pyproject.toml` and `uv.lock`;
  refuses an existing target and a target with `AGENTS.md`, `CLAUDE.md` or `.git` above it; logs each copy in
  `zkusebna/_log.tsv`; tests.
- Verify: `uv run pytest tests/test_new_test_env.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `tools/new_test_env.py`, `tests/test_new_test_env.py`, `docs/`
- Depends on: T16

### T18 – The analyst's role: profile × method × topic (research environment) (done; owner tests)
- Goal: the profile is the model's role as an analyst, and in each study it is joined with the method and the topic
  into a role for that study, framed again when the profile or the method changes (owner 2026-11-15; one study,
  one method).
- Acceptance criteria: in `../MIXED-Method-Ontology/`: skill `frame-role` (role memo
  `topics/<slug>/memos/<date>-role-<model-id>.md` before the data are read, with `profile_version`; owner confirms);
  `AGENTS.md` sets the role in three steps every session (profile, study and method, role memo) and asks to act
  from it whenever information is weighed; profile template and `profile-model` with a Role and a Version; Role in
  the profile of `claude-opus-5-5`; `analysts/README.md`, `methods/reflexivity.md`, the agent rules of the methods
  and `docs/memos.md` updated.
- Verify: `python tools/agents_sync.py --check` in the research environment; the owner tests a first start in a test
  copy
- Paths: `../MIXED-Method-Ontology/` (`.agents/skills/`, `.claude/skills/`, `AGENTS.md`, `analysts/`, `methods/`,
  `docs/memos.md`)
- Depends on: T16

### T19 – GitHub account asked when needed, not hard-coded (both repositories) (done)
- Goal: the instructions name no GitHub accounts and work for any researcher; the old positionality memo of the
  study goes (owner 2026-11-16).
- Acceptance criteria: in `AGENTS.md` of the workshop and of `../MIXED-Method-Ontology/` the account question is
  gone from "Before you start"; the Git rules say: no account for local commits, `gh auth status` shown to the owner
  and confirmed before the first push, pull request or `gh` command, never switch accounts, ask the owner to run it
  if `gh` fails; check `git config user.name/email` before the first commit. The memo
  `topics/nazi-v-ai-dobe/memos/2026-11-14-position-claude-opus-5-5.md` is deleted.
- Verify: `grep -rn "honzapetr\|Jan-dolphin" AGENTS.md ../MIXED-Method-Ontology/AGENTS.md` finds nothing; the owner
  tests a first start in a new test copy
- Paths: `AGENTS.md`, `docs/`, `../MIXED-Method-Ontology/` (`AGENTS.md`, `topics/nazi-v-ai-dobe/memos/`)
- Depends on: T18

### T20 – Analysts are the profile files, no hand-kept list (research environment) (done)
- Goal: `analysts/README.md` does not list the profiles by hand; the list went stale in a test copy without the
  profile and repeated the status the profile holds (owner 2026-11-16, test in `zkusebna/test4/`).
- Acceptance criteria: in `../MIXED-Method-Ontology/` the table "Analysts" in `analysts/README.md` is replaced by the
  rule that the analysts are the files `analysts/<id>.md` (not `_template-*`), status and version in each header;
  `profile-model` no longer adds a row; `.claude/` copies synced.
- Verify: `python tools/agents_sync.py --check` in the research environment
- Paths: `../MIXED-Method-Ontology/` (`analysts/README.md`, `.agents/skills/profile-model/`, `.claude/skills/`)
- Depends on: T19

### T21 – Positions apart from memos; profile without build history (research environment) (done)
- Goal: a memo is a note from research, not a position or a version; the analyst's own position and biases in a
  study are a statement of their own; the profile's journal holds research only, the build history is in git
  (owner 2026-11-16).
- Acceptance criteria: in `../MIXED-Method-Ontology/`: positions in `topics/<slug>/positions/<analyst-id>.md`
  (model: `profile_version`, `status`); skill `frame-role` renamed `state-position`; the profile section Role is
  Position; the Opus profile has no workshop task references and an empty journal; the researcher's draft moved to
  `positions/owner.md`; `AGENTS.md` step 2 is a discussion with the researcher where the study is not defined
  (sources, method, topic, questions, the researcher's position); method rules, templates, `docs/memos.md`,
  `analysts/README.md`, `topics/README.md` follow; `.claude/` synced.
- Verify: `python tools/agents_sync.py --check` in the research environment; no `role memo`, `frame-role` or
  `positionality memo` left there
- Paths: `../MIXED-Method-Ontology/` (`AGENTS.md`, `.agents/skills/`, `.claude/skills/`, `analysts/`, `methods/`,
  `docs/memos.md`, `topics/`)
- Depends on: T20

### T22 – Guards for the analyst in Claude Code (research environment) (done; owner tests)
- Goal: the analyst gets what it needs at the start and cannot leave the environment, skip steps or confirm on the
  owner's behalf (owner 2026-11-16).
- Acceptance criteria: a `SessionStart` hook loads only step 1 (the model's profile, its status and version); the
  study context is added to it once studies are defined with the researcher; a `PreToolUse` hook denies paths
  outside the project root, denies reading `sources/*/text.md` and segments of a study until the profile is
  confirmed and the model's position matches the profile version and is confirmed, and asks the owner (permission
  prompt) when a profile or a position is set to `confirmed`; the logic is an `mmo` command with tests, so other
  agents can run it too.
- Decided (owner 2026-11-16): when the hooks cannot run, the start reports `Guards: NOT running` and the model does
  no analytic step (`AGENTS.md`); test copies include the project files and run `uv sync` by default
  (`--without-project-files`, `--no-sync`).
- Built: `mmo-guard` (`code/mmo/guard.py`, standard library and PyYAML only); hooks in
  `../MIXED-Method-Ontology/.claude/settings.json` run `uv run --project "$CLAUDE_PROJECT_DIR" --no-sync mmo-guard`.
  Each guarded tool call costs about 1 s (Python start on the shared drive).
- Verify: `uv run pytest tests/test_guard.py tests/test_new_test_env.py && uv run ruff check . && uv run ruff format
  --check .`; the owner tests a session in a new test copy
- Depends on: T21

### T23 – Input documents of a study out of git (research environment) (done)
- Goal: while the environment is versioned, the study's input documents are not (owner 2026-11-17).
- Acceptance criteria: `topics/.gitignore` lists `nazi-v-ai-dobe/sources/`; the files leave the index and stay on
  disk; `topic.yaml`, `positions/` and `memos/` stay in git; `topics/README.md` says how; test copies still get the
  ignored sources (but not the scans).
- Verify: `uv run pytest tests/test_new_test_env.py && uv run ruff check . && uv run ruff format --check .`
- Depends on: T22

### T24 – The final text as the contract; segments of text.md; quotations decided (both repositories) (done)
- Goal: every source is brought into the same `text.md`; segments are cut from it; the analysis points to
  quotations; what described the earlier solution (segments of OCR variants, offsets into a scan's text) is rewritten
  or removed, and the pipeline is documented (owner 2026-11-17, `docs/answers.md`, ADR 0012).
- Acceptance criteria: `mmo source finalize` writes `text.md` and `segments.jsonl` (paragraphs, offsets into
  `text.md`, `text == text.md[start:end]`, page, `continues`); hyphenation joined in `text.md`; `mmo ingest` writes no
  segments and asks to choose the variant; `mmo segment <topic> <source>` without a variant; `mmo source check`
  reports missing or stale segments; `mmo topic migrate` drops old segments; the guard gates `segments.jsonl`;
  `docs/source-pipeline.md` describes every step (built / planned), the `text.md` format and the planned quotations;
  ADR 0012; spec, README, `AGENTS.md` traceability rule; in `../MIXED-Method-Ontology/`: `AGENTS.md`,
  `docs/source-preparation.md`, `docs/memos.md`, skill `ingest-sources` (+ `.claude/` sync), method texts
  (evidence segments -> quotations, grounded theory's own use of "segment" kept), ontology `Quotation`.
- Verify: `uv run pytest && uv run ruff check . && uv run ruff format --check .`; in the research environment
  `python tools/agents_sync.py --check`
- Paths: `code/mmo/`, `tests/`, `docs/`, `README.md`, `AGENTS.md`; `../MIXED-Method-Ontology/` (`AGENTS.md`, `docs/`,
  `.agents/skills/ingest-sources/`, `.claude/skills/`, `methods/`, `ontology/`)
- Depends on: T23

### T25a – Carry the study work from one test copy to the next (done)
- Goal: a study framed in a test copy goes on in the next copy on the current environment, and keeps growing over
  further copies, without touching the research repository (owner 2026-11-17).
- Acceptance criteria: `tools/new_test_env.py --carry <copy>` compares the earlier copy with the environment commit
  recorded for it in `_log.tsv` and applies what it created, changed or deleted in the study state (`topics/`,
  `analysts/`, without the environment's own files there and without what the machine rebuilds); environment files
  changed in the copy are listed, not carried; a file changed on both sides stops the run until `--on-conflict
  copy|env`; a position written from another profile version is reported; the log records `--carry`; carrying from
  a carried copy carries everything it holds; documented in `docs/test-copies.md`.
- Verify: `uv run pytest tests/test_new_test_env.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `tools/new_test_env.py`, `tests/test_new_test_env.py`, `docs/`
- Depends on: T25

### Later (after the split)
- Check of the computer's environment, at the end of development (owner 2026-11-16): the start hook first checks
  what the environment needs (`uv`, `git`, the virtual environment from `uv sync`, the program `mmo`) and tells the
  researcher plainly what to install; where the guards cannot run, the model offers to install the missing
  dependencies; with `mmo` released as a package, so others can use the environment.
- A trial that the analyst role is clean in a test copy (`/memory`).
- Releasing `mmo` as a wheel into the research environment instead of the path dependency.

## Where we are (2026-11-19)

Built and merged into `main` of both repositories: the source pipeline (any original -> `text.md` -> segments ->
quotations, T24-T26), the analysis store and the free toolbox (T32), the method as orientation with study
settings, phases and status (T33), proposals of models and the researcher's review (T29); the workshop holds no
research (T15). The whole working cycle can be walked: session start -> profile and position -> study -> sources ->
phases -> quotations, codes, memos, relations -> proposals -> review -> checks. How it works for the researcher:
`../MIXED-Method-Ontology/docs/how-it-works.md`; for the builder: `docs/source-pipeline.md`,
`docs/analysis-store.md`, `docs/test-copies.md`.

**Now: test 9 (owner).** `zkusebna/test9` made from the research environment `main` without `--carry` (from the
start). The owner walks the study `nazi-v-ai-dobe` with a model: session start, profile, the researcher's and the
model's positions, framing (`topic.yaml` questions), `mmo phase`, corpus and context sources (a web page saved as a
text file in `files/` goes through `mmo ingest` + `source finalize` without T28), context analysis memos, fine
analysis of passages of the book (`mmo quote`, `mmo code apply`, `mmo memo add`), `mmo review`, `mmo status`,
`mmo analysis check`. What it teaches is written as tasks; it decides T36, T39 and T31 in detail.

**After test 9**, in this order unless the test says otherwise: T39 (prompts per phase), T36 (outline and
orientation reading), T28 (web pages), T37, T34, T30, T38, T35, T31; T40 and T41 when convenient; T27 when a PDF
comes.

## Analysis

> Replaces T4-T6 of the first plan (written before the split, for paths that no longer exist). The analytic layer
> is built by walking the study `nazi-v-ai-dobe` with SKAD: each task adds what the next phase needs. Decided by the
> owner (2026-11-17): both drive the analysis - an agent in a chat that calls `mmo` to store and check its output,
> and `mmo` calling models through the gateway - over the same proposals and checks; the agent first.

### T25 – Page furniture out of the final text (done)
- Goal: running heads and lone printed page numbers are not content; they no longer become segments or get glued to
  the first paragraph of a page (in `kniha` 478 of 1,581 segments are shorter than 40 characters, mostly these).
- Acceptance criteria: a rule step before `text.md` is written recognises a line repeated at the top of many pages
  (book or chapter title) and a line that is only the page's own printed number, and leaves them out of the text
  (the page number stays in the location comment); what was left out is listed per variant in `ingest/` so it can be
  reviewed; footnotes stay text; tests on samples from `kniha`; the owner decides before `kniha/text.md` is rebuilt.
- Verify: `uv run pytest tests/ingest/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/ingest/`, `tests/ingest/`, `docs/source-pipeline.md`; `../MIXED-Method-Ontology/docs/`
- Built: `code/mmo/ingest/furniture.py`, list `ingest/furniture/<variant>.yaml`, header `left_out`; on a copy of
  `kniha` 203 running heads and 200 page numbers left out, segments 1,581 -> 1,240.
- Depends on: T24

### T25b – Design of the analytic layer (done)
- Goal: decide how `mmo` supports the analysis without limiting it.
- Built: ADR 0013, `AGENTS.md` traceability rule in both repositories, this section rewritten (T26-T36).
- Depends on: T25

### T26 – Quotations: find, check, find again (done)
- Goal: what the analysis points to can be created only from words that are really in `text.md`.
- Acceptance criteria: `mmo quote find <topic> <source> "<words>" [--page n | --segment id]` prints a quotation
  (source, start, end, pages, scans, exact, which `text.md`) or refuses (not found, found more than once without a
  hint); whitespace compared loosely, a location comment inside the span is skipped; `mmo quote check <topic>`
  verifies every quotation in a study's analytic files and finds moved ones again after `text.md` was rebuilt,
  reporting those whose words are gone; ontology `Quotation` used; format in `docs/source-pipeline.md`.
- Verify: `uv run pytest tests/test_quote.py && uv run ruff check . && uv run ruff format --check .`
- Built: `code/mmo/analysis/quote.py`, `mmo quote find` / `check [--update]`; ontology `Quotation` slots `exact`,
  `prefix`, `suffix`, `pages`, `scans`, `text_sha256`; the guard closes `mmo quote` like `text.md`.
- Paths: `code/mmo/analysis/`, `code/mmo/cli.py`, `tests/`, `docs/`, `../MIXED-Method-Ontology/ontology/`
- Depends on: T24

### T27 – PDF with a text layer into the final text
- Goal: a new book or article as a PDF needs no OCR and no model.
- Acceptance criteria: `mmo ingest` recognises a PDF with a text layer and writes one working record per PDF page
  (variant `pdf`), printed page numbers from page labels or the page edge, reading order of the PDF; a PDF without a
  text layer is rendered to images and goes the photo path; location comment `page <n> (<how>) · pdf <i> · <file>`;
  library chosen in the task (ADR if it is a new dependency); tests on a small sample PDF; the owner provides a
  real PDF to try.
- Verify: `uv run pytest tests/ingest/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/ingest/`, `tests/ingest/`, `pyproject.toml`, `uv.lock`, `docs/`
- Depends on: T25

### T28 – Web pages into the final text
- Goal: reviews, announcements and debates (context sources) come in the same way as a book.
- Acceptance criteria: `mmo source fetch <topic> <source>` downloads the URL of `citation.url` into `files/` with the
  date and SHA-256 (a page saved by hand works too); the main text is extracted into the variant `web` with the
  article's headings; `citation.accessed` is set; location comment `web <file> · scan 1`; tests on a saved sample
  page. The owner decides which of the study's context sources are fetched (SKAD phase Corpus).
- Verify: `uv run pytest tests/ingest/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/ingest/`, `tests/ingest/`, `pyproject.toml`, `uv.lock`, `docs/`
- Depends on: T24

> **ADR 0013 (2026-11-19): free analysis on a fixed core.** `mmo` checks integrity - quotations are the exact
> words, every record has author and time (and model, prompt version), a model's output is a proposal until the
> researcher accepts it, nothing disappears without a trace - never the method. The operations of qualitative
> analysis are a toolbox for every method; a method's vocabulary and phases are orientation, `model_role` binds
> models only; strictness is set per study in `topic.yaml`. Source of truth: text files in
> `topics/<slug>/analysis/`; the graph, the graph browser and the REFI-QDA export are views. Order: T26 (done),
> T15 (clean the workshop), T32, T33, T29, then T36, T37, T34, T30, T38, T35, T31. Amendment of ADR 0013 (statuses,
> memos, phases, decisions of the researcher, indexes, hand edits) applies to all of them.
>
> **Similarity and graph procedures (owner, 2026-11-19).** Semantic similarity finds candidates, never analytic
> relations: narratives that belong together without similar words are found through interpretation (codes of
> story elements, schemes, dimensions) and graph procedures over the confirmed analysis. Classic RAG is not used for
> interpretation, which reads passages in sequence with their context.

### T32 – The analysis store and the free toolbox (done)
- Goal: the researcher and an agent code and write freely; every step is recorded and traceable.
- Acceptance criteria: layout of `topics/<slug>/analysis/` (codebook, codings, relations, proposals, history; text
  files, sorted, readable in a diff; memos and positions stay in `memos/` and `positions/`) in `docs/` and the ontology; `mmo code` adds a code (any name and type), codes a
  quotation, renames, merges, splits, recodes; `mmo memo` attaches a memo to a quotation, code, relation, source or
  memo; `mmo relate` links any two items; every operation records author, time, method and, for a model, model and
  prompt version, and appends to the history; nothing is refused for method reasons, only for integrity (a quotation
  not in `text.md`, a missing author); the guard lets a model write `analysis/` only through `mmo`; the researcher may edit by hand, and `mmo check`
  notices such an edit and records it in the history; tests with a toy method.
- Verify: `uv run pytest tests/analysis/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/analysis/`, `code/mmo/cli.py`, `code/mmo/guard.py`, `tests/analysis/`, `docs/`,
  `../MIXED-Method-Ontology/ontology/`, `../MIXED-Method-Ontology/docs/`
- Built: `code/mmo/analysis/store.py`; `mmo code add|apply|rename|merge|split|recode|withdraw|list`,
  `mmo relation add`, `mmo memo add`, `mmo analysis check [--record]`; guard: `analysis/` through `mmo` only, under
  the model's own id; ontology `withdrawn`, slot `method`; docs `docs/analysis-store.md`, research environment
  `docs/analysis.md`.
- Depends on: T26

### T33 – The method as orientation, strictness per study (done)
- Goal: a new method is added by describing it; `mmo` guides by it without limiting the researcher.
- Acceptance criteria: a schema of `method.yaml` (vocabulary, map of phases, `model_role`, practices, prompts per
  phase, versioned) and `mmo method check`; SKAD, GT, TA and the template pass; `topic.yaml` `analysis:` settings
  (codebook, own types, phases as orientation or sequence, model phases and alternatives, team mode, where a
  quotation is required) with defaults that leave the analysis free; `mmo phase <topic> <phase>` sets where the study
  is (free movement, recorded in the history; the phase only limits what a model may propose); the field
  `researcher_decides` (formerly `human_gate`) read as decisions, never locks; `mmo status` shows the map of phases, where the
  study is, what was made and the reminders of the method's practices; a type outside the vocabulary is allowed
  (a memo asked for only if the study says so); several methods in one study; tests with a toy method.
- Verify: `uv run pytest tests/analysis/ tests/test_methods.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/analysis/`, `code/mmo/cli.py`, `tests/`, `docs/`, `../MIXED-Method-Ontology/methods/`,
  `../MIXED-Method-Ontology/docs/`
- Built: `code/mmo/analysis/method.py`, `status.py`; `mmo method check`, `mmo phase`, `mmo status`; settings
  `analysis:` kept by the toolbox; `version` in every `method.yaml`; docs `docs/analysis-store.md`, research
  environment `methods/README.md`, `docs/analysis.md`.
- Depends on: T32

### T29 – Proposals of models and their review (done)
- Goal: what a model proposes (readings, codes, memos, relations) waits for the researcher, who accepts, edits or
  rejects it (replaces T6).
- Acceptance criteria: proposals in `analysis/proposals/` with status `proposed` / `accepted` / `edited` /
  `rejected` (with a reason) / `superseded` (ontology `ProposalStatus`), model, prompt version, time and quotations checked by T26; a proposal outside what the
  method's `model_role` and the study allow for the current phase is refused; `mmo review` lists, accepts, edits,
  rejects; an accepted proposal becomes a record of the toolbox (T32) that keeps its provenance; the researcher's
  own work is never gated; tried on passages of `kniha` in a test copy.
- Verify: `uv run pytest tests/analysis/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/analysis/`, `tests/analysis/`, `docs/`, `../MIXED-Method-Ontology/methods/skad/`,
  `../MIXED-Method-Ontology/.agents/skills/`
- Built: `code/mmo/analysis/review.py`; `mmo review list|accept|edit|reject`; proposals are records with
  `status: proposed` in place (no separate folder); `model_proposes` per phase (SKAD filled from `model_role`);
  codebook changes researcher-only; `--alternative`; guard; research environment `docs/how-it-works.md`.
- Depends on: T33

### T36 – Outline of a source and the model's orientation reading
- Goal: the researcher and the model know the structure of a source and where to start the fine analysis.
- Acceptance criteria:
  - `mmo outline <topic> <source>` lists the parts of `text.md` from its headings (chapter, section, pages, segment
    range), without a model.
  - Orientation reading: the model restates its position, then reads the whole source chapter by chapter and writes
    a first-impression memo (SKAD context analysis) as a proposal: what each part is about, places that touch the
    research questions, candidate passages each with a quotation and the key it was chosen by; marked as
    impressions, not interpretation; followed by a reflexive note of the model on having read the whole first.
  - Keys for choosing passages, set per study in `topic.yaml` with this default (owner, 2026-11-19): first
    *structural* (introduction, openings and endings of chapters, where the author says what the book is about)
    searched by the *research questions*; in later rounds *reception* (places the context sources cite or discuss)
    and *contrast* (minimal and maximal, theoretical sampling).
  - The researcher chooses the passages and records why in a memo; the fine analysis reads a chosen passage
    sequentially with its nearest context and proposes readings (with alternatives) and open codes (T29).
  - The researcher's own reading is supported (a first-impression memo of the researcher, recorded with its time,
    so it can be seen what came from whom) but is never a condition for the model's reading.
  - Tried on `kniha` in a test copy.
- Verify: `uv run pytest tests/analysis/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/analysis/`, `code/mmo/cli.py`, `tests/`, `docs/`, `../MIXED-Method-Ontology/methods/skad/`,
  `../MIXED-Method-Ontology/.agents/skills/`
- Depends on: T29

### T34 – Export to REFI-QDA
- Goal: the study can be opened and looked at in QualCoder, ATLAS.ti, MAXQDA or NVivo.
- Acceptance criteria: `mmo export qdpx <topic>` writes a `.qdpx` (REFI-QDA project 1.0): sources as plain text
  documents, each the whole `text.md` (so the offsets of quotations hold), codes with their hierarchy, codings as plain-text selections (our offsets), memos,
  relations as links, document groups and attributes; method types as code groups or colours; what the standard
  cannot carry is listed in the export's report; validated against the REFI-QDA schema; opened in QualCoder by the
  owner. Export only; import is a later task.
- Verify: `uv run pytest tests/export/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/export/`, `code/mmo/cli.py`, `tests/export/`, `docs/`
- Depends on: T32

### T30 – Graph store (replaces T4)
- Goal: the analysis as an RDF graph, built from the files of `analysis/`, for queries.
- Acceptance criteria: ADR on the graph store; `mmo graph build` writes sorted Turtle per named graph and an
  Oxigraph index from the files (a view: built again at any time, never edited, git-ignored and never carried
  by `tools/new_test_env.py --carry`); quotations as W3C Web Annotation,
  provenance as PROV; SPARQL queries by quotation, code, memo and method work; round trip test.
- Verify: `uv run pytest tests/test_graph.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/graph/`, `tests/`, `docs/adr/`, `../MIXED-Method-Ontology/ontology/`
- Depends on: T32

### T35 – Graph browser in the homelab
- Goal: the researcher looks at the network of codes, quotations and memos in a browser.
- Acceptance criteria: GraphDB Free or Apache Jena Fuseki chosen (ADR), run as a container in the homelab
  (compose file, LAN/VPN only); `mmo graph push` loads a study's graph into it; a short guide with saved queries and
  views (codes of a source, quotations of a code, memos of a code); tried on the study in a test copy.
- Verify: `uv run pytest tests/test_graph.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/graph/`, `compose.*.yaml`, `docs/`, `docs/adr/`
- Depends on: T30

### T31 – Model backends for analysis steps (replaces T5)
- Goal: an analysis step can run on a local model through the gateway with the same checks as an agent.
- Acceptance criteria: (both drivers decided, see the note above) backend per step configured in the topic; the
  prompt of the method's phase (T33); every call recorded (model, prompt version, input quotations); its output goes
  in as proposals (T29); proposals whose quotations fail T26 are refused.
- Verify: `uv run pytest tests/test_llm.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/analysis/`, `tests/`
- Depends on: T29

### T37 – Similarity index of segments (a finder of candidates)
- Goal: passages that say something similar in other words are found as candidates for constant comparison,
  minimal and maximal contrast and reception (what a review discusses in the book).
- Acceptance criteria:
  - a local multilingual embedding model through the gateway (Czech; e.g. bge-m3 or multilingual-e5; chosen in the
    task, ADR) - if the gateway has none, setting it up is part of the task (homelab, LAN/VPN only);
  - `mmo similar index <topic>` embeds the segments of every `text.md` into an index that is a view (rebuilt from
    the segments, never edited, git-ignored and never carried by `--carry`; a light store in `mmo` such as sqlite-vec or LanceDB, chosen in the
    task); the index records model, version and the `text_sha256` it was built from and says when it is stale;
  - `mmo similar find <topic> (--quotation <file/record> | --segment <id> | "<words>") [--source] [--top n]` lists
    candidate segments with source, pages and score; a candidate is not a relation: what is kept becomes a proposal
    or a coding with its quotation (T29, T32), its reason written by the researcher or the model;
  - every search used in the analysis is recorded (model, query, time) and is a trigger of a reflexive note (what
    the machine took as similar steered attention); on/off per study in `topic.yaml`;
  - closed to a model like `text.md` (guard); tests with a small fake embedding backend; tried on `kniha` and the
    reviews.
- Verify: `uv run pytest tests/analysis/ && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/analysis/`, `code/mmo/cli.py`, `code/mmo/guard.py`, `tests/analysis/`, `docs/`, `docs/adr/`,
  `pyproject.toml`, `uv.lock`, `../MIXED-Method-Ontology/docs/`
- Depends on: T29

### T38 – Graph procedures over the analysis
- Goal: narratives and themes that relate without similar words are found through the analysis itself - codes,
  relations, memos - not through the wording.
- Acceptance criteria:
  - over the graph of the confirmed analysis (T30), with the method's vocabulary as orientation: co-occurrence of
    codes (in a quotation, a segment, a document), chains of relations (e.g. SKAD `story_link`: the story line),
    paths between two codes or themes through shared elements, communities and central codes, passages with the
    same story element but an opposite evaluation (contrast);
  - `mmo graph query <topic> <procedure> ...` runs a named procedure (SPARQL kept in the repository, versioned) and
    lists results with their quotations; the same procedures are saved queries of the graph browser (T35);
  - results are views for the researcher; what is kept is written as a memo or a relation through the toolbox;
  - procedures are method-agnostic (a toy method in tests) and tried on the study in a test copy.
- Verify: `uv run pytest tests/test_graph.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `code/mmo/graph/`, `code/mmo/cli.py`, `tests/`, `docs/`
- Depends on: T30

### T39 – Prompts per phase of a method (versioned)
- Goal: what a model does in a phase is written down and versioned, so `--prompt-version` names a real prompt, not
  `chat@<date>`; the same prompt serves the agent in a chat and a local model (T31).
- Acceptance criteria: `methods/skad/prompts/<phase>.md` for the phases a model works in (at least
  context-analysis, fine-analysis), each with a `version:` line, the inputs it needs (passages as quotations,
  the model's position, the study's questions), what it writes through `mmo` (`model_proposes` of the phase,
  quotations, alternatives) and its reflexive checks from `methods/skad/reflexivity.md`; `prompt` set in
  `method.yaml`, method version raised; `mmo status` shows the phase's prompt and version; the skill or the
  analyst's instructions tell a model to use `<method>/<phase>@<version>` as `--prompt-version`; written from what
  test 9 showed; the method texts are not shortened (precision before economy); the owner approves the prompts.
- Verify: `uv run pytest tests/analysis/ tests/test_methods.py && uv run ruff check . && uv run ruff format --check .`
- Paths: `../MIXED-Method-Ontology/methods/skad/`, `../MIXED-Method-Ontology/.agents/skills/`,
  `../MIXED-Method-Ontology/AGENTS.md` (protected: owner's approval), `code/mmo/analysis/`, `tests/`, `docs/`
- Depends on: T29, test 9

### T40 – What a model proposes in grounded theory and thematic analysis
- Goal: GT and TA bind models per phase as SKAD does.
- Acceptance criteria: `model_proposes` for every phase of `methods/grounded-theory/method.yaml` and
  `methods/thematic-analysis/method.yaml`, derived from their `model_role` and procedure texts, method versions
  raised; `mmo method check` passes; the owner approves the mapping (it binds models).
- Verify: `uv run pytest tests/test_methods.py && uv run ruff check .`
- Paths: `../MIXED-Method-Ontology/methods/grounded-theory/`, `../MIXED-Method-Ontology/methods/thematic-analysis/`
- Depends on: T29

### T41 – Clean scratch folders
- Goal: no stale copies of study data in the workshop.
- Acceptance criteria: `scratch/T15/` (leftovers of the old `topics/`, all present in the research environment,
  and the empty sandbox), `scratch/T25b/old-main-leftovers/`, `scratch/T32/env`, `scratch/T29/env` deleted after the
  owner agrees (the classifier refuses deleting without it); one-off scripts of finished tasks removed.
- Verify: `ls scratch/`
- Paths: `scratch/`
- Depends on: -

Open for discussion: a model proposing bibliographic fields of `source.yaml` (from the imprint or the annotation),
confirmed by the researcher.

Later: import of the researcher's coding from REFI-QDA, exports (SKOS, report), querying a finished topic, adding material
with a change overview, quantitative link (DDI-CDI), read-only MCP server, UI.
