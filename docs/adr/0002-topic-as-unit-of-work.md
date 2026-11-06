# 2. A topic is the unit of work and of versioning

- Status: accepted (owner, 2026-11-06)

## Context

The owner works on research topics, not on single method runs. A topic has several questions and goals, gets new
material over time and must stay usable after the analysis (new questions, other angles). Variants must coexist like
git branches.

## Decision

Each topic is a folder `topics/<slug>/` with `topic.yaml`, sources, intermediate results and (later) the graph as
sorted Turtle files. Git provides versions: `main` = confirmed state, branches = variants, merge = acceptance.
Large source files stay out of git; manifests keep their hashes. Method runs are steps inside a topic.

## Consequences

History, diffs and rollback come from git. Text formats must stay diff-friendly (sorted, one record per line or
file). A topic may later move to its own repository without changing its layout.
