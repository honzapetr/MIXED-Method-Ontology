# Answers

> The owner's answers to questions, newest last. They override earlier assumptions.

## 2026-11-06 – first planning conversation

- **Repository:** boilerplate for agentic development in a local folder, usable from Claude Code and Google
  Antigravity.
- **Sources:** the first book exists only as page images (scans). OCR is part of the infrastructure and may run on
  the owner's server.
- **Ontology format:** LinkML (agreed). `.qdpx` export is wanted. The owner knows ATLAS.ti; an open-source QDA tool
  is welcome too (candidate: QualCoder).
- **Review:** CLI first, UI later.
- **Unit of work:** a *topic*, not a single method run. A topic has one or more research questions; the author and
  an AI agent define goals together. The agent must know the methods and how each reaches conclusions. Qualitative
  results must connect to quantitative data. A finished topic must stay usable: ask new questions, see it from
  another angle, add material and update the graph and the analysis.
- **Versions:** a main state and side variants, like branches on GitHub. Git-based versioning of topics is agreed.
- **Parsing of sources is dynamic:** the agent looks at the files in a topic and proposes how to parse them.
- **Models:** local first, through the homelab (see `docs/spec.md`, section Homelab). Cloud API is allowed but not
  the default. It is not decided yet which models do the analysis; variants will be tested.
- **First book / question:** not decided; the agent picks a sample topic and question for development. Which book
  does not matter – the goal is the infrastructure.
- **Next step:** prepare folders, instructions and scripts; then continue locally with real scans and tune OCR.

## 2026-11-12 – how a topic is stored

- **Source-centric layout (approved):** everything about one source lives in its own folder; what the researcher
  writes (metadata, notes, page-number fixes) is kept apart from what the machine produces (OCR, page numbers, order
  report) and from the readable text. The current layout by processing step (`work/ocr`, `work/numbers`,
  `work/order`, `work/text`) is hard to find one's way in.
- **Supplementary information = new sources:** material about a source (reviews, interviews with the author,
  context documents) is added as a source of its own with the role `context`, linked to the source it is about, and
  goes through the same ingest; it is traceable the same way as the primary source.
- **Adding a source should be one step** with the existing OCR tools, not five separate commands.
- **Code layout:** `src/` is confusing here (it reads as research sources). The program moves to `code/mmo/`,
  split into `core/` (project core) and `ingest/` (bringing new data in); command `mmo` unchanged. The empty
  `data/` folder was removed - research data lives only in `topics/`.

## 2026-11-13 – what the project is about

- **The project is the analysis.** OCR was only needed to get the text of the first book; it is a tool for bringing
  in new information (more texts will come), a service like any other tool of the project. Keep the OCR tools;
  instructions, docs and plans describe them as a tool and are not built around OCR. The next focus is the environment for qualitative analysis with AI: how to do
  qualitative analysis with AI by specific approaches, how to find connections in a text and map themes.
- An agent's proposal to treat the analysis as an experiment comparing variants against a benchmark was rejected:
  it came from the OCR work, not from the owner. The way the analysis works is defined with the owner.

## 2026-11-13 – the analysis environment
- **Layers (approved):** (1) an approach as a sequence of analytic moves, each saying what the model does and what
  the researcher does; (2) finding connections in the text in several ways side by side (co-occurrence, semantic
  closeness, tensions, argument structure, typed relations of the method); (3) the theme map as a view of the graph,
  every element with its evidence quotes and status.
- **Theory is part of the process:** how a theory is built and how one works with it afterwards must be a layer of
  the environment, not left out.
- **First method:** the most suitable one for the purpose; the owner has always liked discourse analysis. The
  variant is still to be chosen.
- **Research questions belong with theory:** questions must be tied to why the research exists and what the
  researcher wants to find out; the environment follows how the methodologies let questions and theories arise
  (background: `docs/research-design.md`).
- **How we work now (owner):** we are building the analysis environment, not analysing yet. One study is walked
  through to set the environment up, and what is learned along the way is recorded for the next steps.
- **The study:** SKAD on `nazi-v-dobe-ai`. The purpose of the study is specified later, while going through SKAD.
- **Role of AI:** not decided; scenarios have to be tested.
- **Two lines (owner):** building the environment and the concrete analysis with its sources are kept apart.
  Information about sources has its place in the topic.
- **Topic renamed** to the printed title of the book: "Nazí v AI době", slug `nazi-v-ai-dobe`.
- **Web material about the book** (annotation, reviews, debate, announcement, catalogue) goes in as context
  sources of the topic.
- **Notes and impressions are part of the methodology:** an impression about a source is a note to that source
  and one of the first analytic steps; the infrastructure must make such notes functional (proposal in
  `docs/research-design.md`, section Memos).

## 2026-11-14 – methods and the development rules
- **A method is a folder** with its own research design, procedure, rules for agents, connected applications and
  sources; the description must be holistic and exact for each method, even where it repeats another.
- **SKAD** is the analysis we do; it is added as a method.
- **`docs/`** separates how the environment is built from how it works; the working rules of development (what goes
  where: new method, information for development, concrete analyses and data sources) are written down.
- **AGENTS.md** may be changed for the new layout (approved).
- **Connected applications:** ATLAS.ti and QualCoder for now; more when the study shows the need.
- **Owner's notes:** a file in `docs/` for the owner's own notes while building (`docs/owner-notes.md`).
- **Reflexivity** (later the same day): self-reflective techniques (own background, bias) are part of qualitative
  analysis and must be recorded in the documentation. They apply to the model too: every model writes notes about
  itself, as `claude-opus-5-5` did, and has instructions to write notes as soon as there is a reason. The human
  researcher (the owner) works with reflexivity as well. Kept in both lines: the environment and the study.
- **Research findings first:** the owner wants to see and approve findings before they are written into the
  project.

## 2026-11-14 – the environment and the study apart
- **Two repositories (approved for preparation):** the environment (program, methods, ontology, tests) and each
  study are kept in separate git repositories, so the agent's role (builder or analyst) follows the folder it is
  started in, and trying the analysis does not change the environment. Background found by the model: research
  compendium (Turing Way; Marwick, Boettiger & Mullen 2018), Claude Code loads instructions and memory per folder
  and per git repository, uv path dependencies (ADR 0010).
- **Location:** both stay on Google Drive (`2026/MIXED-Method-Ontology/`); not moved elsewhere.
- **Later:** where analyst profiles live, and a GitHub repository for the study.
- **T11 started** (owner). The sample topic `sample-masaryk-suicide` is deleted in T12, not moved to the fixtures.

## 2026-11-15 – the vendored wheel
- **`fabric-ocr` pinned by file path** instead of the flat index `fabric-vendor` (approved): a study using the
  environment as a path dependency could not install it otherwise (ADR 0005 amendment, ADR 0010).

## 2026-11-15 – workshop and research environment (correction)
- **Two repositories, meant this way (owner confirmed):** (1) the **workshop** – where the environment is built:
  plan, progress, ADRs, development rules, owner's notes, builder roles (planner, coder, reviewer), tests and trial
  copies; no research. (2) the **research environment** – the product, an ecosystem: all methods and approaches,
  analysis tools, ontology, rules and profiles of analysts, and **many studies** (`nazi-v-ai-dobe` is only the
  first). Opened in the environment, the agent is an analyst; opened in the workshop, a builder who changes the
  environment only through planned tasks and tries things on a copy.
- **T11 and ADR 0010 read the request wrongly** ("environment vs. one study"). Nothing reverted yet; to be reviewed.
- **Still open:** where `mmo` with its tests lives (model's proposal: in the research environment, the workshop
  holds plans, decisions and role setup); whether studies live inside the environment (`topics/`) or as folders
  next to it.

## 2026-11-15 – the two repositories decided
- **`mmo` belongs to the workshop.** The workshop is developed like an ordinary application.
- **Studies live inside the research environment** (`topics/`); they are part of the product.
- **Test research environments stay** so the environment can be tried; they need no git. Versions are kept only in
  the two repositories, the workshop and the research environment.
- **Roles must not stack through the folder tree:** a test environment must be clean, with no `AGENTS.md` or
  `CLAUDE.md` of another role above it.
- **Methods and ontology belong to the research environment**, because the analyst needs them for analyses. The
  analyst works only on research; what to change in the analyst's role, the methods or the procedures the owner
  agrees with the builder in the workshop. The model is not to design the process now, only the layout of files.
- **Names (changed by the owner the same day):** the workshop is renamed to `MIXED-Method-Ontology-vyvoj/` and keeps
  the git history; the research environment with the analyst is the new `MIXED-Method-Ontology/` with a fresh git
  history (first commit names the workshop commit). GitHub account for sessions: `honzapetr`. ADR 0011.
- **Order:** split the folders first; test environments and the rest after. The owner will correct the file layout.

## 2026-11-15 – file layout of the split confirmed
- **Layout of ADR 0011 confirmed** as proposed by the model (trees shown to the owner).
- **Skills in the research environment:** `.agents/skills/` stays the source there too; `tools/agents_sync.py` is
  copied so agents other than Claude Code keep the skills.
- **`.claude/settings.json`** is copied (denies reading `.env` and pushing to `main`).
- **Analyst profiles move whole**, journals included, also entries written during the builder's work.
- **`scratch/T11/` never existed at the time of T13**; only the sandbox `../studie/` is to be deleted (T15).
- **`.env` of the research environment starts new** (2026-11-15); the workshop's `.env` is not copied.
- **References to workshop files rewritten in the research environment** (owner): the environment is not meant to
  be finished; roles and procedures of the analysis are developed in a new thread, step by step with the walk
  through the analysis. The walk continues where it stopped: the analysts' personal journals, own biases, what
  influences them.

## 2026-11-15 – model profiles in the research environment
- **Goal (owner):** information about the model as an analyst lives in the research environment, added in a
  scalable way: a model starting in the analytic repository for the first time finds out what it is, looks up what
  concerns it (training data, post-training, filters, measured biases), writes it into its own profile and then
  works with it automatically. Opus 5.5 is the first case; the project is ready for other models.
- **Local models:** the model leading the session writes their profile, marked so.
- **One maker, several models:** each profile is complete on its own (precision before economy; documents change
  between versions).
- **Approval:** a profile is `proposed` until the owner confirms it; no analytic step before that.

## 2026-11-15 – The analyst's role

- The analyst's own position is not only a memo: the profile is the role of the analyst (the model working in the
  research environment, not the builder in the workshop), and its position and biases are part of every judgement
  of information.
- At the start of an instance the role is set from the model and the method; a new study frames it again.
- For now one study has one method.
- Change the research environment now, then test again.

## 2026-11-16 – GitHub account and the old positionality memo

- No GitHub account names in the instructions: the agent asks only before the first operation that talks to GitHub,
  shows what `gh auth status` reports and waits for the owner's confirmation, so the rule works for anyone. Applies
  to the research environment and the workshop.
- The positionality memo `2026-11-14-position-claude-opus-5-5` of `nazi-v-ai-dobe` is not needed; delete it (the
  role memo from `frame-role` takes its place).

## 2026-11-16 – Memos, positions and the profile journal

- A memo is a note written during the research ("what occurred to me"), not a version or a role. The analyst's own
  position and biases in a study are a statement of their own: `topics/<slug>/positions/<analyst-id>.md`. Skill
  `state-position`; the profile section Role is Position.
- The profile journal is part of the research process; the history of building the environment is kept in git and
  does not appear in profiles.
- The session start is staged: (1) the model loads information about itself and secures its own position; (2) what
  is studied and by which method is a discussion with the researcher (sources, methodology, topic, questions, the
  researcher's own position). A start hook loads only step 1 now and is extended once studies are defined.
- Guards approved: stay inside the project, no reading of source text before the steps, confirmations through the
  owner (T22).
- Hooks (T22) are used now. Only the check that the computer has what the environment needs (`uv`, `git`, the
  virtual environment, `mmo`), with a notice what to install, comes at the end of development (2026-11-16).
- T22 decisions: when the hooks cannot run, the start says `Guards: NOT running` and the model does no analytic
  step (later: the model offers to install the dependencies); test copies include the project files and run
  `uv sync` by default.

## 2026-11-17 – The text for the analysis, segments and quotations

- The OCR work on the first book was meant to get its text; the format of `text.md` grew out of it without being
  decided as the input of the analysis. Now it is decided: `text.md` is the one format every source is brought into,
  whatever its original (photos, PDF, web page, text file). The conversion is done by the program, without AI; OCR
  only where there is no text layer.
- The header of `text.md` is written by the program (technical facts: source, variant, pages, what is missing,
  who or what read it). Bibliographic and research facts stay in `source.yaml`, written by the researcher; whether a
  model may propose them (from the imprint, the annotation) is still to be discussed.
- Segments are paragraphs of `text.md`, cut by the program after the text is final; not pages. A page is a place for
  citing, not a unit of meaning; the page stays as a field of every segment.
- What the analysis points to is a **quotation** (not "anchor"; the word collides with Mayring's anchor examples):
  the exact words of a passage with its source, pages and character offsets in `text.md` (W3C Web Annotation
  `TextQuoteSelector` + `TextPositionSelector`; ATLAS.ti "quotation"). A quotation may run over a page break and
  across segments; one code, reading, memo or proposition carries a list of quotations. The program checks that
  the words are at that place and refuses a quotation that is not.
- Rewrite or remove what describes the earlier solution (segments of OCR variants with offsets into a scan's text),
  and document the pipeline in detail (T24).

## 2026-11-17 – Who drives the analysis

- Both: an agent in a chat (Claude Code or another agent that can run commands) and `mmo` itself calling models
  through the gateway. Both write the same proposals with quotations and pass the same checks of `mmo`; `mmo` is not
  tied to one agent. The agent first for interpretive work in dialogue (SKAD fine analysis); `mmo` with local models
  for repetitive work over many passages (T31).
- Changes of T24 approved, including the protected paths (`AGENTS.md` of both repositories, skill `ingest-sources`).

## 2026-11-19 – Free analysis on a fixed core (ADR 0013)

- Qualitative analysis must stay free, as the methods require. `mmo` guards integrity, not the method: quotations
  are the exact words, every record has author and time (model and prompt version for a model), a model's output is
  a proposal until the researcher accepts it, nothing disappears without a trace. The operations of qualitative
  analysis are a toolbox for every method; a method's vocabulary and phases are orientation; `model_role` binds
  models only. New methods are added by describing them.
- A quotation is required for codes and for everything a model proposes; a reflexive or methodological memo and an
  idea of the researcher may stand without one. The traceability rule of `AGENTS.md` in both repositories is changed
  accordingly (protected path, approved).
- Strictness is set by the researcher per study (`topic.yaml`), not by the method.
- Storage: text files in `topics/<slug>/analysis/` are the source of truth; the RDF graph, the graph browser and
  the export are views built from them.
- QDA programs: export to REFI-QDA (`.qdpx`) only for now; import later.
- A graph browser in the homelab goes into the plan now (T35).
- Choosing passages (T36): start structurally (introduction, first chapter, openings and endings of chapters)
  searched by the research questions; later rounds by reception (what reviews and the debate discuss) and by
  contrast. The key is set per study.
- The model's orientation reading covers the whole book, marked as first impressions, with a reflexive note.
- The researcher reads too, but the researcher's reading is never a condition for the model's reading.

## 2026-11-19 – Similarity search and graph procedures

- Semantic similarity (embeddings of segments) is a tool that finds candidates - for constant comparison, contrast
  and reception - never a relation of the analysis; a kept candidate gets its reason in a memo or a proposal. Index
  as a view, local multilingual model, recorded, a trigger of a reflexive note (T37).
- Classic RAG is not used for interpretation, which reads passages in sequence with their context.
- Narratives that relate without similar words are found through interpretation (codes of story elements, schemes,
  dimensions) and graph procedures over the confirmed analysis (T38).
