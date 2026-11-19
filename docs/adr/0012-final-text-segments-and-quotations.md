# 12. The final text, segments and quotations

- Status: accepted (2026-11-17, owner; `docs/answers.md`); amends ADR 0006 (segments of a source)

## Context

The first book was photographed, read by OCR and by Claude models, put in reading order and written out as
`text.md` – a header, one location comment per page and the page's text. That format grew out of getting the text;
it was never decided as the input of the analysis. Meanwhile segments were cut from each OCR variant separately
(`segments/<variant>.jsonl`), with offsets into one scan's OCR text and with a cleaned text that was not word for
word what `text.md` holds. Two problems follow:

- What the analysis reads (`text.md`) and what it would point to (segments of a working variant) were two different
  texts; a quote taken from `text.md` could not be checked against a segment.
- New kinds of sources (a PDF with a text layer, a web page with a review, a transcript) have no scans, so a format
  built around scans does not fit them.

The owner also asked what segments are for. Qualitative tools point a code at a passage of any length (ATLAS.ti
"quotation", MAXQDA "coded segment", NVivo "coding reference"); W3C Web Annotation does it with a
`TextQuoteSelector` (exact words) and a `TextPositionSelector` (offsets). SKAD codes passages the researcher chooses
(*Textstellen*); it does not define how a passage is recorded.

## Decision

1. **`text.md` is the contract.** Every source, whatever its original, is brought into one final text with the same
   form: a header written by the program, a title, and its text in reading order under **location comments**
   (`<!-- page 15 (printed) · scan 1 · IMG_….jpg -->` for a page, `<!-- file part-1.txt · scan 1 -->` for a text
   file; further kinds come with their converters). Conversion is done by the program without AI; OCR is used only
   where there is no text layer. Words hyphenated at a line end are joined when `text.md` is written.
2. **Header and metadata are apart.** The header of `text.md` holds technical facts only (source, variant, date,
   pages, missing pages, unclear words, who or what read it). Bibliographic and research facts live in
   `source.yaml`, written by the researcher; whether a model may propose them is open.
3. **Segments are paragraphs of `text.md`.** `mmo source finalize` writes `text.md` and cuts it into
   `sources/<id>/segments.jsonl`; `mmo segment` cuts it again. A segment is one paragraph of one place, with
   `start`/`end` offsets into `text.md` and `text` equal to `text.md[start:end]`. Pages are not segments: a page is a
   place to cite, not a unit of meaning; it is a field of every segment. Segments are a rebuildable index for
   reading, batching and counting – not what the analysis points to. Per-variant segments are gone.
4. **The analysis points to quotations.** A quotation is the exact words of a passage with its source, pages and
   offsets in `text.md`. It may be shorter than a segment or run over several and over a page break (the location
   comment inside it is not part of the words). A code, reading, memo or proposition carries a list of quotations.
   The program checks a quotation before it is stored and refuses one whose words are not at that place; when
   `text.md` is rebuilt, a quotation is found again by its words. The term "anchor" is not used: it collides with
   Mayring's anchor examples (*Ankerbeispiele*).

## Consequences

- `mmo ingest` no longer writes segments; it ends with the working variant's text and asks the researcher to choose
  the variant. `mmo segment <topic> <source>` takes no variant. `mmo source check` reports segments that are missing
  or no longer match `text.md`. Old `work/segments/` files are dropped by `mmo topic migrate`.
- The guard (`mmo-guard`) gates `segments.jsonl` like `text.md`.
- The ontology gets `Quotation` (W3C Web Annotation target with both selectors); `Annotation`, evidence and
  propositions point to quotations; `Segment` stays as the reading unit.
- Method texts that said "evidence segments" or "quote the segment" now speak of quotations; where a method uses
  "segment" in its own sense (grounded theory's breaking data into segments), the word stays.
- Converters for PDF, web pages and other formats, removing page furniture (running heads, page numbers), and
  storing and checking quotations are tasks of their own (`docs/plan.md`); how the whole pipeline works is in
  `docs/source-pipeline.md`.
