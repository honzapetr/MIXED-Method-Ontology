# Memos

> How memos work in the environment. Status: **proposal** (T8) – the format is used by the first memo of
> `topics/nazi-v-ai-dobe/`; no `mmo` command reads it yet. Why memos matter methodologically:
> `methods/foundations.md`; which memos each phase expects: `memos` in `methods/<id>/method.yaml`.

## Where memos live

The concrete analysis keeps its memos in its topic:
- `topics/<slug>/memos/<id>.md` – memos of the topic (all types);
- `topics/<slug>/sources/<id>/notes.md` – the researcher's context memo of one source.

## Format

A Markdown file with a YAML header:

| Field | Meaning |
| :--- | :--- |
| `id` | `<date>-<short-name>`, the file name |
| `type` | `context` (why a source is here), `first-impression`, `familiarisation`, `reflexive` (the position of the researcher or of a model, and notes written when a trigger occurs – `docs/environment/analysts/README.md`), `analytic` (about codes, categories, relations), `theoretical` (towards propositions), `methodological` (a decision about the procedure), `steering` (instructions for the next step of a model) |
| `author` | a person or the exact model id (e.g. `claude-opus-5-5`); every author has a profile in `docs/environment/analysts/` |
| `created` | date |
| `status` | `draft` (person) or `proposed` / `confirmed` / `rejected` (model memos are always proposed first) |
| `about` | what the memo is about: the topic, source ids, segment ids, concept ids, question ids |
| `basis` | what it rests on: segments, sources, or `how` it came about (e.g. only web summaries) – an impression says so |
| `method`, `phase` | the method and phase it belongs to |
| `supersedes` | an earlier memo it revises |

Example: `topics/nazi-v-ai-dobe/memos/2026-11-13-author-positions.md`.

## What makes memos work (planned)

- Agents read memos as context: steering memos are passed to the next step; first impressions become checks to run
  against the text (confirmed, revised or dropped with a reason).
- Every memo is listed by what it is about, so a source, a question or a concept shows its memos.
- In the graph a memo is a `Memo` (PROV-O: who, when, from what), linked to its `about` and `basis`.
- A check (`mmo source check`, later `mmo memo check`) reports a memo pointing to an unknown source or segment.
