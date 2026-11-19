# 9. Reflexivity of researchers and models

- Status: accepted (2026-11-14, owner)

## Context

Qualitative analysis is interpretation, and the position of the interpreter shapes it. In this environment models
take part in interpretation too. A model has no biography, but it has a position: its maker, training data,
post-training, setting and prior knowledge. The first study (`topics/nazi-v-ai-dobe/`) is about AI, so the model
used to build the environment is itself inside the discourse it would analyse. Models will change over time
(newer versions, local models). The owner wants reflexivity recorded for both kinds of analyst, with every model
writing notes about itself and writing them whenever there is a reason.

## Decision

- `methods/reflexivity.md`: shared overview (positionality vs. reflexivity, forms, techniques, the model as a
  positioned analyst, sources). Each method has its own `reflexivity.md` – the seventh file of a method folder.
- `docs/environment/analysts/`: one profile per analyst – a human researcher (written by the person) or a model
  version (written by the model itself, checked by the owner) – with a journal, templates, the triggers for writing
  a reflexive note and the gate questions for the researcher.
- In a study each analyst writes a positionality memo at framing and reflexive notes as triggers occur
  (`topics/<slug>/memos/`, type `reflexive`); notes about an analyst in general go to the profile's journal.
- A new model version is a new analyst with a new profile.
- `AGENTS.md` gets a short rule pointing to the analysts' README (protected path, owner asked for the instructions).

## Consequences

- `tests/test_methods.py` requires `reflexivity.md` in every method folder.
- A model's self-description is a hypothesis; checks (cross-model comparison, re-runs, a critic model, the
  researcher's review) test it.
- The ontology will need an `Analyst` (PROV-O agent) linked to its profile, memos and steps (`docs/spec.md`).
