# 15. Searching for context by the method and the research questions

- Status: accepted (2026-11-24, owner)

## Context

In test 9 the corpus grew only when the owner pushed for it ("are these all sales texts? how is the independence of
further information decided?"); the model then ran nine web searches without a plan. The study ended with the
finding "no independent reception found", and it cannot be seen how thoroughly it was looked for. Context is part of
the analysis in SKAD ("context belongs to the analysis"; corpus by theoretical sampling, minimal and maximal
contrast), and grounded theory samples the next data by its emerging categories; what counts as relevant context is
a matter of the method and the research questions, not of a search engine.

The owner (2026-11-24): a step of relevant context search must be there, derived from the research questions and the
method, and not only on the web; the types and the character of sources matter.

The owner's note of 2026-11-23 adds that a model may know the texts it studies from training; this must be on record
before it meets them.

## Decision

1. **The method says what relevant context is.** `methods/<id>/method.yaml` gets a description of context search:
   what it is derived from, which types of sources it looks for, and when it is repeated. SKAD: arenas of the
   discourse field, speaker positions, the dispositif (events, publisher, promotion), minimal and maximal contrast;
   repeated after content structure. Grounded theory: theoretical sampling by the emerging categories, repeated as
   they emerge. Thematic analysis: defining the data set by the question; small. `mmo` checks only that the search
   can be traced, never what a method asks (ADR 0013).
2. **A search plan comes first**, as a memo the researcher approves. For each research question: what context it
   needs; **which types and which character of sources, and why that matters** (review, interview, register entry,
   archive, readers' discussion, scholarly text, record of an event; the author's own, the author's circle,
   independent); where to look; how independence is judged; when to stop (saturation or a time box).
3. **Not only the web.** The plan knows library catalogues, the Czech web archive (Webarchiv NK), public registers,
   scholarly databases and the sources only the researcher can obtain (printed reviews, a recording of a panel, an
   interview with the author). What a model cannot reach it writes as a **request to the researcher**. Paid media
   archives (Newton, Anopress) are such requests; the owner has no access to them now.
4. **Every candidate carries its provenance**: the query, the place and the date it was found; the type and
   character of the source; who speaks in it and their relation to the object of the study (the author, the author's
   circle, an independent voice).
5. **Prior knowledge from training is marked apart.** Before the search a blind probe (a subagent, ADR 0014) is given
   only the name of the source and its author and says what it knows; this is recorded as the model's prior knowledge
   in a reflexive memo, later confirmed by a source or left marked as unconfirmed. The same probe is run for the
   critic's model.
6. **A cloud model searches the web only with the researcher's approval, per study**, recorded in `topic.yaml`.
7. **The search can return.** A gap found in a later phase or by the critic starts a new round of the same plan; the
   corpus may grow (SKAD, grounded theory).

## Consequences

- `method.yaml` of SKAD, GT, TA and the template get the context-search description; method versions are raised;
  `mmo method check` knows the field (T44).
- `source.yaml` gets provenance and relation fields; `mmo source check` reports a candidate without provenance (T44).
- `topic.yaml` records whether a cloud model may search the web (T44).
- The blind probe is a role of ADR 0014 (T45).
