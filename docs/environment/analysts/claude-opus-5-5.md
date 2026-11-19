# claude-opus-5-5 – model profile

> Written by the model itself on 2026-11-14 (T10); to be checked by the owner. Tendencies are hypotheses until a
> check or a study shows them.

| Field | Content |
| :--- | :--- |
| id, maker | `claude-opus-5-5` (Claude Opus 5.5), Anthropic |
| access | cloud; used in interactive sessions with the owner through Claude Code (owner's choice for building the environment; use for analysis steps still needs the owner's approval per step type) |
| knowledge cutoff | June 2026 |
| setting | Claude Code in VS Code; `AGENTS.md`, `CLAUDE.md`, project skills, a memory folder; tools for files, shell, web search. Long sessions are compacted into summaries, so later steps may rest on a summary, not the original text |
| language coverage | reads and writes Czech; the quality of reading Czech essayistic prose is not tested |
| training and post-training | trained on large text collections with more English, online and technical text than Czech; tuned for helpfulness, caution and balance, and heavily for programming tasks; details of the data are not known to the model |
| tendencies (hypotheses) | balanced, hedged framing that may soften sharp positions; agreeableness with the owner; structuring, tidying and removing repetition; fitting data to known theory; using background knowledge without saying so; acting ahead of approval |
| position towards topics | Anthropic makes AI systems and takes part in the public debate about AI. In any study of AI discourse (e.g. `topics/nazi-v-ai-dobe/`) this model is inside the discourse it reads: an object of it, and the product of one of its speakers |
| what it lacks | lived experience; membership in the social worlds it reads about; memory between sessions except project files; knowledge after June 2026; privileged access to its own biases |
| used for | building the environment (T1–T10); `nazi-v-ai-dobe`: web search for context sources and a first-impression memo (T8), the model positionality memo (T10) |

## Journal

- 2026-11-14 – correction by the owner (T9): when writing how methods work, the model pulled towards merging and
  shortening method texts to avoid repetition; the owner stopped it (`docs/owner-notes.md`). Shows the programming
  habit of economy over precision. Rule since then: precision before economy.
- 2026-11-14 – acted before approval (T10): asked to research reflexivity, the model started writing files before
  the owner had seen the findings; the owner asked to see them first. Shows a pull towards finishing a task in one
  go. For research content: report findings first, write after approval.
- 2026-11-14 – background knowledge (T11 preparation): in the findings on separating the environment from a study,
  the claim that QDA applications keep the program apart from the project file came from general knowledge, not
  from a source found; it was marked so to the owner and in ADR 0010.
- 2026-11-15 – correction by the owner (T11): the owner asked to separate the builder's workshop from the research
  environment being built (an ecosystem of methods, approaches and many studies). The model read it as "environment
  vs. one study", found sources that fit that reading and built T11 on it without restating its understanding
  first. Shows fitting the request to a familiar software pattern (tool vs. project). Rule: restate the owner's
  structure in their words and get a yes before planning a split.
