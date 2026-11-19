---
name: transcribe-pages
description: Read page photos of a source with a Claude model (subagents) and rebuild the final text text.md - for missing or retaken pages and for pages the reading was unsure of. Use when the owner brings more photos of a source that already has a final text, or asks to fix its transcription. Not part of the analysis.
---
# Transcribe pages with a Claude model

Text preparation, not analysis: the result is `topics/<slug>/sources/<id>/text.md`, the only text the analysis
reads. Everything else (variants, prompts, order reports) stays in `ingest/`. The tested setup (T2f, book `kniha`):
`claude-sonnet-5-5` reads well enough (0.04 % character errors against Opus; Haiku 0.68 %, it drops and replaces
words silently), about 7 000 tokens per page in batches of 10. A cloud model needs the owner's approval - ask once
per source and record it in `docs/progress.md`.

1. **New photos** go to `files/` of the source. Run `uv run mmo source scan <slug> <id>`: scan numbers follow
   file-name order, so check in `ingest/files.yaml` that the old scans kept their numbers. If they did not (a new
   file sorts before old ones), stop and ask the owner - every stored reading is keyed by scan.
2. **Images for the model:** `uv run mmo ocr images <slug> <id> --out scratch/T<n>/img --missing-from <variants>`
   (or `--scans 214-220`). Upright by EXIF, grayscale, 1600 px; photos taken sideways stay as they are.
3. **Read** with subagents (Agent tool, `model: sonnet`), 10 scans per agent, agents in parallel. Each agent gets the
   instructions in [read-v1.md](read-v1.md) word for word, the list of image paths and the output folder
   `scratch/T<n>/out/`, and writes one `scan-NNNN.txt` per scan, nothing else. When agents stop on a usage limit,
   list the scans without an output and start new agents for those only.
4. **Import** as a new variant (never into an existing one):
   `uv run mmo ocr import <slug> <id> scratch/T<n>/out --variant <name> --model claude-sonnet-5-5 --prompt-version read-v1`,
   and save the instructions next to it as `ingest/ocr/<name>/PROMPT-read-v1.md` (model, date, scans, approval).
5. **Unsure places:** `grep -l "\[?\]"` over the outputs and the agents' remarks. Look at crops of those places
   yourself (Opus) and store the corrected whole pages as a variant `<name>-check` the same way
   (`--prompt-version check-v1`, changes listed in its `PROMPT-check-v1.md`). A word that cannot be read stays `[?]`.
6. **Merge** into the variant named in `text` of `source.yaml`, checked readings first:
   `uv run mmo ocr merge <slug> <id> --variants <name>-check <name> <older variants...> --into <final>` - repeat
   the full list the previous merge used (in its records, `merged_from`), with the new variants in front.
7. **Order:** `uv run mmo ocr order <slug> <id> --variant <final>`. Missing pages, numbers found twice and pages
   without a number go to the owner; a page without a printed number gets `printed_pages`, a second photo of a page
   `retakes` in `source.yaml` - only what the text of the page proves, never a guess.
8. **Final text:** `uv run mmo source finalize <slug> <id>`, then `uv run mmo source check <slug> <id>`. Its header
   says which pages are missing and how many words are unreadable. Spot-check two new pages against the photos.
9. Record in `docs/progress.md`: scans read, model, prompt version, what the owner decided, what is still missing.

Do not edit `text.md` or any record in `ingest/` by hand; scratch files stay in `scratch/T<n>/`.
