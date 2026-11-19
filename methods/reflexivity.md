# Reflexivity – the researcher and the model

> How the environment makes the position of whoever interprets the data explicit: the researcher's background,
> assumptions and relation to the topic, and – because models take part in the analysis – the position of each
> model. A shared overview; each method has its own `methods/<id>/reflexivity.md`, which says what reflexivity means
> in that method and is never replaced by this file. Status: draft (T10, 2026-11-14), from web search summaries and
> general knowledge of the literature; to be checked against the sources below.

## What reflexivity is

Qualitative analysis is interpretation, and interpretation is done by someone. Reflexivity is the ongoing practice
of examining how the interpreter – their background, interests, assumptions, relations and choices – shapes the
questions, the data, the reading and the result, and of making this visible to others.

- **Positionality** is a description: who the researcher is in relation to the study (social position, history
  with the topic, insider or outsider, stakes). **Reflexivity** is the practice that keeps asking what that
  position does to the research, at every step. A positionality statement written once and never revisited is a
  checklist, not reflexivity.
- Reflexivity is not a removal of bias. Most interpretive methods do not aim at a neutral analyst; they aim at an
  analyst whose position is explicit, so that readers can judge the reading. Methods differ in what they do with
  the position (see each method's `reflexivity.md`).
- Too little reflexivity gives a flat, "view from nowhere" analysis; too much turns the study into a study of the
  researcher. The aim is a balance (Finlay 2002).

## Forms of reflexivity

Two ways of sorting it that are useful here:

- **By object** (Olmos-Vega et al. 2023): *personal* (my background, beliefs, feelings, stakes), *interpersonal*
  (relations with participants, team members – and here with the model), *methodological* (what my choices of
  method, corpus, codes do), *contextual* (the institutional, social and historical setting of the study).
- **By tradition** (Finlay 2002, five variants – names given from memory, to check): introspection,
  intersubjective reflection, mutual collaboration, reflexivity as social critique, reflexivity as discursive
  deconstruction.
- **Epistemic reflexivity** (Bourdieu & Wacquant 1992): not only the individual's biography but the position of the
  researcher in the academic field and the "scholastic" view of someone who interprets other people's practice from
  outside it.

## Techniques

| Technique | What it is | When |
| :--- | :--- | :--- |
| Positionality memo | Who I am in relation to this topic, data and readers; what I want from the study; what I stand to gain or lose | framing; revisited at synthesis |
| Expectations declared before reading | What I expect to find, written before the data are read, compared later with what was found | before the first reading |
| Reflexive journal | Dated notes on decisions, reactions, surprises, discomfort, during the whole study | throughout |
| Bracketing | Writing down preconceptions in order to set them aside (phenomenology, classic GT); criticised in interpretive methods, where preconceptions are used, not set aside (Tufford & Newman 2012) | depends on the method |
| Reflexive questions at gates | Fixed questions asked whenever something is confirmed: what else could this be, whose reading is this, what did I not want to see | every human gate |
| Critical friend / peer debriefing | Another person questions the reading and the decisions | at phase ends |
| Audit trail | Every decision is recorded with its reason, so the path can be followed | throughout (the memo record) |
| Reporting | Reflexivity is written into the study, not only kept privately | writing up |

In this environment these are memos (`docs/environment/memos.md`): `reflexive` for position and reactions,
`methodological` for decisions, and the gates of each method say which reflexive questions are asked.

## Two analysts: the researcher and the model

Both interpret, both have a position, both write reflexive notes. The human researcher decides and owns the
result; the model proposes. The researcher reflects on their own position *and* on their relation to the model;
the model reflects on its position and on its relation to the researcher. How this works in the environment –
profiles, where notes go, the triggers for writing a note, the gate questions – is in
`docs/environment/analysts/README.md`.

## Reflexivity differs by method

| Method | What is done with the analyst's position | Own text |
| :--- | :--- | :--- |
| SKAD | The researcher is a participant in the discourse; their knowledge is part of the frame and made explicit, not bracketed; SKAD's own tools (schemes, story lines) apply to the researcher too | `skad/reflexivity.md` |
| GT, classic | Avoid forcing: preconceptions written down and set aside; theoretical sensitivity from immersion | `grounded-theory/reflexivity.md` |
| GT, Straussian | Sensitivity developed on purpose; experience and literature used if checked against the data | `grounded-theory/reflexivity.md` |
| GT, constructivist | Theory co-constructed; reflexivity part of the method and of the account | `grounded-theory/reflexivity.md` |
| Reflexive TA | Subjectivity is a resource; journal through all phases; no inter-coder agreement | `thematic-analysis/reflexivity.md` |

## The model as a positioned analyst

A model that proposes codes, readings or memos takes part in interpretation. It has no biography, but it has a
position: it was made by someone, trained on some texts and not others, tuned towards some behaviour, and runs
under some instructions. Reflexivity in this environment therefore covers the model too. What belongs to it:

### 1. The analyst is a model version, not "the AI"

- The model is identified by its exact id (e.g. `claude-opus-5-5`), its maker, its knowledge cutoff, and the
  setting it runs in (harness, instructions, tools, sampling). Another version or another model is another
  analyst, even under the same name.
- The model will change: newer versions of the same family, other cloud models, and local models through the
  gateway (ADR 0003, "local first"). Each model used as an analyst writes its own profile in
  `docs/environment/analysts/<model-id>.md`; each analytic step records which model made it (the traceability
  rule).
- A finding that holds for one model is not known to hold for another. Changing the model in the middle of a phase
  is a methodological decision and gets a `methodological` memo.

### 2. What shapes a model's position

| Source | What it can do to the analysis |
| :--- | :--- |
| Training data | Over-represents some languages, regions, periods and voices (English, online, technical, Western); knows some discourses better than others; Czech texts and Czech public debate are under-represented |
| Post-training (values, style) | Pulls towards balance, caution, hedging, politeness and a "both sides" framing; may soften or smooth sharp positions in the data; may be agreeable with the researcher (sycophancy) |
| The maker's place in the field | A model is a product of a company that is itself an actor in public discourse – about AI in particular. When the data are about AI, the model is not outside the discourse it analyses |
| Instructions and harness | System prompt, `AGENTS.md`, skills, memory files and the coding-oriented tools shape what the model does: structure, tidiness, avoiding repetition – the habit that nearly blurred the methods (`docs/owner-notes.md`, 2026-11-14) |
| Prior knowledge of the material | The model may know the author, the book, reviews or the debate from training or from a web search in the same session; this must not pass for something read in the data |
| Knowledge cutoff | Knows nothing after it; may treat its own period's debate as the present |
| Session context | What has already been read, a compacted summary instead of the original text, the order in which passages came; long contexts are read unevenly |

### 3. What a model lacks – and how to treat its self-reports

- No lived experience, no membership in the social worlds it reads about, no memory between sessions except the
  files of the project. It cannot "recognise itself" in a reading the way a researcher can.
- A model's statements about its own biases are not privileged access; they are hypotheses. A reflexive memo by a
  model says what *may* shape its readings; the checks below test it. A list of biases never replaces a check.
- No confessional or anthropomorphic language (feelings, beliefs held, discomfort). The model states conditions
  and tendencies, not inner states.

### 4. Tendencies to watch in a model's analytic output

- smoothing contradictions and ambivalence into a coherent story;
- fitting the data into the categories of the method or of familiar theory before the data justify it;
- merging near-duplicate codes or readings (economy over precision);
- paraphrase that drifts from the quote; claims without a segment;
- adopting the researcher's framing or the framing of the prompt;
- favouring passages at the start and end of a long input;
- different results on re-runs of the same step.

### 5. Reflexive techniques for models

| Technique | How |
| :--- | :--- |
| Model profile | `docs/environment/analysts/<model-id>.md`, written by the model itself: id, maker, cutoff, setting, known tendencies (as hypotheses), what it was used for, and a journal |
| Running notes | the model writes a note whenever a trigger occurs (correction by the researcher, background knowledge used, a merge or a softened reading, the topic concerns AI or its maker, …; full list in `docs/environment/analysts/README.md`) |
| Model positionality memo per study | at framing: the model's relation to this topic, its prior knowledge of the material, the tendencies most likely to matter here; `reflexive`, `proposed` |
| Prior knowledge declared before reading | what the model already "knows" or expects about the material, written before it reads the data, compared later; `basis.how` always separates the text, context sources, web search and the model's background |
| Reflexive note at each gate | with a batch of proposals: what may have been smoothed, merged, left out or framed by the prompt |
| Cross-model comparison | the same step by two models (e.g. a cloud model and a local one); differences are data for a `reflexive` or `methodological` memo, not noise to be averaged |
| Re-run check | the same step run again; unstable proposals are flagged |
| Critic by another model | scenario C (critic) is run, where possible, by a different model than the one that proposed |
| The researcher's relation to the model | interpersonal reflexivity: did I accept this because it was well written? did the model's framing become mine? recorded in the researcher's journal |

## Sources

Found by web search on 2026-11-14 (T10) unless marked; status as in the method `sources.md` files.

| Work | Link | Status |
| :--- | :--- | :--- |
| Finlay, L. (2002). Negotiating the swamp: the opportunity and challenge of reflexivity in research practice. *Qualitative Research* 2(2). | <https://journals.sagepub.com/doi/10.1177/146879410200200205> | summary |
| Olmos-Vega, F. M., Stalmeijer, R. E., Varpio, L. & Kahlke, R. (2023). A practical guide to reflexivity in qualitative research: AMEE Guide No. 149. *Medical Teacher* 45(3). | <https://doi.org/10.1080/0142159X.2022.2057287> | summary |
| Bourdieu, P. & Wacquant, L. (1992). *An Invitation to Reflexive Sociology*. University of Chicago Press. | – | general knowledge |
| Tufford, L. & Newman, P. (2012). Bracketing in qualitative research. *Qualitative Social Work* 11(1). | – | general knowledge |
| Berger, R. (2015). Now I see it, now I don't: researcher's position and reflexivity in qualitative research. *Qualitative Research* 15(2). | – | general knowledge |
| Mauthner, N. & Doucet, A. (2003). Reflexive accounts and accounts of reflexivity in qualitative data analysis. *Sociology* 37(3). | – | general knowledge |
| Xu, W. (2026). Doing thematic analysis in the age of generative AI: practices, ethics and reflexivity. *International Journal of Qualitative Methods*. | <https://journals.sagepub.com/doi/10.1177/16094069261425173> | found |
| LLM-assisted thematic analysis: opportunities, limitations, and recommendations (2025, preprint). | <https://arxiv.org/pdf/2511.14528> | found |
| Reflexis: supporting reflexivity and rigor in collaborative qualitative analysis through design for deliberation (2026, preprint). | <https://arxiv.org/html/2601.15445v2> | found |
| Interrogating the use of large language models in qualitative research using the Qualifying Qualitative Research Quality framework. *Journal of Systematics and Evaluation*. | <https://seejournal.org/articles/10.21061/see.174> | found |
| Evaluation of large language models within GenAI in qualitative research. *Scientific Reports* (2025). | <https://www.nature.com/articles/s41598-025-18969-w> | found |

"general knowledge" = known to the model from training, not looked up in this task; check before citing.
