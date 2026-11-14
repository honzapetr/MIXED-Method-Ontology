# SKAD – reflexivity

> What reflexivity means in a SKAD study, for the researcher and for the model. Written for SKAD only; overlaps with
> `methods/reflexivity.md` and other methods are kept on purpose (`methods/README.md`). Status: draft (T10), from
> summaries; to check against Keller 2011 and the 2018 volume (`sources.md`).

## Stance

- SKAD is interpretive: discourses are reconstructed by an interpreter who belongs to a society and its stocks of
  knowledge (Berger & Luckmann). There is no neutral position outside discourse; the researcher's own knowledge of
  the field is part of the frame, and it is made explicit, not bracketed.
- The researcher is often a participant in the discourse studied – as a citizen, an expert, a user, a critic.
  Reflexivity asks from which speaker position the researcher reads, and which readings that position makes easy
  or hard.
- SKAD's analytic tools apply to the researcher too: which interpretive schemes, classifications and story lines
  does the researcher bring? A reconstruction that only finds the researcher's own schemes in the data is suspect.
- Reflexivity works against reification: the categories of the analysis are constructions of the study, not
  properties of the world (the same distance SKAD keeps from the content of the discourse).

## The model in a SKAD study

- A model is trained on texts of many discourses and carries their schemes. Where the discourse studied is one the
  model's training data are full of, the model reads it from inside: its "obvious" readings are the discourse's own
  schemes.
- **When the discourse is about AI**, the model and its maker are actors in it. A language model is one of the
  objects the discourse speaks about, and the maker is a speaker with interests. The model's readings of
  statements about AI (hopes, threats, the human in the age of AI) are not neutral: it may defend, soften, or
  over-correct. This is recorded in the model's positionality memo and checked by a model of a different maker and
  by the researcher.
- Subject positions offered by the discourse (e.g. "the human who must stay human", "the user", "the creator")
  may include positions for AI systems themselves. The model does not decide what such positions mean.

## By phase

| Phase | Researcher | Model |
| :--- | :--- | :--- |
| framing | positionality memo: relation to the topic and the discourse, own position in it, stakes, expected story lines | positionality memo for this study (relation to the topic, prior knowledge of the material, likely tendencies) |
| corpus | why these documents and not others; whose voices are missing because of my access or interest | declares what it knows about candidate documents and their authors from background, separately from what it read |
| context-analysis | which context I take for granted | separates context from context sources, web search and background |
| fine-analysis | at each gate: is this reading mine or the text's? which reading did I not want? | gives alternative readings; notes where it chose the "balanced" reading over a sharper one |
| content-structure | do my schemes come from the data or from my own view of the topic? | notes which schemes it may have brought from training data; flags merges it did not make |
| speakers-and-effects | how do I relate to the speakers (sympathy, distance)? | notes its maker's position among speakers when the discourse concerns AI |
| synthesis | revisit the framing memo: what changed; what my position made visible and invisible | revisit its framing memo; compare with outputs of another model where they exist |

Memos: `reflexive` (positions, reactions), `methodological` (decisions); format `docs/environment/memos.md`.
Techniques for both analysts: `methods/reflexivity.md`.
Profiles of the analysts, where notes go and when to write one: `docs/environment/analysts/README.md`.
