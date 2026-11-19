# Test copies of the research environment

> How the environment is tried without touching the research repository: `tools/new_test_env.py` (T17, T22, T23,
> T25a; ADR 0011). For the owner and the builder; the analyst in a copy does not know it is a copy.

## Why

The research environment `../MIXED-Method-Ontology/` is where the real research lives. A change of the environment
(instructions, skills, hooks, the program `mmo`) is tried in a **test copy** in `../zkusebna/<name>/`, outside both
repositories: an agent started there works with the new environment, and nothing it writes reaches the research
repository. `zkusebna/` has no `AGENTS.md`, `CLAUDE.md` or `.git` above the copies (the tool refuses one), so no other
instructions leak in.

## Making a copy

```bash
python tools/new_test_env.py                    # zkusebna/test<N>, the next free number
python tools/new_test_env.py test8 --git        # a name of your own; the copy gets its own git
python tools/new_test_env.py --dry-run          # only list what would be copied
```

| What | In the copy |
| :--- | :--- |
| Files git sees in the research environment (tracked + untracked not ignored), with uncommitted changes | yes |
| A study's input documents kept out of git by `topics/.gitignore` (`text.md`, segments, `ingest/` …) | yes |
| Page images and other git-ignored originals | only with `--with-source-files` |
| `.env`, `.venv/`, caches, `scratch/`, `.git/` | never |
| Project files (dotfiles, `pyproject.toml`, `uv.lock`, `tools/`) | yes; `--without-project-files` leaves them out (then the hooks cannot run) |

The path of the workshop in `pyproject.toml` / `uv.lock` is rewritten, and `uv sync` runs in the copy (`--no-sync`
skips it), so `mmo` and the guard hooks (`mmo-guard`) work there. `mmo` comes **from the workshop as it is checked
out**: a copy uses the program of the workshop's current branch, not a copy of it.

`--without-profile <model-id>` leaves a model's profile out, to try a model's first start. `--git` gives the copy a
repository of its own, so the work done in it can be followed commit by commit.

Every copy is recorded in `zkusebna/_log.tsv` (outside the copy, so the analyst does not see it): time, name,
branch and commit of the research environment, `clean` or `dirty` (uncommitted changes copied), options.

## Carrying the work of an earlier copy (`--carry`)

A test goes on longer than one version of the environment: in `test7` the researcher and the model framed the study
(questions, positions, memos, the confirmed profile); then the environment changed (T24, T25). `--carry` starts a
new copy from the **current** environment and brings in **the study work** of the earlier one:

```bash
python tools/new_test_env.py test8 --carry test7 --git
```

**What is carried.** The tool compares every file of the earlier copy with the commit of the research environment
it was made from (`_log.tsv`). A file the copy created, changed or deleted since then is its own work. Of that, only
the **study state** is carried:

| Carried (study state) | Never carried |
| :--- | :--- |
| `topics/<slug>/topic.yaml`, `positions/`, `memos/`, and other files a study gains later | the environment: `AGENTS.md`, `methods/`, skills, `docs/`, `ontology/`, project files |
| `topics/<slug>/sources/<id>/source.yaml`, `notes.md` (written by the researcher) | the environment's own files in the study areas: `topics/README.md`, `topics/.gitignore`, `analysts/README.md`, `analysts/_template-*` |
| `analysts/<id>.md` (a profile, e.g. its confirmation) | what the machine rebuilds: `sources/<id>/text.md`, `segments.jsonl`, `ingest/`, `files/`, `ground-truth/`, `topics/<slug>/work/` |

Everything else comes new from the research environment: new instructions, methods, the new `text.md` and its
segments. A file deleted in the earlier copy is deleted in the new one.

**Conflicts.** A study file changed in the earlier copy *and* in the research environment since then (e.g. the
owner edited `topic.yaml` in the research repository too) is a conflict. The tool lists all conflicts and creates
nothing until a side is chosen: `--on-conflict copy` keeps the test's version, `--on-conflict env` the
environment's.

**Feedback.** Environment files the agent changed in the earlier copy (an instruction, a method text) are listed as
`not carried (environment …)`. They are not lost: they tell the builder what the environment may need, and a change
worth keeping is made in the research environment through a task.

**Checks after carrying.** If a carried position was written from another profile version than the profile in the
new copy, the tool warns: the guard keeps the study's text closed to that model until its position is stated again
(skill `state-position`).

**Growing over time.** The new copy's row in `_log.tsv` names the environment commit it was made from and
`--carry <earlier>`. Its carried files differ from that commit, so they count as its own work: carrying from it
later takes everything it holds - what came from the earlier copy and what was added in it.

```
test7  (env a352a96)   framing: topic.yaml, positions, memos, profile confirmed
  └─ --carry ─▶ test8  (env 37c1bb2)   + new text.md, segments, quotation rules; next steps of the study
                  └─ --carry ─▶ test9 (env …)   everything of test7 and test8 on the next environment
```

With `--git` the new copy has two commits: the copy of the environment, then `chore: study work carried from
<earlier>`, so what was carried can be seen with `git show`.

## From a test to the research

A test copy is a test. When the owner decides that work done in a copy is real research (e.g. the framing of a
study), it is brought into the research environment on a branch of its own and merged with the owner's approval -
never by copying a whole test folder back. The files to take are the same study state `--carry` lists.

## Recorded uses

| Copy | Made from | Purpose |
| :--- | :--- | :--- |
| `test1`-`test4` | T16-T19 | a model's first start without its profile |
| `test5`-`test7` | T20-T22 | the analyst's steps, positions, guards; in `test7` the framing of `nazi-v-ai-dobe` |
| `test8` | T25 (`37c1bb2`), `--carry test7` | the framing of `test7` on the final text with segments and the quotation rules |
| `test9` | T29 (`cde59c7`), from the start, `--git` | the whole working cycle: session start, positions, framing, sources, phases, quotations, codes, memos, review (plan: test 9) |
