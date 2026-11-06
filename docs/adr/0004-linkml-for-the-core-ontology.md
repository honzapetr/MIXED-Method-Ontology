# 4. LinkML for the core ontology

- Status: accepted (owner, 2026-11-06); schema is a draft

## Context

The ontology must map to SKOS, W3C Web Annotation, PROV-O, DDI-CDI and export to REFI-QDA (`.qdpx`). It should
also give Python classes and validation.

## Decision

The core is written in LinkML (`ontology/schema/mmo.yaml`) with `class_uri` / `slot_uri` pointing to the standards.
OWL/Turtle, JSON-LD context and Python classes will be generated from it when the graph is built (T4). `.qdpx` is a
separate export, because QDA tools do not read LinkML or RDF.

## Consequences

Until generation is wired in, `tests/test_ontology_and_methods.py` checks the schema's internal consistency.
Standard versions must be verified before the mapping is relied on.
