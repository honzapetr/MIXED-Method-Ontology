# Foundations – purpose, questions and theory across methods

> Methodology shared by the methods: how a study links its reason, its questions and its theory, where theory
> comes from, and why memos are analytic work. This is an overview for comparison; it never replaces a method's
> own text in `methods/<id>/` (`methods/README.md`). Status: working summary – check the editions in the sources
> before relying on details.

## The chain

Most methodologies agree on one chain, but differ in how firm each link is at the start:

```
purpose (why the study exists)
  -> goals (what the researcher wants to find out, for whom)
  -> conceptual framework (prior theory, sensitising concepts, own position)
  -> research questions
  -> analysis (method)
  -> theory / findings (answers to the questions, grounded in evidence)
  -> new questions, revised framework, revised purpose
```

Maxwell's interactive model (*Qualitative Research Design*, 1996; 3rd ed. 2013) makes the chain a system, not a
line: five components – goals, conceptual framework, research questions, methods, validity – each shaping the
others. Goals answer "why is this study worth doing" (personal, practical, intellectual goals). The conceptual
framework answers "what do I think is going on" (existing theory, own experience, earlier studies, thought
experiments). Research questions sit in the middle: they must follow from the goals and the framework and be
answerable by the methods. Focused questions usually emerge during the study, not before it. Maxwell also
separates the intended design from the "design in use" – what actually happened.

## Where theory comes from

| Logic | Theory before the data | Theory after the data | Typical home |
| :--- | :--- | :--- | :--- |
| Deductive | theory gives hypotheses to test | confirmed or rejected | quantitative strand |
| Inductive | kept away (classic GT) | built from codes and categories | Glaser & Strauss 1967 |
| Abductive | known theories are the background against which a surprise is noticed | a new explanation for the surprise, checked again in the data | Timmermans & Tavory 2012 |

**Sensitising concepts** (Blumer 1954) give a direction of looking, not a definition to apply; they are the usual
way prior theory enters a qualitative study without fixing its result. **Reflexivity:** the researcher's position
and assumptions are part of the framework and are written down.

## Memos are analytic work

Notes and impressions are not side remarks: every approach treats them as part of the analysis – GT memoing in
every phase, familiarisation notes and the reflexivity journal in TA, interpretive and context memos in SKAD. A
first impression already frames the analysis, so it must be visible, typed and traceable like any other step, and
kept apart from findings. Each method says which memos its phases expect (`memos` in `method.yaml`); the format is
in `docs/environment/memos.md`. Reflexivity of the researcher and of the model: `methods/reflexivity.md`.

## Overview of methods

Short comparison. The binding text of each method is in its folder; CDA and mixed methods have no module yet.

| Method | Purpose | Questions arise | Prior theory | Reasoning | Theory output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GT (`grounded-theory/`) | understand a process in an area of interest | broad initial question, refined during coding | sensitising concepts, lightly | inductive, abductive moments | substantive theory around a core category |
| Reflexive TA (`thematic-analysis/`) | interpret patterns of meaning | broad, may change during analysis | declared framework (orientation, epistemology) | inductive or theory-led | defined themes, not necessarily a theory |
| SKAD (`skad/`) | reconstruct how a discourse makes knowledge | about phenomenon, speakers, interpretive schemes, classifications, phenomenon and narrative structure, effects | heuristic frame (Berger & Luckmann, Foucault) | hermeneutic, non-deductive, GT coding | reconstruction of discourses, middle-range account |
| CDA, Fairclough (no module) | critique of a social wrong | from the social wrong, its obstacles and ways past | critical social theory, explicit | explanatory critique | explanation of how semiosis sustains the wrong |
| Mixed methods (no module) | integrate strands | separate qual, quant and mixed questions | may shape the whole design | depends on the strand | integrated inferences (meta-inferences) |

**CDA, dialectical-relational (Fairclough).** The purpose is a normative starting point: (1) focus on a social
wrong in its semiotic aspect, (2) identify obstacles to addressing it, (3) ask whether the social order "needs" the
wrong, (4) identify possible ways past the obstacles.

**Mixed methods (Creswell & Plano Clark, 2018; 4th ed. 2025).** Separate qualitative, quantitative and mixed
questions; the mixed question asks how the strands are integrated (e.g. "how do the qualitative findings explain
the quantitative results?"). The questions decide the design (convergent, explanatory sequential, exploratory
sequential). A theoretical framework may shape the whole design.

## Sources

Found by web search on 2026-11-13 (T8); status as in the method `sources.md` files.

| Work | Link | Status |
| :--- | :--- | :--- |
| Maxwell, J. A. (2013). *Qualitative Research Design: An Interactive Approach*, 3rd ed. SAGE. | <https://www.sagepub.com/en-us/nam/qualitative-research-design/book234502> | summary |
| Maxwell, J. A. (2009). Designing a qualitative study. In Bickman & Rog (eds.), *SAGE Handbook of Applied Social Research Methods*. | <https://study.sagepub.com/sites/default/files/sk_book_chapter_designing_a_qualitative_study.pdf> | found |
| Blumer, H. (1954). What is wrong with social theory? *American Sociological Review* 19(1). | – | summary |
| Timmermans, S. & Tavory, I. (2012). Theory construction in qualitative research. *Sociological Theory* 30(3). | <https://www.mackenzie.br/fileadmin/user_upload/Timmermans___Tavory__2012__Theory_Construction_in_Qualitative_Research_From_Grounded_Theory.pdf> | found |
| Fairclough, N. (2010). *Critical Discourse Analysis: The Critical Study of Language*, 2nd ed. Routledge. | <https://www.perlego.com/book/2192459/critical-discourse-analysis-the-critical-study-of-language-pdf> | summary |
| Creswell, J. W. & Plano Clark, V. L. (2018; 2025). *Designing and Conducting Mixed Methods Research*. SAGE. | <https://us.sagepub.com/en-us/cab/designing-and-conducting-mixed-methods-research/book269004> | summary |
| Keller, R., Hornidge, A.-K. & Schünemann, W. J. (eds.) (2018). *The Sociology of Knowledge Approach to Discourse*. Routledge (open access). | <https://library.oapen.org/bitstream/20.500.12657/57263/1/9781351690614.pdf> | found |
| Keller, R. (2018). The Sociology of Knowledge Approach to Discourse: an introduction (chapter). | <https://www.taylorfrancis.com/chapters/oa-edit/10.4324/9781315170008-2/sociology-knowledge-approach-discourse-reiner-keller> | found |
