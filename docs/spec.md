# Specification

> Working specification. Parts marked **(planned)** are direction, not built yet; the owner will test variants
> before they are fixed.

## Concepts

| Concept | Meaning |
| :--- | :--- |
| Topic | A long-lived research project (a study): research questions, goals, sources, analyses. One folder in `topics/` of the research environment. |
| Research question | A question of the topic. A topic usually has several. |
| Goal | What the author and the agent want to find out next; changes over time, every change recorded. |
| Source | A book, interview, field note, document or dataset, with metadata and provenance. |
| Page | One scanned image of a source, with its OCR results per backend. |
| Final text | `text.md` of a source: the one text the analysis reads, the same form for every kind of original (ADR 0012). |
| Segment | A paragraph of the final text with its place (source, scan, page) and character offsets in `text.md`; a rebuildable index for reading, batching and counting. |
| Quotation | What the analysis points to: the exact words of a passage with source, pages and offsets in `text.md`; any length, may cross a page break; made and checked by `mmo quote` (T26). |
| Method | An analytical method, one folder `methods/<id>/` of the research environment: research design, procedure, rules for agents, applications, sources, and `method.yaml` (phases, code types, relation types, outputs) for agents and tests. |
| Analysis run **(planned)** | A step of a model: method phase × questions × chosen passages → proposals in `analysis/`. |
| Proposal **(planned)** | What a model writes - a code, reading, category, theme, relation or memo - with status `proposed` / `accepted` / `edited` / `rejected` / `superseded`, provenance and its quotations; the researcher's own records are not proposals (ADR 0013). |

## Repository layout

Two repositories (ADR 0010, ADR 0011). **Workshop** (this one): `code/mmo/` the program (ADR 0007: `core/` topic
and sources, `ingest/` OCR, page numbers, reading order, final text, segments, `analysis/` quotations and later the
analytic layer, `guard.py` the analyst's hooks) · `docs/` project memory · `tests/` · `tools/`. **Research
environment** `../MIXED-Method-Ontology/`: `topics/` the studies, the only data folder · `methods/` method folders ·
`ontology/` schema and mapping · `analysts/` profiles · `docs/` manuals for the researcher and the analyst ·
`AGENTS.md` and skills of the analyst; it uses `mmo` from the workshop.

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

`ontology/schema/mmo.yaml` (research environment) is a LinkML schema of the core classes. `ontology/mapping.md` maps them to SKOS, W3C Web
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

How methods link purpose, questions and theory: `methods/foundations.md` (research environment) and `research-design.md` of each method.
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
   (`analysts/` of the research environment) and a position in the study at framing, writes reflexive notes when a trigger occurs
   and revisits the memo at synthesis (`methods/reflexivity.md`). The ontology would need `Analyst` (person or
   model version, PROV-O agent) linked to its profile, memos and steps.

Memos are part of every method; format and use: `docs/memos.md` of the research environment.

## Human steering (planned)

Framing (questions, goals, sensitising concepts, seed codebook) · review of proposals (accept, edit, reject with a
reason) · the researcher's own coding and memos, never gated · steering memos fed into later steps · choice of data for
the next round · a fixed codebook when the study asks for one (deductive mode). Phases of a method are a map: the
researcher says where the study is (`mmo phase`, T33) and moves freely; the phase decides only what a model may
propose. What the method calls the researcher's decisions (`researcher_decides`) are decisions, not locks.

## Analysts and roles (planned; ADR 0014)

- **Lead analyst** of a study: position, codebook, interpretation, relations, synthesis, revisiting its position,
  the conversation with the researcher.
- **Subagents** with a clean context and one role each: chapter reader, instance finder, context searcher, source
  preparer, blind probe, critic. Each has a profile, a short position for its role, a versioned prompt of its role and
  phase; it writes only through `mmo` under its own analyst id; its output is a proposal.
- A subagent returns quotations and findings, not conclusions; the lead reads the quoted places before interpreting.
- The single view lives in the record: map, memos, codebook and the **coverage** of each source (read whole, read in
  passages, known only through the map).
- Every run of a subagent is recorded: analyst id, role, model, prompt version, input, what it wrote.
- **The critic** is a model of another maker (checked by `mmo`), chosen per study in `topic.yaml` (default
  `gemini-4-neon-medium`), started through `agy` in print mode by `mmo critic run`; its run is stored in the study;
  its instructions come from the method's critic template filled in by the researcher; round 1 independent, round 2
  comparison. The guard holds: as a hook if `agy` supports one, otherwise `--sandbox` and a check of changes after the
  run.
- Subagents inside Claude Code use the lead's model.

## Outline, coverage and the choice of passages (ADR 0014; built in T36)

- `mmo outline <topic> <source> [--coverage]`: parts of `text.md` from its headings, without a model - `part-01`,
  `part-02`, ... in the order of the headings, each with its level, title, character range, pages and segments.
- `outline` of `source.yaml` (the researcher's): `chapters` (`id`, `title`, `first` - a heading's text or a part id;
  a chapter runs to the next one) and `parts` without a heading (`id`, `title`, `at` - exact words found once in
  `text.md`; the part starts at their line). Declared parts do not renumber the parts from headings. Problems
  (unknown heading, words not found once, a chapter out of order, a taken id) are printed; `mmo outline` exits 1.
- `mmo coverage add <topic> <source> --part <part|chapter|part-03..part-07> --how whole|passages|map` records
  `op: coverage` (`source`, `parts`, `how`, `text_sha256`, `note`) with its author and run; any author. `mmo coverage
  list` and `mmo status` show for each studied source (not context sources) the best reading of each part - whole >
  passages > map > quoted (a coding or memo quotes it, no reading declared) > nobody - per chapter, and the parts
  outside chapters known only through a map or by nobody. A declaration on an earlier `text.md` is not counted.
- `analysis.passage_keys` (`first: [structural, questions]`, `later: [reception, contrast]`; owner 2026-11-19);
  `mmo status` shows them and the number of `passage-choice` memos (the researcher's choice of passages and why).
- `mmo status` shows first impressions by author (the researcher's own reading kept with its time).
- The orientation reading is the method's prompt (SKAD `context-analysis` 2026-11-25): position restated, the whole
  source read chapter by chapter (or by chapter readers), coverage recorded, a first-impression memo with candidate
  passages and their keys, a reflexive memo on having read the whole first.
- `mmo-guard` closes `mmo outline` and `mmo coverage` on a closed study (they read `text.md`).

## The critic of another maker (ADR 0014; built in T46)

- `analysis.critic` of `topic.yaml`: `analyst` (profile id, default `gemini-4-neon`), `model` (the `agy` model,
  default `gemini-4-neon-medium`), `timeout_minutes` (60).
- `mmo critic brief` (the researcher only) copies the method's critic template (`roles: critic:` of `method.yaml`) to
  `topics/<slug>/critic/brief.md`; the researcher replaces every `<fill: ...>` and sets `status: ready`. The guard
  denies a model writing `topics/<slug>/critic/`.
- `mmo critic run --round 1|2 [--dry-run] [--timeout]` refuses a critic of the same maker as another positioned model
  (maker from the profile row `| name, maker | <name>, <maker> |`), a critic without a confirmed profile and position
  listing `critic`, a brief not ready, and round 2 before an accepted round 1. It starts a run of the role `critic`
  and runs `agy -p <prompt> --model <model> --output-format stream-json --sandbox` in the environment with
  `MMO_ANALYST`, `MMO_CRITIC_RUN`, `MMO_CRITIC_ROUND`, `MMO_STUDY`. The prompt is the run's header, the role and the
  brief without the other round's section.
- Record: `topics/<slug>/critic/runs/<run>/` (`prompt.md`, `stream.jsonl`, `response.md`, `check.yaml`) and
  `op: critic-run` (round, analyst, model, prompt version, brief template and hash, prompt hash, status, exit code,
  minutes, steps, calls denied by the guard, records written, files changed, violations).
- After the run the files of the environment (size and time; not `.git`, `.venv`, `files/`, `ingest/`) are compared
  with their state before; anything but memos, the analysis files and the run's record is a violation: `status:
  violations`, not accepted.
- The guard as an `agy` hook (`.agents/hooks.json` of the environment, `mmo-guard agy-pre-tool-use`): the same checks,
  mapped from `agy` tools (`run_command` -> the Bash checks; tools with path arguments -> path checks; `search_web`,
  `read_url_content`, browser tools -> the web check). `agy` treats a missing decision as a denial: no objection is
  `allow` inside a critic's run and `ask` otherwise. In a critic's run file-writing tools are denied (it writes only
  through `mmo`); in round 1 the lead's memos, the analysis files and other analysts' positions are closed.
- In Claude Code a subagent named `critic` is refused (the critic is another maker's model).

## Context search (ADR 0015; built in T44, the blind probe in T45)

- `method.yaml` has `context_search`: `derived_from`, `source_types` (list), `character`, `where` (list), `repeat`;
  `mmo method check` checks its shape, never its content.
- A **search plan** is a memo of type `search-plan`, per research question: context needed, types and character of
  sources and why, where to look (not only the web), how independence is judged, when to stop. A model's plan is
  approved when the researcher accepts or edits it; the researcher's own plan is approved as written.
- `mmo context round` records a round by an approved plan (`op: search-round`, `plan`, `round`, `reason`); a later
  round of the same plan names the gap that started it (`gaps: [memo:<id>]`).
- What a model cannot reach (paid archives, printed sources, interviews) is a request to the researcher:
  `mmo context request` (`op: request`, `request-<n>`, `what`, `why`, `where`, `question`, `plan`); only the
  researcher closes it (`mmo context close`, `op: request-closed`, `outcome`, `sources`). `mmo status` lists the open
  ones.
- `source.yaml` of a context source: `provenance` - `found` (`how`: search | reference | researcher; `query` for a
  search; `place` unless the researcher brought it; `date`; `by`; `plan`; `round`), `type`, `character`, `speaker`,
  `relation` (author | author-circle | independent), `judged`; written by `mmo source provenance`, reported missing
  by `mmo source check`.
- `analysis.web_search: [<model id>]` in `topic.yaml`: the models the researcher lets search the web for the study.
  `mmo run start` records `web: true|false` in the run (`false` for a blind probe). `mmo-guard` allows WebSearch and
  WebFetch only while the model has an open run recorded `web: true` in a study that still lists it; `mmo run close`
  (the lead or the researcher) closes the run and the web with it, and `mmo critic run` closes the critic's run when
  `agy` ends (T48, the owner's answer 2B of 2026-11-25). A web call names no study: the open run says which study it
  is for, and `MMO_STUDY` (set by `mmo critic run`) narrows the check to that study.
- **Blind probe** (T45): `mmo probe start <topic> --source <id> [--analyst <model>]` starts a run of the role
  `blind-probe` whose input is only the title and `citation.authors` of `source.yaml`, and prints the whole task. The
  answer is a `reflexive` memo with `--prior-knowledge source:<id>`, recorded as `prior_knowledge: {source, model,
  before_search, met_source_before}`. Context memos compare it with `--about memo:<probe>`; `mmo probe list` and
  `mmo status` show each probe as compared or not, and remind of a positioned model not probed on a primary source.
  `mmo-guard` keeps a subagent named `blind-probe` (hook field `agent_type`) away from the study's files but its
  position, from `mmo` but `memo add`, and from the web.

## Out of scope now

Exports, MCP server, UI – see `docs/plan.md`. The analysis environment is the current focus; how it works is
defined with the owner before it is specified here.
