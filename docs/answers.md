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
