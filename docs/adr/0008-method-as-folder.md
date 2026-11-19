# 8. A method is a folder with its own research design

- Status: accepted (2026-11-14, owner)

## Context

Methods were single YAML files (`methods/*.yaml`) and the research design of all methods was one document
(`docs/research-design.md`). The owner wants each method described completely and exactly - its research design,
procedure, rules for agents, connected applications and literature - because the methods differ in how purpose,
questions and theory relate. A shared document invited merging and "deduplicating" the methods, which blurred the
approach (`docs/owner-notes.md`, 2026-11-14). `docs/` mixed how the environment is built with how it works.

## Decision

- One folder per method, `methods/<id>/`: `method.yaml` (read by agents and tests, with `status` and memo types per
  phase), `research-design.md`, `procedure.md`, `agent-rules.md`, `applications.md`, `sources.md`. A template in
  `methods/_template/`. Shared methodology is an overview in `methods/foundations.md` and never replaces a
  method's own text.
- SKAD is added as the method of the first study.
- `docs/` keeps the project memory at its root and gets `docs/environment/` for how the built environment works
  (`source-preparation.md`, `memos.md`), `docs/development.md` for the working rules, `docs/owner-notes.md` for the
  owner's notes.

## Consequences

- Texts repeat across methods on purpose; reviews do not count repetition as a defect.
- `tests/test_methods.py` checks every method folder; `tests/test_ontology.py` checks the schema.
- Links to `docs/source-preparation.md` moved to `docs/environment/source-preparation.md`, including the protected
  `AGENTS.md` and the `ingest-sources` skill (owner approved).
