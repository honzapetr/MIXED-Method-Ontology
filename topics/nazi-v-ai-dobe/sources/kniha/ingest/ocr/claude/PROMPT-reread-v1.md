# Prompt `reread-v1` – variant `claude`

Model: `claude-opus-5-5` (Claude Code subagents, 7 runs of 4–6 scans), 2026-11-12. Cloud model approved by the owner
for these pages because the homelab OCR service was unavailable.

Scans: the 37 scans where `fabric` looped or stopped early (found by `mmo ocr clean`, rules `clean-v1`, plus scans 59
and 60 with a short text): 17, 19, 24, 25, 26, 28, 38, 42, 45, 48, 49, 50, 54, 57, 58, 59, 60, 61, 62, 65, 69, 75, 94,
96, 102, 108, 111, 121, 122, 124, 125, 152, 162, 183, 185, 187, 197.

Input per scan (the original photo, EXIF orientation applied, grayscale, not rotated – the photos are upright; the
`fabric` warnings "rotated N degrees" do not hold for the stored pixels): the whole page at 1600 px and the top and
bottom 55 % at 1800 px.

Instructions given (the same for every run):

> Transcribe exactly what is printed, character by character, in Czech with all diacritics. Do not correct,
> modernise, summarise or translate. Do not add anything that is not on the page.
> First line: the running header exactly as printed, if there is one. Last line: the printed page number alone, if
> there is one.
> Body: one paragraph per line, with a blank line between paragraphs. Join the printed lines of a paragraph with
> spaces; where a word is split by a hyphen at a line end, join it without the hyphen. A paragraph cut off at the top
> or bottom of the page stays as it is.
> Footnote reference numbers in the text: Unicode superscript digits directly after the word or punctuation.
> Footnotes at the page bottom: their own lines, starting with the number.
> Headings: their own line, prefixed with `## `.
> Quotation marks as printed („…“ or "…").
> A word you truly cannot read: write `[?]` in its place. Never guess silently.

Known limits of the result: italics are not marked; closing quotation marks are written `“` on most pages but `"` on
some (the print's closing mark is ambiguous); misprints are kept as printed (e.g. "nuzným", "ze" for "za").
