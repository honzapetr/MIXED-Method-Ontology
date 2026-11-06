# Mapping to standards (draft)

> Status: first proposal. Before relying on it, verify the current version and exact scope of every standard
> (owner's brief). Nothing here is generated or validated yet.

| Our class | Standard | How |
| :--- | :--- | :--- |
| `Codebook` | SKOS `skos:ConceptScheme` | one scheme per topic (and per locked version) |
| `Code`, `Category`, `Theme`, `CoreCategory` | SKOS `skos:Concept` | hierarchy with `skos:broader` / `skos:narrower`; label `skos:prefLabel`, definition `skos:definition` |
| `Annotation` | W3C Web Annotation `oa:Annotation` | body = concept, target = segment with `oa:TextQuoteSelector` (exact quote) and `oa:TextPositionSelector` (start/end) |
| `Segment`, `Page`, `Source` | Dublin Core terms (`dcterms:`), Web Annotation selectors | source metadata in `dcterms:`; segment = specific resource on a page |
| `AnalyticalStep` | PROV-O `prov:Activity` | `prov:used` segments, `prov:wasAssociatedWith` agent (person or model), start/end times |
| proposals (`status`, `author`, `generated_by`) | PROV-O `prov:wasGeneratedBy`, `prov:wasAttributedTo` | every statement points to the step that produced it |
| `Agent` | PROV-O `prov:Agent` (`prov:Person`, `prov:SoftwareAgent`) | models are software agents with name and version |
| `Variable`, `Case` | DDI-CDI | instance variables and units; link qualitative concepts to variables (mixed methods) |
| whole project | REFI-QDA Project Exchange (`.qdpx`) | export of sources, codes and coded segments for ATLAS.ti, MAXQDA, NVivo, QualCoder |
| concepts (optional) | ELSST | `skos:closeMatch` from our concepts to the social-science thesaurus |

## Open questions

- REFI-QDA has no place for relation types, statuses and provenance; decide what goes to memos in `.qdpx`.
- DDI-CDI version and namespace to use (the prefix in the schema is a placeholder).
- Whether `Relation` should be reified as an RDF statement or modelled as its own resource (current draft: own
  resource, so it can carry evidence, confidence and provenance).
