# 14. A lead analyst, subagents with narrow roles, and a critic of another maker

- Status: accepted (2026-11-24, owner)

## Context

In test 9 (`zkusebna/test9`, 2026-11-23/24) one model (claude-opus-5-5) walked the study `nazi-v-ai-dobe` from its
position to the final report in one chat; a model of another maker (gemini-4-neon, Antigravity CLI) was brought in
by the owner as a critic. Record: `scratch/test9/` (both conversations and their transcripts). What it showed:

- **The context filled with reading.** The chat grew from 43k to 540k tokens on the first day and from 67k to 510k
  on the second; two thirds of all tool output was `text.md` of the book. The whole-book reading for the map of
  passages (+200k tokens in four minutes) was followed at once by a compaction: the next day the model worked from
  its map and a summary, not from what it had read. The "single view of the analyst" lived in the record (map,
  memos, codebook), not in the model's context.
- **A closed loop of the model's own map.** The model chose passages from its own map and read passages, not
  chapters; it misread the book's stance on existential risk, overstated one scheme (S6) and missed another (S7, "AI
  as mirror"). The model named this itself when it revisited its position at synthesis.
- **The critic corrected it with a clean context.** Told to read chapters whole before reading the model's memos,
  the critic corrected the schemes in four of six places, mostly with text the lead model had not read, not with a
  different reading of the same passages.
- **The context also filled with the researcher's view.** The model's expectations were confirmed, and it noted that
  this is the risk: they came from the researcher's words. One agent absorbs the whole conversation.
- **The critic ran outside the environment's conditions.** Its instructions were written by the model it criticised
  (the questions came from that model's doubts); it ran without the guard (`mmo-guard` exists only for Claude Code);
  its conversation is not in the study's record and had to be decoded from the Antigravity database.

The owner's note of 2026-11-23 (`docs/owner-notes.md`) asked the same question: should the main agent orchestrate
subagents with the right context, or does that lose the single view of an AI analyst?

## Decision

**A lead analyst** of a study keeps what makes the view one: its position, the codebook, interpretation, relations
between schemes, synthesis, the revisiting of its position and the conversation with the researcher.

**Subagents with narrow roles and a clean context** do bounded work and write it into the record:

| Role | Input | Output |
| :--- | :--- | :--- |
| chapter reader | one part of a source (from its outline), the study's questions | reading notes with exact quotations; no interpretation of schemes |
| instance finder | one code or scheme with its definition | instances and counter-instances across a source, as quotations |
| context searcher | one item of the context search plan (ADR 0015) | candidate sources with their provenance |
| source preparer | one chosen source | `text.md` through the pipeline, `finalize`, spot check |
| blind probe | the name of a source and its author only | what the model knows from training (ADR 0015) |
| critic | the critic's template of the method, the study's confirmed schemes | counter-evidence, missing voices, alternative readings |

Rules:

1. **The single view lives in the record, not in a context.** The map, memos, codebook and a record of coverage
   (what was read whole, what only through the map) are what the lead and every subagent share.
2. **A subagent returns quotations and findings, not conclusions.** The lead reads the quoted places itself before it
   draws an interpretation from them; otherwise the closed loop returns through summaries.
3. **Every subagent is a positioned analyst** (ADR 0009): a profile, a short position for its role in the study, and
   a versioned prompt of its role and phase. What it writes is a proposal the researcher decides (ADR 0013). It
   writes only through `mmo`, under its own analyst id.
4. **Subagents inside Claude Code run the same model as the lead**, so readings stay comparable; a smaller model for
   reading and searching may be tried later as a variant of its own.
5. **The critic is a model of another maker**, checked by `mmo`, not by habit (Antigravity also serves Claude models).
   The model is chosen per study in `topic.yaml`; the default is `gemini-4-neon-medium`.
6. **The critic is started by the orchestrator through `agy`** in print mode (`agy -p --model <model>
   --output-format stream-json`), and the whole run is stored in the study's record. Its profile and its position are
   written once, at the start, and confirmed by the researcher through `mmo review`. Its instructions come from a
   critic's template in the method, filled in by the researcher, not written by the analyst it criticises. It reads
   independently first (round 1: sources and the labels of confirmed schemes, not the lead's memos) and compares
   after (round 2).
7. **The guard holds for every analyst.** If `agy` cannot run the guard as a hook, the critic runs restricted
   (`--sandbox`) and `mmo` checks after the run what changed in the repository; a run that changed anything outside
   what an analyst may write is reported and its changes are not accepted.

## Consequences

- Roles become files of the research environment (`.agents/`, with a skill of the orchestrator), each with input,
  output, position and prompt version (T43); prompts are per phase **and role** (T39).
- `mmo` records coverage of a source (T36) and runs of subagents (who, role, prompt version, input, output).
- `mmo critic run` starts the critic through `agy` and refuses a model of the lead's maker (T46).
- The researcher decides many proposals at once in one command (T47), because subagents produce more of them.
- Test 10 compares one agent with the orchestrator on a new source: coverage, the critic's corrections, peak context
  and the researcher's judgment of whether the interpretation stays one.
