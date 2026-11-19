# 13. Free qualitative analysis on a fixed core of integrity

- Status: accepted (2026-11-19, owner)

## Context

After T24-T25 the final text, its segments and quotations are settled; the analytic layer of `mmo` is next (T26
onwards). A first proposal made `mmo` an "analysis engine" that would refuse code types a method does not list and
let only confirmed items pass to the next phase. The owner objected: qualitative analysis must stay free, as the
methods themselves require. Codes emerge from the data (grounded theory, reflexive thematic analysis), codebooks
evolve, phases are recursive (Braun & Clarke; Keller for SKAD), and the researcher renames, merges and splits codes
and goes back. A program that enforces a method turns an interpretive approach into a procedure.

The proposal mixed two concerns:

- **Integrity** - the analysis can be traced to the words of the text and to who made each step; a model cannot
  invent or alter a quotation, and its output does not become analysis by itself. This guards against the errors of
  AI and is the audit trail of qualitative research (Lincoln & Guba).
- **Framing** - which codes, relations and steps are allowed. This belongs to the researcher, guided by the method.

The operations of qualitative analysis are shared across methods and tools (ATLAS.ti, MAXQDA, NVivo, QualCoder;
Saldaña's coding manual): reading and annotating, choosing passages (quotations), coding in first and second cycle,
renaming, merging and splitting codes, an evolving codebook, memos attached to anything, constant comparison and
queries, categories, themes and relations, maps and networks, document groups, cases and attributes, theoretical
sampling, reflexivity, team agreement or consensus, writing up with quotations. Methods differ in which operations
they stress, their vocabulary and the order they suggest - not in having different operations.

## Decision

Three layers.

1. **A fixed core of integrity** - always, not configurable:
   - a quotation is the exact words at their place in `text.md` (ADR 0012), checked by `mmo`;
   - every record carries its author and time, and for a model also the model and the prompt version;
   - what a model writes is a *proposal* until the researcher accepts, edits or rejects it;
   - nothing disappears without a trace: renames, merges, splits and moves between phases are recorded, and git
     keeps the history.
2. **A free toolbox** - `mmo` offers the operations above to every method: quote, annotate, code with any code,
   rename, merge, split, write a memo about anything, relate anything, group documents, compare and query. The tools
   check only the core, never the method.
3. **The method as orientation** - `methods/<id>/method.yaml` is read by `mmo`, but as guidance:
   - `code_types` and `relation_types` are a suggested vocabulary; a type of the researcher's own is allowed (at
     most `mmo` asks for a memo on why it arose, if the study wants that);
   - `phases` are a map: where the researcher is, what a phase usually needs; moving between phases is free and
     recorded;
   - `model_role` is a rule, **for models only**: what a model may propose in a phase and with which prompt;
   - `practices` are reminders (e.g. a merge of codes without a memo).

**Strictness is set by the researcher per study**, in `topic.yaml` (`analysis:`), not by the method: e.g. the
codebook (`emergent`, `evolving`, `fixed`), own types (`allowed`, `ask_memo`), phases (`orientation`, `sequence`), in
which phases a model may propose and whether it must offer alternative readings, team work (`none`, `consensus`,
`agreement`), where a quotation is required. The exact keys are set in the task that builds them.

**Where a quotation is required.** Codes (every coding points to a quotation) and everything a model proposes. A
reflexive or methodological memo and an idea of the researcher may stand without one; they still carry author and
time.

**Storage.** The source of truth is text files in git, `topics/<slug>/analysis/` (codebook, codings, memos,
relations, proposals, history; layout set in the task that builds it). Everything else is a view that can be built
again from them:

- an RDF graph (Oxigraph, in `mmo`) for queries, by the agent and the researcher;
- a graph browser in the homelab (GraphDB Free or Apache Jena Fuseki, chosen in its task) to look at the network of
  codes, quotations and memos;
- an export to REFI-QDA (`.qdpx`) for QualCoder, ATLAS.ti, MAXQDA and NVivo. Export only for now; an import of the
  researcher's coding back into `mmo` is a later task of its own.

**Adding a method** is a description, not code: a folder from `methods/_template/` with its texts, vocabulary, map of
phases and prompts for models, checked by `mmo method check`. A method that needs an operation the toolbox lacks
(e.g. situational maps) adds it to the toolbox as a general operation that other methods may use too.

## Consequences

- The traceability rule in `AGENTS.md` of both repositories is made precise: quotations are required for codes and
  for everything a model proposes; author and time for every record (owner approved, protected path).
- The plan's Analysis section is rewritten: T26 (quotations) belongs to the core and is unchanged; the toolbox, the
  method as orientation, study settings, the export and the graph browser become tasks; proposals (T29), the graph
  (T30) and model backends (T31) build on them.
- `mmo` is tested with a toy method as well as with SKAD, GT and TA, so no method is hard-wired.
- One study may use several methods (`methods:` in `topic.yaml`); each record names the method it belongs to; the
  graph is shared because method types map onto the general classes of the ontology (`Code`, `Relation`, `Memo`,
  `Quotation`).
- The REFI-QDA export loses what the standard cannot carry (status of a proposal, model, method types); method types
  are mapped to code groups or colours.

## Amendment (2026-11-19, owner)

A review of the plan as a whole found places where earlier texts contradicted this decision; resolved:

- **Statuses of a proposal:** `proposed`, `accepted`, `edited` (accepted with changes, kept to see what came from
  whom), `rejected` (with a reason), `superseded` (replaced by a rename, merge or split). The ontology's
  `ProposalStatus` and `docs/spec.md` use them.
- **Memos and positions stay where they are**, `topics/<slug>/memos/` and `positions/`; `analysis/` holds the
  codebook, codings, relations, proposals and the history.
- **Phases:** the researcher sets where the study is (`mmo phase`, T33) and moves freely; the phase only limits what
  a model may propose. `docs/spec.md` no longer says that a phase starts from confirmed state only.
- **The method's "gates"** are renamed: `researcher_decides` in `method.yaml`, "Researcher decides:" in the
  procedures, "decision of the researcher" in the reflexivity texts - what the researcher decides, never a lock.
- **Graph:** a view, not files of record; acceptance is the status of a proposal, not a merge of git branches.
- **Machine indexes** (graph, similarity) are kept out of git and never carried between test copies.
- **Hand edits** of `analysis/` by the researcher are allowed; `mmo` notices them and records them in the history.
