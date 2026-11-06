# Brief – MIXED-Method-Ontology

> Written with the owner. Agents change it only when the owner asks. The original brief (Czech) is in the owner's
> project files; this is its working summary.

## Goal

Infrastructure for qualitative and mixed-methods research. Sources of a research topic (books, interviews, field
notes, documents, survey data) are turned semi-automatically into codes, categories, themes and relations between
meanings. The result is a versioned knowledge graph that both the researcher and AI agents can work with.

The goal is the infrastructure, not the analysis of one particular book.

## Principles

- **The model proposes, the human confirms.** Every code, category, theme and relation has a status (proposed,
  confirmed, rejected) and an author.
- **Traceability.** Every statement in the graph leads back to an exact span of a source (page, paragraph, quote).
- **Methodologies as modules.** The same source can be analysed with several methods and the results compared.
  Methods can be added without changing the core.
- **Open standards** instead of a custom format where possible: SKOS, W3C Web Annotation, PROV-O, DDI-CDI,
  REFI-QDA (`.qdpx`).
- **A topic is a living project.** A topic has several research questions and goals defined by the researcher
  together with an agent. It stays usable after the analysis: you can query it, look at it from another angle, add
  material and update the graph. Versions work like git branches.
- **Local first.** Models run on the owner's homelab through the LLM gateway; cloud models are an option, not a
  requirement.

## Scope (first phase)

- Repository set up for agentic development (Claude Code, Antigravity CLI, Project Lab).
- Folder structure for topics, sources, intermediate results and the ontology.
- Ingest of scanned book pages: OCR with interchangeable backends (local Tesseract, vision models behind the
  OpenAI-compatible gateway) so that variants can be tested and compared.
- Splitting OCR text into segments with exact positions.
- Draft of the core ontology (LinkML) and of the first method definitions (grounded theory, thematic analysis).

## Out of scope (for now)

- Choosing the final models for analysis – the owner will test variants first.
- The analysis engine, the graph store, review CLI, exports (SKOS, `.qdpx`, report) and the read-only MCP server.
  They follow once ingest works on real scans.
- A user interface.

## Constraints

- Stack: Python 3.12+, uv, local files; RDF graph later (Oxigraph is the candidate).
- Runs in the Project Lab and on the owner's computer; homelab services are reachable only from the LAN or over
  WireGuard.
- Source scans are not committed to git (size, copyright); only manifests with hashes are.
