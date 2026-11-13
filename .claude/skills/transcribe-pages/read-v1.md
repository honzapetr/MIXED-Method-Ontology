# Instructions `read-v1` for the reading agents

Give these to every agent word for word, followed by the image paths and the output folder.

> You transcribe photos of printed pages. For each image write `<output folder>/scan-NNNN.txt` with the same number
> as the image and nothing else; use only the file reading and writing tools.
>
> Transcribe exactly what is printed, character by character, in Czech with all diacritics. Do not correct,
> modernise, summarise or translate. Do not add anything that is not on the page.
> Line 1: `ROTATION: 0` or `ROTATION: 90cw` / `90ccw` / `180` (how the photo is rotated relative to upright text).
> Some photos are rotated by 90° (text runs vertically). Read them anyway, in the correct reading direction.
> Next line: the running header exactly as printed, if there is one. Last line: the printed page number alone, if
> there is one.
> Body: one paragraph per line, with a blank line between paragraphs. Join the printed lines of a paragraph with
> spaces; where a word is split by a hyphen at a line end, join it without the hyphen. A paragraph cut off at the
> top or bottom of the page stays as it is.
> Footnote reference numbers in the text: Unicode superscript digits directly after the word or punctuation.
> Footnotes at the page bottom: their own lines, starting with the number.
> Headings: their own line, prefixed with `## `.
> Quotation marks as printed („…“ or "…").
> A word or number you truly cannot read: write `[?]` in its place. Never guess silently, not even from a sequence.
> If the image shows no printed text page (cover, blank page, picture), write after the ROTATION line one line
> `[no text: <short description>]`, plus any printed text that is there.
> If the photo shows parts of two pages, transcribe only the main page and add a last line
> `[note: neighbouring page partly visible]`.
>
> At the end, reply with one line per scan where something was unsure (scan, what, why) - or "all clear".
