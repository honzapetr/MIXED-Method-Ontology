# The analysis store and the free toolbox

> How the analysis of a study is stored and changed: `code/mmo/analysis/store.py`, commands `mmo code`,
> `mmo relation`, `mmo memo`, `mmo analysis check` (T32). Decisions: ADR 0013 (free analysis on a fixed core, with
> its amendment), ADR 0012 (quotations). For the builder; the analyst's manual is `docs/analysis.md` of the research
> environment.

## The principle

`mmo` checks **integrity**, never the method:

| Checked (refused or reported) | Never checked |
| :--- | :--- |
| a quotation is the exact words of `text.md` (T26) | which codes, labels and types exist |
| every record has an author and a time; a model also names its prompt version | which relation types are used |
| a reference points to something that exists | the order of phases, going back, merging, splitting |
| nothing disappears: withdrawn, merged and split items stay with their status | how many codes, how long a quotation |
| edits by hand are noticed and recorded | whether a method's vocabulary is followed |

A model's record is a **proposal** (`status: proposed`) until the researcher decides (T29); the researcher's own
records are written `accepted` and need no decision.

## Layout

```
topics/<slug>/
  analysis/                 # source of truth of the analysis, in git, written through mmo
    codebook.yaml           # codes, sorted by id
    codings.jsonl           # a code applied to a quotation, one per line, sorted by id
    relations.yaml          # relations between any two items, sorted by id
    history.jsonl           # every operation, appended, with the state (SHA-256) of the three files after it
  memos/<id>.md             # memos stay here (format: docs/memos.md of the research environment)
  positions/<analyst>.md    # positions stay here
```

### Records (field names = slots of the ontology)

```yaml
# codebook.yaml – ontology Code (skos:Concept)
codes:
- id: spasa-skrze-ai          # from the first label; stays when the label changes
  label: Spása skrze AI
  code_type: interpretive_scheme   # any word; SKAD's list only orients
  method: skad                # optional; a study may use several methods
  definition: ...
  broader: spasa              # optional: a broader code
  status: accepted            # proposed | accepted | edited | rejected | superseded | withdrawn
  superseded_by: [..]         # after a merge or split
  author: owner
  created: '2026-11-19T10:00:00+00:00'
  generated_by: {model: claude-opus-5-5, prompt_version: chat@2026-11-19}   # only for a model
```

```json
// codings.jsonl – ontology Annotation (oa:Annotation): body = the code, target = the quotation
{"id": "cd-0001", "body": "spasa-skrze-ai", "target": {"source": "kniha", "start": 70674, "end": 70716,
 "pages": [57], "scans": [41], "exact": "…", "prefix": "…", "suffix": "…", "text_sha256": "…"},
 "method": "skad", "note": "…", "status": "accepted", "author": "owner", "created": "…", "was": ["prorok"]}
```

```yaml
# relations.yaml – ontology Relation
relations:
- id: rel-0001
  relation_type: story_link     # any word
  subject: code:spasa-skrze-ai  # code:, coding:, relation:, memo:, source:
  object: code:vyvolenost
  evidence: [<quotation>, ...]  # optional
  description: ...
  status: accepted
  author: owner
  created: ...
```

`history.jsonl` – one line per operation: `at`, `op` (`add-code`, `apply-code`, `rename-code`, `merge-codes`,
`split-code`, `recode`, `withdraw`, `relate`, `memo`, `update-quotations`, `hand-edit`), `author` (and
`generated_by` for a model), the ids involved, a `reason` if given, and `state`: the SHA-256 of the three files.

## Commands

```bash
uv run mmo code add <topic> "<label>" [--type T] [--method M] [--definition D] [--broader ID] --by X
uv run mmo code apply <topic> "<code id or label>" <source> "<exact words>" [--page n | --segment id] --by X
uv run mmo code rename <topic> <code id> "<new label>" --by X
uv run mmo code merge <topic> <into> <code> [<code> ...] [--reason R] --by X
uv run mmo code split <topic> <code> "<label>" "<label>" [...] [--reason R] --by X   # codings wait for recode
uv run mmo code recode <topic> <coding id> "<code id or label>" --by X
uv run mmo code withdraw <topic> coding:<id>|code:<id>|relation:<id> [--reason R] --by X
uv run mmo code list <topic>
uv run mmo relation add <topic> <subject ref> <type> <object ref> [--evidence SOURCE[@PAGE] "WORDS"]... --by X
uv run mmo memo add <topic> --type T --title "..." [--text "..." | --file F] [--about REF]...
                    [--quote SOURCE[@PAGE] "WORDS"]... [--method M] [--phase P] --by X
uv run mmo analysis check <topic> [--record --by X]
```

- `--by` is the researcher's id or the exact model id. If `analysts/<id>.md` of the environment is a model profile,
  the author is a model and must give `--prompt-version` (the skill or prompt and its version; `chat@<date>` for a
  dialogue with the researcher).
- `code apply` with a label that is not in the codebook adds the code - coding is free; a quotation that is not in
  `text.md` is refused (T26).
- `memo add` writes `memos/<date>-<title>.md` with `author`, `created`, `status` (`proposed` for a model, `draft`
  for a person), `about`, `basis.quotations`, `generated_by`; the memo is recorded in the history.

## Checks

- `mmo analysis check <topic>`: every record has an author and a time; codes, codings and relations point to things
  that exist; every coding's quotation is still at its place in `text.md`; the files are as the last operation left
  them. An edit by hand is allowed - `--record --by <who>` writes it into the history. Exit 1 while anything is left.
- `mmo quote check <topic> [--update]` (T26) also finds the quotations of `codings.jsonl` and `relations.yaml`; an
  update of the store is recorded (`update-quotations`), so it is not taken for an edit by hand.

## Guard

`mmo-guard` (the analyst's hooks in the research environment):
- a model may read `analysis/` but writes it only through `mmo` (Write and Edit, and shell writes such as `>`,
  `sed -i`, `tee`, `cp`, `mv`, `rm`, are denied there); memos and positions stay free Markdown;
- `mmo quote|code|relation|memo|analysis` on a study is closed exactly when reading its `text.md` is;
- a model writes only under its own id: `--by <someone else>` is denied.

## Later

- T29 reviews proposals (accept, edit, reject) and limits what a model may propose per phase.
- T33 adds `mmo phase` and the study's settings (`analysis:` in `topic.yaml`), e.g. asking for a memo when a type
  outside the method's vocabulary is used.
- T30 builds the RDF graph from these files; T34 exports them to REFI-QDA.
