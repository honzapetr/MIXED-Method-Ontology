# 6. Source-centric topic layout

- Status: accepted (2026-11-12, owner approved the direction; details below are technical choices)

## Context

T1 and T2a stored a topic's intermediate results by processing step: `work/ocr/<variant>/<source>/`,
`work/numbers/<source>.json`, `work/order/<variant>/<source>.yaml`, `work/text/<variant>/<source>.md`,
`work/segments/<source>.jsonl`, `ground-truth/<source>/`. Everything about one book is spread over six places. In
qualitative research the unit a researcher works with is the document (source) – as in ATLAS.ti, MAXQDA and
REFI-QDA, which we will export to. Three more problems showed on the first book:

- `source.yaml` mixes what the researcher writes (title, note, `printed_pages` fixes) with 213 machine-written image
  hashes, which makes hand edits awkward.
- `page` means the scan number (file-name order) in `source.yaml`, the OCR JSON and segment ids, but the printed
  page number in the reading order. The two were confused in practice.
- There is no place for what qualitative work needs about a source: a citation, attributes (document variables /
  cases), a memo on context, the research questions it serves, and supplementary material about it.

## Decision

1. **One folder per source** holds everything about it:

   ```
   sources/<id>/
     source.yaml        # written by the researcher
     notes.md           # written by the researcher: context memo
     files/             # original files (images, text, ...); images git-ignored
     text/<variant>.md  # readable whole text in reading order
     segments/<variant>.jsonl
     ground-truth/scan-NNNN.txt
     ingest/            # written by the machine, never edited by hand
       files.yaml       #   every original file with its SHA-256 and scan number
       ocr/<variant>/scan-NNNN.json
       page-numbers.json
       order/<variant>.yaml
   ```

   Topic-level folders stay for what spans sources: `topic.yaml`, `memos/`, `graph/`.
2. **Human and machine files are separate.** `source.yaml` keeps only researcher-written fields: `id`, `title`,
   `kind`, `role`, `about`, `language`, `citation`, `attributes`, `questions`, `printed_pages`, `note`. Image hashes
   move to `ingest/files.yaml`.
3. **`scan` and `page` have one meaning each.** `scan` = position of a file in file-name order (identity of an
   image); `page` = printed page number. OCR JSON gets `scan` instead of `page`; files are `scan-NNNN.json`;
   segment ids become `<source>:s<scan>:<n>`. Readers accept the old `page` key, so older results still load.
4. **Supplementary material is a source** with `role: context` and `about: [<source id>, ...]`; the primary source
   has `role: primary` (default). It is ingested and segmented like any other source.
5. **`topic.yaml` lists its sources** (`sources: [<id>, ...]`), kept in sync by the CLI.
6. **Existing topics are migrated by a command** (`mmo topic migrate <topic>`): files are moved and field names
   rewritten; OCR text, timing and provenance stay byte-for-byte the same, so no OCR is rerun.

## Consequences

A researcher finds a source's text, notes and review reports in one folder; agents get one path per source. Paths in
code, tests, spec, README, `topics/README.md` and the `ingest-sources` skill change. Segment ids change; nothing
refers to them yet (the graph is T4), so now is the cheapest time. Comparing variants across sources needs a loop
over sources instead of one folder – acceptable, comparison is per source anyway.
