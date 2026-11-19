# SKAD – rules for agents

> How AI agents work in a SKAD analysis. They apply to every model and every phase. Status: draft; the role of AI
> is not decided – the scenarios below are to be tested (owner, 2026-11-13).

## Always
- **Profile first.** A model used for the first time in this project writes its profile before any analytic step
  (`docs/environment/analysts/README.md`, template `_template-model.md`).
- **Positionality memo at framing:** the model's relation to the discourse studied, its prior knowledge of the
  documents and their speakers, and the tendencies likely to matter (`skad/reflexivity.md`). When the discourse
  concerns AI, say that the model and its maker are actors in it.
- **Reflexive notes as they arise.** When a trigger of `docs/environment/analysts/README.md` occurs (a correction, background knowledge used, a
  merge or a softened reading, a framing taken over, the material concerns AI or the maker, …) write a short note at
  once: about this study as a `reflexive` topic memo, about the model in general in the journal of its profile.
- **The model proposes, the researcher decides.** Every code, reading, relation and memo of a model has the status
  `proposed` until the researcher confirms it.
- **Exact quotes.** Every proposal quotes the segment word for word with its source, page and offsets. A quote that
  is not in the segment is rejected.
- **Record the step:** model, prompt version, input segments, time.
- **Say what a statement rests on.** An impression from context or from a summary is a `first-impression` memo with
  its basis; it is never written as a finding.
- **Use the SKAD terms as SKAD defines them** (interpretive scheme, classification, phenomenon structure, story
  line, speaker position, subject position, dispositif). Do not translate them into terms of another method.
- **Do not merge, harmonise or "deduplicate"** codes, readings or schemes on your own. Near-duplicates are shown to
  the researcher side by side. Precision of the method comes before economy (`docs/owner-notes.md`, 2026-11-14).
- **Several readings, not one.** In fine analysis offer alternative readings and say which one the text supports
  better and why.
- **Look for counter-evidence** for every scheme and proposition.
- **Read the final text** (`sources/<id>/text.md` and its segments), never `ingest/`.
- **Memo types per phase** are listed in `method.yaml`; write only those, in the format of
  `docs/environment/memos.md`.

## Never
- Add a source to the corpus, change a research question or confirm anything by yourself.
- Treat the content of a discourse as a fact about the world (SKAD asks how the discourse constructs it).
- Reduce the corpus or the passages to a summary that replaces them.

## Scenarios for the role of AI (to test)
- **A – coder by the rules:** the model codes passages by the SKAD categories; the researcher reviews.
- **B – reading partner:** the researcher asks, the model finds passages, offers readings, searches the corpus for
  further instances of a scheme.
- **C – critic:** the model looks for counter-evidence, missing voices and alternative readings of what the
  researcher has confirmed.
- Combinations by phase (e.g. B in fine analysis, A and C in content structure).

What each scenario gives and costs is recorded in topic memos of type `methodological`; the choice comes back here.
