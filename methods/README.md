# Methods

One folder per analytical method. Everything about a method is in its folder: what it is for, how it links purpose,
questions and theory, its procedure, the rules for agents, the applications it works with and its literature. A
new method needs a new folder only; the core does not change.

**Precision before economy.** Each method is described completely and in its own terms, even where the same
information appears in another method. Do not merge, shorten or "deduplicate" method texts across folders
(`docs/owner-notes.md`, 2026-11-14). `foundations.md` is a shared overview for comparison; it never replaces a
method's own text.

## A method folder

| File | Content |
| :--- | :--- |
| `method.yaml` | the part agents and tests read: `id` (= folder name), `name`, `status`, `references`, `summary`, `research_design` (short form: `purpose`, `questions`, `prior_theory`, `reasoning`, `theory_output`), `code_types`, `relation_types`, `phases`, `practices`, `conclusions` |
| `research-design.md` | for this method: what it is for, purpose and goals, how research questions arise, role of prior theory, reasoning, unit of analysis, theory output, quality criteria, working with the result |
| `procedure.md` | the phases step by step: what the researcher does, what the model does, the gate |
| `agent-rules.md` | rules for AI agents in this method: always, never, scenarios for the role of AI to test |
| `applications.md` | connected applications (QDA tools, exports): use, exchange, status |
| `sources.md` | literature with links and reading status (`found`, `summary`, `read`) |

A phase in `method.yaml` has `id`, `goal`, `input`, `output`, `memos` (memo types it expects,
`docs/environment/memos.md`), optional `allowed_relations`, `model_role` and `human_gate`.

`status`: `draft` (being written), `testing` (used on a study), `stable` (the owner confirmed it).

## Methods

| Folder | Method | Status |
| :--- | :--- | :--- |
| `skad/` | Sociology of Knowledge Approach to Discourse (Keller) – the method of the first study, `topics/nazi-v-ai-dobe/` | draft |
| `grounded-theory/` | Grounded theory (classic, Straussian, constructivist) | draft |
| `thematic-analysis/` | Reflexive thematic analysis (Braun & Clarke) | draft |

## Adding a method

1. Copy `_template/` to `methods/<id>/` and set `id` to the folder name, `status: draft`.
2. Write `sources.md` first, then `research-design.md`, `procedure.md`, `agent-rules.md`, `applications.md`, and
   `method.yaml` last (it is the short form of the texts).
3. `uv run pytest tests/test_methods.py` checks the folder.

Planned: CDA (Fairclough), Mayring's qualitative content analysis, ethnography, narrative analysis, mixed-methods
designs, and non-LLM methods (embedding clusters, topic models).
