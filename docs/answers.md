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
