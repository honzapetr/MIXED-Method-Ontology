# Research design: purpose, questions and theory

> Background for the analysis environment (T8). How qualitative and mixed-methods approaches link the reason for a
> study, its research questions and its theory, and what that means for the environment. Proposals for the
> environment are marked **(proposal)**; the owner decides. References are working summaries: check the editions
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

Maxwell's interactive model (Qualitative Research Design, 1996; 3rd ed. 2013) makes the chain a system, not a line:
five components - goals, conceptual framework, research questions, methods, validity - each shaping the others.
Goals answer "why is this study worth doing" (personal, practical, intellectual goals). The conceptual framework
answers "what do I think is going on" (existing theory, own experience, earlier studies, thought experiments).
Research questions sit in the middle: they must follow from the goals and the framework and be answerable by the
methods. Focused questions usually emerge during the study, not before it. Maxwell also separates the intended
design from the "design in use" - what actually happened.

## Where theory comes from

| Logic | Theory before the data | Theory after the data | Typical home |
| :--- | :--- | :--- | :--- |
| Deductive | theory gives hypotheses to test | confirmed or rejected | quantitative strand |
| Inductive | kept away (classic GT) | built from codes and categories | Glaser & Strauss 1967 |
| Abductive | known theories are the background against which a surprise is noticed | a new explanation for the surprise, checked again in the data | Timmermans & Tavory 2012 |

**Sensitising concepts** (Blumer 1954) give a direction of looking, not a definition to apply; they are the usual
way prior theory enters a qualitative study without fixing its result. **Reflexivity**: the researcher's position
and assumptions are part of the framework and are written down.

## How each approach handles it

**Grounded theory.** Glaser: start from an area of interest, no preconceived question ("what is going on here?").
Strauss & Corbin: a broad question naming the phenomenon, narrowed during coding. Charmaz (constructivist GT):
an initial question and sensitising concepts are points of departure; theory is constructed by the researcher, not
discovered. Output: a substantive theory (a core category and the categories and relations around it); a formal
theory when it is compared across areas.

**Reflexive thematic analysis** (Braun & Clarke). The question may be broad and change during analysis. Theory
enters as the explicit framework (ontology, epistemology, inductive or theory-led orientation). The aim is an
interpretive account of themes, not necessarily a theory.

**Sociology of Knowledge Approach to Discourse - SKAD** (Keller, 2005; English 2011, 2018). Theory base: social
construction of reality (Berger & Luckmann) and Foucault's questions about discourse and power/knowledge. The
questions are about how knowledge is made: what phenomenon a discourse constitutes, who speaks and from which
position, which interpretive schemes, classifications, phenomenon structure (causes, responsibility, solutions,
values) and narrative structure it uses, and what effects it has (dispositif). Theory here is a heuristic frame,
not hypotheses; analysis is hermeneutic and non-deductive and borrows GT coding and comparison. Output: a
reconstruction of the discourse(s) - their structure, positions and effects - as a middle-range account.

**Critical discourse analysis - dialectical-relational** (Fairclough). The purpose is stated as a normative starting
point: (1) focus on a social wrong in its semiotic aspect, (2) identify obstacles to addressing it, (3) ask whether
the social order "needs" the wrong, (4) identify possible ways past the obstacles. The "why" of the study is part
of the method itself.

**Mixed methods** (Creswell & Plano Clark, 2018; 4th ed. 2025). Separate qualitative, quantitative and mixed
questions; the mixed question asks how the strands are integrated (e.g. "how do the qualitative findings explain
the quantitative results?"). The questions decide the design (convergent, explanatory sequential, exploratory
sequential). A theoretical framework may shape the whole design.

## What this means for the environment (proposal)

1. **The purpose is recorded, not implied.** A topic states why it exists (problem, motive, for whom) and the
   researcher's position. Every question traces back to it.
2. **Questions are living objects.** Each research question has a type (qualitative, quantitative, mixed), an
   origin (from the purpose, from the framework, from a surprise in the analysis), a status (initial, refined,
   dropped, answered) and a history - which memo or finding changed it. This is Maxwell's "design in use".
3. **The conceptual framework is explicit:** sensitising concepts, prior theories, assumptions. The method module
   says how the framework may be used (GT: lightly; SKAD: as a heuristic frame; CDA: normative starting point).
4. **Theory is built from propositions.** A proposition connects confirmed concepts and relations, answers one or
   more questions, has evidence and counter-evidence (segments) and a memo on how it was reached (inductive,
   abductive, from prior theory).
5. **Working with theory afterwards:** test it against new sources (confirms / extends / contradicts), compare it
   with prior theories of the framework, derive new questions - including quantitative ones, which is the link to
   the mixed-methods strand.
6. **Ontology:** today it has `ResearchQuestion` and `Goal`; it would need a purpose and position of the topic, a
   conceptual framework with sensitising concepts, and `Theory` / `Proposition` linked to questions and evidence.

## Per method, in short

The same summary is in each method module under `research_design` (`methods/*.yaml`), so agents read it with the
method. SKAD is the method of the first study (`nazi-v-dobe-ai`); its module is written in the next step.

| Method | Purpose | Questions arise | Prior theory | Reasoning | Theory output |
| :--- | :--- | :--- | :--- | :--- | :--- |
| GT (Charmaz) | understand a process in an area of interest | broad initial question, refined during coding | sensitising concepts, lightly | inductive, abductive moments | substantive theory around a core category |
| Reflexive TA | interpret patterns of meaning | broad, may change during analysis | declared framework (orientation, epistemology) | inductive or theory-led | defined themes, not necessarily a theory |
| SKAD | reconstruct how a discourse makes knowledge | about phenomenon, speakers, interpretive schemes, classifications, phenomenon and narrative structure, effects | heuristic frame (Berger & Luckmann, Foucault) | hermeneutic, non-deductive, GT coding | reconstruction of discourses, middle-range account |
| CDA (Fairclough) | critique of a social wrong | from the social wrong, its obstacles and ways past | critical social theory, explicit | explanatory critique | explanation of how semiosis sustains the wrong |
| Mixed methods | integrate strands | separate qual, quant and mixed questions | may shape the whole design | depends on the strand | integrated inferences (meta-inferences) |

## Sources consulted (T8, 2026-11-13)

Found by web search and used for this document:

- Maxwell, Qualitative Research Design (SAGE):
  <https://www.sagepub.com/en-us/nam/qualitative-research-design/book234502>
- Maxwell, Designing a Qualitative Study (chapter):
  <https://study.sagepub.com/sites/default/files/sk_book_chapter_designing_a_qualitative_study.pdf>
- Keller, Hornidge & Schünemann (eds.), The Sociology of Knowledge Approach to Discourse (OAPEN, open access):
  <https://library.oapen.org/bitstream/20.500.12657/57263/1/9781351690614.pdf>
- Keller, The Sociology of Knowledge Approach to Discourse (chapter, Taylor & Francis):
  <https://www.taylorfrancis.com/chapters/oa-edit/10.4324/9781315170008-2/sociology-knowledge-approach-discourse-reiner-keller>
- Fairclough, Critical Discourse Analysis: <https://www.perlego.com/book/2192459/critical-discourse-analysis-the-critical-study-of-language-pdf>
- Timmermans & Tavory (2012), Theory Construction in Qualitative Research:
  <https://www.mackenzie.br/fileadmin/user_upload/Timmermans___Tavory__2012__Theory_Construction_in_Qualitative_Research_From_Grounded_Theory.pdf>
- Creswell & Plano Clark, Designing and Conducting Mixed Methods Research (SAGE):
  <https://us.sagepub.com/en-us/cab/designing-and-conducting-mixed-methods-research/book269004>

Not read in full yet; to read first for the SKAD module: the OAPEN volume (open access) and Keller (2011) in
*Human Studies*.

## References

- Blumer, H. (1954). What is wrong with social theory? *American Sociological Review* 19(1).
- Braun, V. & Clarke, V. (2006; 2019; 2022). Thematic analysis; *Thematic Analysis: A Practical Guide*. SAGE.
- Charmaz, K. (2006; 2014). *Constructing Grounded Theory*. SAGE.
- Creswell, J. W. & Plano Clark, V. L. (2018; 2025). *Designing and Conducting Mixed Methods Research*. SAGE.
- Fairclough, N. (2010). *Critical Discourse Analysis: The Critical Study of Language*, 2nd ed. Routledge.
- Glaser, B. & Strauss, A. (1967). *The Discovery of Grounded Theory*. Aldine.
- Keller, R. (2011). The Sociology of Knowledge Approach to Discourse (SKAD). *Human Studies* 34(1).
- Keller, R., Hornidge, A.-K. & Schünemann, W. (eds.) (2018). *The Sociology of Knowledge Approach to Discourse*.
  Routledge (open access).
- Maxwell, J. A. (2013). *Qualitative Research Design: An Interactive Approach*, 3rd ed. SAGE.
- Strauss, A. & Corbin, J. (1990). *Basics of Qualitative Research*. SAGE.
- Timmermans, S. & Tavory, I. (2012). Theory construction in qualitative research: from grounded theory to abductive
  analysis. *Sociological Theory* 30(3).
