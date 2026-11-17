# The source pipeline: from an original to quotations

> How a source of any kind becomes the text the analysis reads, its segments, and the quotations the analysis points
> to. Decisions: ADR 0006 (source folder), ADR 0012 (final text, segments, quotations), `docs/answers.md`
> 2026-11-17. Each step is marked **built** or **planned**; planned steps are tasks in `docs/plan.md`. The manual for
> the researcher and the analyst is `docs/source-preparation.md` of the research environment.

## Principles

1. **One contract.** Whatever the original (photos, PDF, web page, text file, transcript), the result is one
   `text.md` of the same form. Everything after it – segments, quotations, the analysis – knows only `text.md`.
2. **The program converts, not a model.** Conversion is code with tests, without AI. OCR (a model reading an image)
   is used only where there is no text layer, and every reading records who or what made it.
3. **Every word can be traced back.** A quotation leads to its place in `text.md`; the location comment above it
   leads to the page, the scan and the original file; `ingest/files.yaml` holds the file's SHA-256.
4. **Nothing is overwritten that a person decided.** Working variants stay side by side in `ingest/`; the researcher
   chooses which one becomes `text.md`; `source.yaml` and `notes.md` are written only by the researcher.
5. **Steps are resumable.** A rerun does only what is missing or changed.

## Overview

```
original files            working records                 final text            index            analysis
files/  ── 2 convert ──▶  ingest/ocr/<variant>/  ── 5 ──▶  text.md  ── 6 ──▶  segments.jsonl
           (per type)     scan-NNNN.json                      │                                 7 quotations
           3 order        ingest/text/<variant>.md            └────────── words + offsets ──────▶ (codes, memos …)
           4 clean
1 add: source.yaml, notes.md (researcher)
```

| Step | What | Command | Status |
| :--- | :--- | :--- | :--- |
| 1 | Add the source: metadata and context memo | `mmo source add` | built |
| 2 | Convert each original into working records | `mmo ingest` (photos: `mmo ocr run`) | built for photos and text files; planned for PDF, web pages, DOCX/EPUB |
| 3 | Reading order and printed page numbers | `mmo ocr numbers`, `mmo ocr order` | built (photos) |
| 4 | Clean the working text | `mmo ocr clean`, `merge`; hyphenation at step 5 | built; page furniture planned |
| 5 | Choose the variant, write the final text | `source.yaml` `text: {variant: …}`, `mmo source finalize` | built |
| 6 | Cut the final text into segments | done by `finalize`; again with `mmo segment` | built |
| 7 | Quotations: store and check what the analysis points to | `mmo quote …` | planned |
| – | What a source still lacks | `mmo source check` | built |

## The source folder

```
topics/<slug>/sources/<id>/
  source.yaml          RESEARCHER  metadata (step 1)
  notes.md             RESEARCHER  context memo: why the source is here, how it came about
  files/               originals as received (images, PDF, saved web page …); large files git-ignored
  ingest/              MACHINE, never edited by hand
    files.yaml           every original: scan number, file name, SHA-256
    ocr/<variant>/scan-NNNN.json   working records, one per unit (page, file)
    page-numbers.json    printed page numbers read from the page edges (photos)
    order/<variant>.yaml reading order report (photos)
    text/<variant>.md    the whole text of one working variant, for reading and comparing
  text.md              FINAL: the only text the analysis reads (step 5)
  segments.jsonl       index of text.md: its paragraphs (step 6)
  ground-truth/scan-NNNN.txt   optional hand-corrected text for measuring OCR
```

In the research environment a study's `sources/` may be kept out of git (`topics/.gitignore`); then it needs a backup
of its own.

## Step 1 – Add the source (built)

`mmo source add <topic> <id> --kind <kind> [--role context --about <id>]` creates `source.yaml` and `notes.md`. The
fields of `source.yaml` are in `docs/spec.md` (section Topic folder): identity, kind, role, citation, attributes,
the research questions it serves, page-number fixes, retakes, the chosen variant. They are the researcher's.

**Open (to discuss with the owner):** whether a model may *propose* bibliographic fields (authors, year, publisher,
ISBN) from the imprint page or the publisher's annotation. If it does, the proposal is marked as a proposal and the
researcher confirms it; the program never writes it into `source.yaml` by itself.

## Step 2 – Convert (built for photos and text files; others planned)

Each kind of original has its converter. Every converter writes **working records** of the same shape, one per unit,
so the later steps do not care where the text came from:

```json
{"source": "kniha", "scan": 1, "image": "IMG_20260902_195453.jpg", "image_sha256": "…",
 "backend": "fabric", "model": "…", "prompt_version": "…", "confidence": null, "quality": "…",
 "warnings": [], "seconds": 4.2, "created": "2026-11-12T…", "text": "…"}
```

`scan` is the unit's position in file-name order (for a PDF: the page index; for a web page: 1); `image` names the
original file; `backend`/`model`/`prompt_version` say who or what produced the text.

| Original | Converter | Unit and location comment | Status |
| :--- | :--- | :--- | :--- |
| Photos of pages (`.jpg`, `.png`, …) | OCR backend (`tesseract`, `openai`, `fabric`); pages read later by a Claude model through `mmo ocr images` / `import` / `merge` (skill `transcribe-pages`) | one photo = one page: `<!-- page 15 (printed) · scan 1 · IMG_….jpg -->` | built |
| Text files (`.txt`, `.md`) | taken as they are, variant `original` | one file: `<!-- file part-1.txt · scan 1 -->` | built |
| PDF with a text layer (e-book, article) | text extraction by a library (PyMuPDF or Docling – chosen in the task), no OCR | one PDF page: `<!-- page 15 (printed) · pdf 17 · kniha.pdf -->`; the printed number from the PDF's page labels or the page edge | planned |
| PDF of scans (no text layer) | pages rendered to images, then the photo path | as photos, plus `pdf <n>` | planned |
| Web page (review, interview, announcement) | `mmo source fetch <url>` saves a snapshot (HTML, date, SHA-256) into `files/`; main-text extraction (e.g. trafilatura); a page saved by hand works the same | one page: `<!-- web <file> · scan 1 -->`; headings of the article stay as headings | planned |
| DOCX, EPUB | conversion to Markdown (e.g. pandoc) | one file or one chapter: `<!-- file … · scan n -->` / `<!-- chapter … -->` | planned |
| Audio or video interview | out of scope now; a transcript enters as a text file | – | – |

A converter that cannot read part of a unit writes `[?]` for each unreadable word and a warning in the record; it
never guesses words.

## Step 3 – Reading order and page numbers (built for photos)

Only photos need it: their file order is the order they were taken, not the order of the book. `mmo ocr numbers`
reads the printed page number from the top and bottom edge of each photo; `mmo ocr order` sorts by it (a number set
by hand in `source.yaml` wins; a missing number between two known ones is inferred; retakes are left out) and reports
missing pages, numbers found twice and pages without a number. Text files keep file-name order. A PDF has its own
order; its printed numbers come from page labels.

## Step 4 – Clean (built; page furniture planned)

- **OCR junk** – `mmo ocr clean` removes loops and junk by rules into `<variant>-clean` and lists stuck pages;
  `mmo ocr merge` combines variants page by page (e.g. a Claude reading where the OCR failed).
- **Hyphenation** – a word split by a hyphen at a line end is joined when `text.md` is written (step 5); a hyphen
  before a capital stays (`Rakousko-Uhersko`). The working variant keeps what was read.
- **Page furniture (planned)** – running heads (the book's title or the chapter's title at the top of a page) and
  printed page numbers are not content. In the first book they are inside `text.md`: of its 1,581 segments 478 are
  shorter than 40 characters, mostly running heads (`NAZÍ V AI DOBĚ` 89×, chapter titles) and lone page numbers, and
  a running head is glued to the first paragraph of a page. A rule step will mark or remove them before `text.md` is
  written; the page number stays in the location comment. Footnotes stay text but should become recognisable.

## Step 5 – The final text `text.md` (built)

The researcher names the variant good enough for the analysis in `source.yaml`:

```yaml
text:
  variant: book
```

`mmo source finalize <topic> <source>` writes `text.md` and cuts its segments (step 6). It is never edited by hand;
a correction goes into a working variant (or a new one, e.g. pages read again) and `finalize` runs again.

### The format (the contract)

```
---
source: "kniha"
title: "Nazí v AI době"
status: "final - the text for the analysis"
variant: "book"
built: "2026-11-13"
pages: 211
printed_pages: "15-235"
missing_pages: "1-14, 17-19, 56"
pages_without_number: ["scan 213 IMG_….jpg"]
unclear_words: 6
read_by: {"claude-opus-5-5": 45, "claude-sonnet-5-5": 166}
---

> Final text of `kniha` for the analysis. Do not edit by hand: …

# Nazí v AI době

<!-- page 15 (printed) · scan 1 · IMG_20260902_195453.jpg -->

First paragraph of the page …

Second paragraph …

<!-- page 16 (manual) · scan 2 · IMG_20260902_195457.jpg -->

…
```

- **Header** (front matter, one JSON value per line): technical facts written by the program – `source`, `title`,
  `status`, `variant`, `built`, `pages` (units in the text), and for paged sources `printed_pages`,
  `missing_pages` (including those before the first one), `pages_without_number`; `unclear_words` (count of `[?]`);
  `read_by` (pages per model or backend). Bibliographic facts are not here; they are in `source.yaml`.
- **Note and title** – one quoted line saying what the file is, then `# <title>`. Text before the first location
  comment belongs to no place and is never segmented or quoted.
- **Location comment** – one line `<!-- … -->` before the text of each unit; its parts are separated by ` · `:
  `page <n> (<how>)` with `how` = `printed` (read from the page), `manual` (set by the researcher), `inferred`
  (between two known pages), or `page ? (unknown)`; `scan <n>` (the unit's position among the originals);
  the original file name; `file <name>` for a text file. New converters add their own part (`pdf <n>`, `web <file>`)
  and keep `scan <n>`.
- **Body** – paragraphs separated by one blank line, in reading order; line breaks inside a paragraph are kept;
  Markdown headings (`## …`) where the source has headings; `[?]` for each word nobody could read.
- **Encoding** – UTF-8, `\n` line ends. Offsets everywhere count Unicode characters of the file read this way.

## Step 6 – Segments (built)

`segments.jsonl` next to `text.md`, one JSON object per line, in reading order:

```json
{"id": "kniha:s1:2", "source": "kniha", "scan": 1, "page": 15, "index": 2,
 "start": 1024, "end": 1552, "text": "Mohl jsem rozvést téma nahoty, …", "continues": false}
```

| Field | Meaning |
| :--- | :--- |
| `id` | `<source>:s<scan>:<index>` – stable while the unit's paragraphs stay as they are |
| `scan`, `page` | the place: unit number and printed page (`null` when unknown or the source has no pages) |
| `index` | paragraph number within the place, from 1 |
| `start`, `end` | offsets into `text.md`; `text` is exactly `text.md[start:end]` |
| `continues` | the paragraph has no sentence end before the next location comment – it probably goes on on the next page |

- **A segment is a paragraph of one place.** A paragraph broken by a page is two segments, the first with
  `continues: true`; a quotation can still cover both.
- **Rebuilt, not versioned.** `finalize` and `mmo segment` write the file anew. `mmo source check` reports segments
  whose words are no longer at their offsets (`text.md` changed). Nothing durable points to a segment id alone:
  durable references are quotations (step 7).
- **What they are for:** reading in passages, giving a model a batch instead of the whole book, knowing which
  passages were read or coded, counting (code × place × source), and export to QDA tools.

## Step 7 – Quotations (planned)

A quotation is what a code, reading, memo, proposition or context statement points to. Planned record (stored with
the analytic output that uses it):

```yaml
quotation:
  source: kniha
  start: 1042          # offsets in text.md (inside the segment kniha:s1:2)
  end: 1101
  pages: [15]          # from the location comments the span crosses
  scans: [1]
  exact: "téma nahoty, kterou vnímám jako upřímný a osvobozující stav"
  text_md: {variant: book, built: "2026-11-13"}   # which text.md it was taken from
```

- **Creating:** the analyst (person or model) gives the source and the exact words, optionally a hint where (page or
  segment). The program finds the words in `text.md`, fills offsets, pages and scans, and refuses the quotation when
  the words are not there or are there more than once without a hint. A model never writes offsets by itself.
- **Across a page break:** the words may run over a location comment; the comment is not part of `exact`, and
  `pages` lists both pages. Whitespace (a line break against a space) is compared loosely; letters, punctuation and
  `[?]` exactly.
- **Checking:** before storing, and in a check over a study, the program verifies that `exact` is at
  `start`–`end`. After `text.md` is rebuilt (a page read again), it finds the words again and updates the offsets;
  a quotation whose words are gone is reported for the researcher, never silently dropped or moved.
- **Several per statement:** a code, scheme or proposition carries a list (evidence; for propositions also
  counter-evidence), possibly from several sources.
- **Standards:** W3C Web Annotation `oa:TextQuoteSelector` (`exact`, with prefix and suffix if needed) plus
  `oa:TextPositionSelector` (`start`, `end`) on the source's `text.md`; REFI-QDA exports it as a coded selection;
  ATLAS.ti calls it a quotation.

## Checks

`mmo source check <topic> [<source>]` lists in plain words what a source lacks: metadata, the context memo, ingest
not run, the variant not chosen, `text.md` not built, segments not cut or not matching `text.md`, problems of the
reading order, stuck OCR pages. After `finalize` the researcher reads a few pages of `text.md` against the originals.

## Walk-throughs

**A new book as photos (built):** `source add` → photos into `files/` → `mmo ingest --backend fabric` (OCR, page
numbers, order, working text) → fix page numbers in `source.yaml`, read missing or bad pages again with a Claude
model (`transcribe-pages`) → choose the variant → `source finalize` (text.md + segments) → `source check`.

**A new book as a PDF (planned):** `source add` → PDF into `files/` → `mmo ingest` detects a text layer and extracts
page by page with page labels (or renders and OCRs a scanned PDF) → page furniture removed by rules → choose the
variant → `source finalize` → `source check`. No model is needed unless pages are scans.

**A review on the web (planned):** `source add --role context --about kniha` → `mmo source fetch <url>` saves a dated
snapshot into `files/` (or the researcher saves the page) → main text extracted into the variant `web` →
`source finalize` → `source check`. The URL and the access date go to `citation` in `source.yaml`.

## Commands

```bash
uv run mmo source add <topic> <id> --kind book --title "…"
uv run mmo ingest <topic> <id> --backend fabric          # photos; text files need no backend
uv run mmo ocr order <topic> <id> --variant fabric        # single steps, see docs/source-preparation.md
uv run mmo source finalize <topic> <id>                   # text.md and segments.jsonl
uv run mmo segment <topic> <id>                           # cut segments again
uv run mmo source check <topic> [<id>]
```
