# Topics

One folder per research topic (layout: `docs/spec.md`, section Topic folder). Create one with
`uv run mmo topic new <slug> --title "..."`.

Everything about one source is in `sources/<id>/` (ADR 0006):

| Path | Who writes it | What |
| :--- | :--- | :--- |
| `source.yaml` | researcher | title, kind, role (`primary` / `context`), citation, attributes, questions, page-number fixes, the final variant |
| `notes.md` | researcher | context memo: why the source is here, how it came about |
| `files/` | researcher | the original files; page images are git-ignored |
| `text.md` | machine, from the researcher's choice | **the final text for the analysis**: the variant named in `text` of `source.yaml`, with a header of what is missing (`mmo source finalize`) |
| `segments/<variant>.jsonl` | machine | paragraphs with exact positions, the unit of analysis |
| `ground-truth/scan-NNNN.txt` | researcher | hand-corrected scans for measuring OCR |
| `ingest/` | machine, never edited | file hashes, OCR per scan, page numbers, reading-order reports, the text of every working variant (`ingest/text/`) |

Supplementary material about a source (a review, an interview with the author) is a source of its own with
`role: context` and `about: [<id>]`. Topic memos go to `memos/`. A topic from before ADR 0006 is moved with
`uv run mmo topic migrate <slug>`.

Text results are committed, so variants can be compared and reviewed in git.
