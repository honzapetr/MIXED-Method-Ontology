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

## The method as orientation, strictness per study (T33)

`code/mmo/analysis/method.py`, `status.py`; commands `mmo method check`, `mmo phase`, `mmo status`.

- **Method schema** (`check_method`, `mmo method check [ids] [--methods DIR]`): the keys of `methods/README.md` of
  the research environment, a `version`, every phase with `goal`, `input`, `output`, `memos`, `model_role`,
  `researcher_decides` (`human_gate` is reported as renamed), `allowed_relations` among `relation_types`, known memo
  types, and an optional versioned `prompt` file per phase. `mmo` holds no code for any method.
- **Study settings** (`study_settings`): `analysis:` of `topic.yaml` merged over free defaults; unknown keys or
  values are refused. Kept by the toolbox: `codebook: fixed` refuses new codes; `phases: sequence` allows only the
  next phase or going back; `model.phases` refuses a model's writes outside the listed phases (in `author_of`);
  `quotation_required.memos` refuses those memo types without `--quote`; `own_types: ask_memo` prints a reminder
  after `code add` / `relation add` and lists such types in `mmo status`. `model.alternatives` and `team` are stored
  for T29 and later.
- **Phase**: `mmo phase <topic> <phase> [--method]` - the researcher only (refused for a model in `mmo` and by the
  guard); recorded as `op: phase` with `method`, `phase`, `previous` in `history.jsonl`; the current phase of each
  method is the last such event.
- **Status**: `mmo status <topic>` - every method of the study with its version and map of phases (`->` marks where
  the study is), the model's role and the researcher's decisions there, the memo types the phase usually has, what
  was made, proposals waiting, changed settings, reminders (merges or splits without a reason, own types if asked,
  the methods' practices). Orientation only; nothing there is a condition.

## Proposals and the review (T29)

`code/mmo/analysis/review.py`; commands `mmo review list|accept|edit|reject`.

- **A proposal is a record, not a file of its own:** a code, coding, relation or memo written by a model has
  `status: proposed` in the same file. No separate `analysis/proposals/` folder - accepting it changes its status in
  place, so the accepted record keeps its provenance (`author`, `generated_by`) without being copied.
- **Decisions:** `accepted`; `edited` with `decided.changes` (`{field: [old, new]}`; a coding's code by `--code`);
  `rejected` with a required reason. `decided: {verdict, by, at, reason | note, changes}` on the record, `op:
  review` in the history with the cascade. Accepting a coding accepts its proposed code; rejecting a code rejects its
  proposed codings and is refused while codings the researcher holds use it. Memos are decided in their front
  matter; an edit of a memo's text is made by hand and marked with `--note`.
- **Only a person decides** (`decide` refuses a model; the guard denies `mmo review` other than `list` to a model).
- **Many at once** (T47): `select(topic, refs, kind, author, role, run, phase)` - the waiting proposals matching every
  filter; the phase is the one the study was in when the record was written (`phases_when_written()`: the history
  event that wrote it - `memo`, `add-code`, `apply-code`, `relate` - against the `phase` events before it; a memo's
  own `phase` field counts too). `decide_many()` - accept or reject only; each is `decide()` with the same reason or
  note and one `batch` id (`batch-<time>`) in its `op: review` event; a proposal no longer waiting (decided in the
  cascade of an earlier one) is skipped; an error is reported and the rest go on. CLI: `mmo review list|accept|reject
  [refs] [--kind] [--author] [--role] [--from-run] [--phase] [--all] [--dry-run]` (`--from-run`, because `--run` is
  the author's run); accept and reject without a reference or filter need `--all`.
- **What a model may propose** (`Store.may_propose`): `model_proposes` of the current phase of each of the study's
  methods (a phase without it, or a method without a phase set, does not limit); one method allowing the kind is
  enough. A model may not rename, merge, split or recode (`researcher_only`) and withdraws only its own waiting
  proposals. `analysis.model.alternatives: true` makes a model's analytic memo need `--alternative`.
- SKAD's phases have `model_proposes` taken from their `model_role` (version `2026-11-19.2`); GT and TA have none
  yet, so their phases do not limit what a model proposes.

## Later

- T30 builds the RDF graph from these files; T34 exports them to REFI-QDA.

## Roles and runs of subagents (T43, ADR 0014)

`code/mmo/analysis/roles.py`. A role is a file of the research environment, `.agents/roles/<role>.md`, with front
matter `name`, `description`, `version`, `writes` (`code`, `coding`, `relation`, `memo`, or `none`); its body is
the role's prompt, its prompt version `role/<role>@<version>`. `tools/agents_sync.py` of the environment copies the
roles to `.claude/agents/` as Claude Code subagents.

```bash
uv run mmo role list [--env <environment>]          # roles, prompt versions, what they write; problems of the files
uv run mmo run start <topic> --role R --input "..." [--input ...] [--analyst <model>] [--note N] --by X [--prompt-version V]
uv run mmo run close <topic> <run> --by X [--note N]   # the work came back; the web closes with the run (T48)
uv run mmo run list <topic>                         # each run, its input, what it wrote, open or closed, web
uv run mmo memo add <topic> ... --by <model> --run run-0001   # any write command takes --run
```

- `run start` (the lead or the researcher) refuses a role the analyst's position does not list (`roles:` in the front
  matter of `positions/<model>.md`), an analyst without a model profile, a run started from inside a run, and a run
  without input. It is an event of `history.jsonl`: `op: run`, `run`, `analyst`, `role`, `prompt_version`, `input`.
- `--run` makes the author the run's analyst in its role: the prompt version comes from the run (another one is
  refused), `generated_by` gets `role` and `run`, and the role's `writes` limits what may be written (on top of
  `model_proposes` of the phase). An instance finder (`coding, memo`) can code only with existing codes, because a
  new label would add a code.
- `run close` (the lead or the researcher, not a subagent) is `op: run-closed` (`run`, `analyst`, `note`); a run is
  closed once. `closed_runs()` in `roles.py`.
- `run list` finds what a run wrote by `generated_by.run` of codes, codings, relations and memos.
- `analysis check` reports a record whose run is not in the history, or whose author or role differ from the run.
- `mmo-guard` closes `mmo run` on a closed study like the other study commands.
- Phase prompts (T39): `prompt` of a phase in `method.yaml` (versioned file); `mmo status` shows it with the
  `--prompt-version <method>/<phase>@<version>` to use. Method-specific role prompts: optional `roles:` of
  `method.yaml` (role -> file with a `version:` line), checked by `mmo method check`.

## Outline and coverage (T36, ADR 0014)

`code/mmo/analysis/outline.py`, `mmo outline`, `mmo coverage add|list` (spec, "Outline, coverage and the choice of
passages").

- `outline(topic, source)` -> `Outline(parts, chapters, problems, text_sha256)`: parts from `HEADING` after the front
  matter plus `outline.parts` of `source.yaml`; pages and segment ids from `segments.jsonl` (a segment belongs to the
  part where it starts; headings are segments too). `resolve()` turns part ids, chapter ids and ranges into part ids.
- `add_coverage()` saves `op: coverage`; `coverage()` joins the declarations with `quoted` from the quotations of
  codings and memos (not rejected or withdrawn); `best()` ranks whole > passages > map > quoted; `summary()` gives
  the lines of `mmo status`.
- Settings: `passage_keys` in `DEFAULTS` of `method.py`; memo type `passage-choice`; `source.yaml` field `outline`.

## Context search (T44, ADR 0015)

`code/mmo/analysis/context.py` (plans, rounds, requests, the summary for `mmo status`), `code/mmo/core/provenance.py`
(`provenance` of `source.yaml`), `mmo context round|request|close|list`, `mmo source provenance`.

- Memo type `search-plan`. `plans()` reads the memos of that type; approved = `accepted` or `edited`, or written by
  the researcher (no `generated_by`) and not rejected or withdrawn.
- History events: `search-round` (`plan`, `round`, `reason`, `gaps`), `request` (`request`, `what`, `why`, `where`,
  `question`, `plan`), `request-closed` (`request`, `outcome`, `sources`). A round needs an approved plan; a second
  round of a plan needs `--gap`. A request's `--question` must be a question id of `topic.yaml`. Only the researcher
  closes a request.
- `analysis.web_search` (a list of model ids) is a study setting; `start_run(..., web=True)` records `web` for every
  run (`web=False` for a run that never searches, the blind probe).
- `mmo-guard` (`check_web`, `open_web_runs`, T48) allows `WebSearch` and `WebFetch` only while some
  `topics/<slug>/analysis/history.jsonl` has an open run (`op: run`, `web: true`, no `run-closed`) of the model (or,
  when the hook does not know the model, of any model) that `analysis.web_search` of that study still lists;
  `MMO_STUDY` narrows it to one study. The same for `agy`'s web tools. `mmo status` / `mmo context list` print
  `web open in runs: ...`. The research environment's `.claude/settings.json` matches these tools.
- `check_source` reports a context source without complete provenance; the studied (primary) source needs none.

## The critic through agy (T46, ADR 0014)

`code/mmo/analysis/critic.py`, `mmo critic brief|run|list`, `mmo-guard agy-pre-tool-use` (spec, "The critic of another
maker").

- `run_critic(topic, author, round, timeout_minutes, runner, dry_run)`; `runner(cmd, cwd, env, timeout)` returns
  `(exit code, stdout, stderr)` - tests pass a fake `agy`.
- `snapshot()` / `changes()` / `allowed_change()`: what a critic may change is `topics/<slug>/memos/*.md`, the four
  analysis files and its run's record.
- `parse_stream()` reads `agy` stream-json: the `result.response`, the tool steps (`step_update` DONE with a tool
  step type) and the calls denied by a pre-tool hook.
- `agy` facts found in the task (1.5.16): hooks from `.agents/hooks.json` of the workspace run in `-p` mode, also in
  an untrusted workspace; the hook's input has `toolCall.name`, `toolCall.args` (`run_command.CommandLine`,
  `read_file.Path`, `write_file.Path`/`Content`, `search_web.query`), `workspacePaths`, `cwd`, `modelName`;
  an answer without `decision` denies; `run_command` runs PowerShell on Windows; the prompt goes as an argument
  (from Python, not through Git Bash or PowerShell).

## Blind probe (T45, ADR 0015)

`code/mmo/analysis/probe.py`, `mmo probe start|list`, `mmo memo add --prior-knowledge source:<id>`.

- `start_probe` = `start_run` with the role `blind-probe` and the input `[source:<id>, title: ..., author: ...]` from
  `source.yaml` (refused without `citation.authors` and a title); `task()` is the text the lead hands over.
- `write_memo(prior_knowledge=...)` needs type `reflexive` and adds `source:<id>` to `about`. `prior_record` computes
  `before_search` (no `search-round` in the history) and `met_source_before` (a coding of the model on the source, or a
  memo of the model quoting it or about it, prior-knowledge memos aside).
- `probes()` lists the memos with `prior_knowledge` and the memos that refer to them (`about: memo:<id>`).
- `mmo-guard`: `check_blind` applies when the hook input's `agent_type` is `blind-probe` (Claude Code names the
  subagent there).
- `agy` on Windows: pass the prompt as an argument from Python (`subprocess`), not through Git Bash or PowerShell;
  stdin with `-p` does not work in 1.5.16. The terminal shows Czech letters as `?`/U+FFFD, the files are UTF-8.
