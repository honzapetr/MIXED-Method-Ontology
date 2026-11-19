# 7. Code in `code/mmo/`, split into core and ingest

- Status: accepted (2026-11-12, owner chose the folder name)

## Context

The program lived in `src/mixed_method_ontology/`, the usual Python "src layout". In this project "sources" are
research sources (`topics/<slug>/sources/`), so a top-level `src/` reads as research data and confuses the owner.
Inside the package all modules sat side by side, so it was not visible which part is the core of the project and
which part brings new data in. An empty `data/` folder (left over from moving the first book's photos into its
topic) added to the confusion.

## Decision

- The package moves to `code/mmo/` and is called `mmo`, like its command. Hatchling builds it from there
  (`packages = ["code/mmo"]`); the folder name `code` is not a Python package, so it does not clash with the
  standard library module of the same name.
- Inside, by function:
  - `core/` - the project core: topic, sources and their layout; later the graph, analysis runs and review.
  - `ingest/` - bringing new data in: OCR backends (`ingest/ocr/`), printed page numbers, reading order,
    segmentation, OCR comparison.
  - `cli.py`, `__main__.py`, `config.py` at the top: the command and settings shared by both.
- Tests mirror it: `tests/core/`, `tests/ingest/`.
- Research data lives only in `topics/`; there is no other data folder.

## Consequences

The top level reads: `code/` program, `topics/` research data, `methods/` and `ontology/` definitions, `docs/`
project memory, `tests/`, `tools/`. Imports change from `mixed_method_ontology.*` to `mmo.*`; files move with
`git mv` so history follows them. `AGENTS.md` (protected) names the new path.
