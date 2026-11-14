# Grounded theory – rules for agents

> How AI agents work in a grounded-theory analysis. Status: draft; the role of AI is not decided – scenarios to
> test.

## Always
- **Profile first.** A model used for the first time in this project writes its profile before any analytic step
  (`docs/environment/analysts/README.md`, template `_template-model.md`).
- **Declare prior knowledge before open coding:** what the model already knows about the field and the material,
  and which ready-made concepts it is likely to bring – the risk of forcing (`grounded-theory/reflexivity.md`).
- **Reflexive notes as they arise.** When a trigger of `docs/environment/analysts/README.md` occurs (a correction, background knowledge used, a
  code named from literature rather than from the data, a merge, a framing taken over, …) write a short note at
  once: about this study as a `reflexive` topic memo, about the model in general in the journal of its profile.
- **The model proposes, the researcher decides.** Every code, category, relation and memo of a model is `proposed`
  until the researcher confirms it.
- **Exact quotes** with source, page and offsets; a quote that is not in the segment is rejected.
- **Record the step:** model, prompt version, input segments, time.
- **Stay close to the data** in open coding: name what happens, prefer the words of the data (in-vivo) and
  process codes; do not apply categories from theory.
- **Use the terms of the GT version the topic follows** (Straussian or constructivist); do not mix them.
- **Do not merge or "deduplicate"** codes on your own; constant comparison is the researcher's decision. Show
  similar codes side by side (`docs/owner-notes.md`, 2026-11-14).
- **Compare constantly:** with every proposal, name the segments it was compared with.
- **Memo types per phase** as in `method.yaml`, format `docs/environment/memos.md`.

## Never
- Choose the next data (theoretical sampling) or the core category by yourself.
- Declare saturation.

## Scenarios for the role of AI (to test)
- **A – open coder:** proposes codes per segment; the researcher reviews.
- **B – comparison partner:** for a code or category, finds similar and contrasting segments across the data.
- **C – critic:** looks for negative cases and gaps in the categories.
