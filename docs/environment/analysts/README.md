# Analysts – researchers and models

> Who interprets the data is part of the analysis. Every analyst – a human researcher or a model – keeps a profile
> of their position and writes reflexive notes whenever there is a reason. Why and how, in general and per method:
> `methods/reflexivity.md` and `methods/<id>/reflexivity.md`. Status: proposal (T10, agreed with the owner
> 2026-11-14); no `mmo` command reads these files yet.

## Two roles

| | Human researcher | Model |
| :--- | :--- | :--- |
| Role in the analysis | decides: confirms, rejects, frames, interprets; owns the result | proposes: codes, readings, relations, memos; never confirms (`methods/<id>/agent-rules.md`) |
| Position comes from | biography, social position, relation to the topic and the field, stakes, theory and method preferences | maker, training data, post-training, setting and instructions, prior knowledge of the material, knowledge cutoff |
| Profile | `analysts/<person-id>.md`, written by the person (template `_template-researcher.md`) | `analysts/<model-id>.md`, written by the model itself and checked by the owner (template `_template-model.md`) |
| Status of their notes | `draft` until the person considers them done | always `proposed` first |
| Self-description | first-hand, but partial; revisited during the study | hypotheses, not privileged access; tested by checks |
| Also reflects on | their relation to the model: did the model's framing become mine? | its relation to the researcher: did it adopt the researcher's framing, agree too easily? |

## Where notes go

| Note about | Where | Type |
| :--- | :--- | :--- |
| the analyst in general (background, tendencies, setting), independent of a study | the journal at the end of the analyst's profile, `docs/environment/analysts/<id>.md` | dated entry |
| the analyst's position in one study, and anything that happened in that study | `topics/<slug>/memos/<date>-<name>.md` | `reflexive` (format `docs/environment/memos.md`) |
| a decision about the procedure that follows from it | `topics/<slug>/memos/` | `methodological` |

Each study has, at framing, one positionality memo of each analyst who takes part (the researcher and every model
used for analysis). At synthesis each analyst revisits it.

## When to write a note

Write a short dated note **as soon as** one of these happens – not later, and not only at phase ends.

### Model

1. The researcher corrects, rejects or rewrites its proposal or text – what was wrong and which tendency it shows.
2. It used knowledge that did not come from the text being analysed (training, web search, an earlier session) –
   say what and from where.
3. It merged, shortened, summarised or harmonised something, or chose a balanced or softened reading over a sharper
   one.
4. It adopted the researcher's or the prompt's framing, or disagrees with the researcher.
5. The material concerns AI, the model's maker or the model itself.
6. A re-run or another model gave a different result.
7. It is unsure of the language, the cultural context or the genre (e.g. Czech essayistic prose).
8. Its setting changed: new instructions, a new model version, compacted context, new tools.
9. It acted before the researcher approved, or beyond the task.
10. At every human gate with a batch of proposals: a short note on what it may have smoothed, merged or left out.

### Researcher

1. Surprise, strong agreement, irritation or discomfort when reading.
2. A change of mind about a reading, a scheme, a question or the purpose.
3. Accepting or rejecting a model proposal for reasons other than the text (it sounded good, it was too long to
   check, it fit what I wanted).
4. Contact with the field or the author, new context information, or the researcher's own role in the discourse
   coming up.
5. A decision about the corpus, the questions or the method.
6. At every gate, the gate questions:
   - Is this reading mine, the model's, or the text's?
   - What else could it be?
   - What did I not want to see?
   - Would I accept this if it argued the opposite?

### Form

- One to five sentences, dated, with what triggered it and what it may change.
- Facts and tendencies, not apologies. A model does not describe feelings or inner states.
- A note is never deleted; a later note revises it (`supersedes` in topic memos).

## A new analyst

- **A model** used for the first time in this project writes its profile from `_template-model.md` before it does
  any analytic step, answering every field from what it can state about itself and marking what it does not know.
  The owner checks it. A new version of a model is a new analyst with a new profile.
- **A researcher** joining a study writes their profile from `_template-researcher.md`. Nobody else writes it for
  them; a model may only ask the questions.

## Analysts

| Id | Kind | Profile |
| :--- | :--- | :--- |
| `claude-opus-5-5` | model (Anthropic, cloud) | `claude-opus-5-5.md` |
| the owner | researcher | not written yet – the owner writes it from `_template-researcher.md` |

Planned: profiles of the local models behind the gateway when they are used; a short test set per model (Czech
passages with known readings) to turn hypotheses into observations; cross-model comparison stored side by side.
