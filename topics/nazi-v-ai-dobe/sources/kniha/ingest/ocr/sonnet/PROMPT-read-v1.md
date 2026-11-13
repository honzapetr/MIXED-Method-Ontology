# Prompt `read-v1` – variant `sonnet`

Model: `claude-sonnet-5-5` (Claude Code subagents, batches of 10–13 scans), 2026-11-13. Cloud model approved by the
owner for the whole book (T2f). Every scan without a `claude` reading (176 of 213).

Model choice: 7 test scans, 5 with an Opus reading (`claude`) as reference. Character error rate against `claude`:
`claude-haiku-5-5` 0.68 % (left out a phrase and two words, replaced "naráz" by "najednou"), `claude-sonnet-5-5`
0.04 % (two diacritics, one quotation mark). Both read the two photos taken sideways and found every page number.
Cost about 7 000 tokens per scan with batches of 10.

Input per scan: the original photo, EXIF orientation applied, grayscale, long side 1600 px, not rotated (16 photos
are stored sideways; the model reads them as they are and reports the rotation, stored in `rotation`).

Instructions: the same as `reread-v1` (variant `claude`), plus:

> Some photos are rotated by 90° (text runs vertically). Read them anyway, in the correct reading direction.
> Line 1: `ROTATION: 0` or `ROTATION: 90cw` / `90ccw` / `180` (how the photo is rotated relative to upright text).
> A word or number you truly cannot read: write `[?]` in its place. Never guess silently, not even from a sequence.
> If the image shows no printed text page (cover, blank page, picture), write after the ROTATION line one line
> `[no text: <short description>]`, plus any printed text that is there.
> If the photo shows parts of two pages, transcribe only the main page and add a last line
> `[note: neighbouring page partly visible]`.

("not even from a sequence" was added after the first 9 batches, scans 1–118, because one run filled in footnote
numbers on scan 86 from their sequence.)

Known limits: italics are not marked; scans the models flagged for a check: 86 (footnote numbers 17–37 inferred),
115 and 117 (a partly unclear passage), 23 (header "TANEC SLUNCÍ", elsewhere "TANEC SLUNCI").
