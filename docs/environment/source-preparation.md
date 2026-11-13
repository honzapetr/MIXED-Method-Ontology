# Source preparation

> A tool of the project: it brings new material into a topic as text the analysis can read - OCR of page photos,
> reading order, final text, segments.

## Pipeline

1. **Add and inspect** – `mmo source add` creates the source (`--role context --about <id>` for supplementary
   material); the agent lists its files and proposes a parsing plan (skill `ingest-sources`). `mmo ingest` then
   runs steps 2, 3 and 5 for it in one go (resumable) and ends with what to review; text files (`.txt`, `.md`)
   skip OCR and become the variant `original`, in file-name order. `mmo source check` lists what a source
   still lacks: citation, attributes, questions, `about`, the memo, unreviewed reading-order problems.
2. **OCR** – `mmo ocr run` sends every page image to one backend and stores one JSON per page:
   `scan`, `image`, `image_sha256`, `backend`, `model`, `prompt_version`, `text`, `confidence` (if known),
   `quality` and `warnings` (if the backend reports them), `seconds`, `created`. Results of different backends live
   side by side, so variants can be compared. `scan` (formerly `page`) is the **scan number** (file-name order), the identity of an
   image; `--workers N` reads N pages at once, and a failed page does not stop the others (a rerun retries it).
3. **Order** – `mmo ocr numbers` reads the printed page number from the top and bottom edge of every image (the
   strips go to the fabric service's Extract: OCR models leave headers and footers out of the page text, Tesseract
   cannot read a lone number from a photo); results in `ingest/page-numbers.json` of the source, resumable. `mmo ocr order` takes
   that number, else a line that is only a number among the first or last three lines of the OCR text (for an
   imported transcription of the whole page the other way round: its own number first), and sorts the pages by it.
   Photos listed in `retakes` are left out. A page without a number between two pages two apart gets
   the number between them (`inferred`); a number set by hand in `source.yaml` (`printed_pages: {<image>: <page>}`)
   wins (`manual`); other pages stay `unknown` and follow the page photographed before them. The report lists missing
   pages, numbers found twice (a retaken photo or a misread number) and unknown pages. `mmo ocr book` writes the whole
   text in that order, each page under a comment with its printed number, scan number and image.
   **Final text.** The researcher names the variant that is good enough in `source.yaml` (`text: {variant: ...}`);
   `mmo source finalize` writes `text.md` next to `source.yaml`: a header (variant, date, pages, printed range,
   missing pages including those before the first one, pages without a number, count of `[?]`, which models read
   the pages) and the variant's text in reading order with the same page comments. It is the only text the analysis
   reads; working variants stay in `ingest/`. Pages read later with a Claude model go through `mmo ocr images`,
   `mmo ocr import`, `mmo ocr merge` and `mmo source finalize` again (skill `transcribe-pages`).
4. **Compare** – `mmo ocr compare` reports the character error rate (CER) of each backend against ground truth when
   it exists, otherwise between two backends.
5. **Segment** – `mmo segment` joins the text of one backend's pages in reading order, repairs words hyphenated across line ends and
   splits paragraphs into segments with ids `<source>:s<scan>:<n>` and character offsets into the scan's text.

## OCR backends

| Backend | How | Notes |
| :--- | :--- | :--- |
| `tesseract` | local `tesseract` binary, language `ces` by default | free, offline baseline; needs `tesseract-ocr-ces` |
| `openai` | OpenAI-compatible `chat/completions` with the image as a data URL | the homelab LiteLLM gateway, Ollama or vLLM; Claude can sit behind the same gateway |
| `fabric` | the homelab AI Fabric's OCR service through its client library `fabric-ocr` (ADR 0005) | the service turns photos upright, reads them with its OCR model (started on demand) and falls back to Tesseract (`quality: basic`); `--mode fast` = CPU only; 2 pages at once |

Backends are registered in `code/mmo/ingest/ocr/`; a new one implements `OcrBackend.recognize()`.

## Single steps

```bash
sudo apt install tesseract-ocr tesseract-ocr-ces   # only for the tesseract backend
# single steps, e.g. to compare OCR variants on a sample
uv run mmo ocr run my-topic my-book --backend tesseract --scans 1-10
uv run mmo ocr run my-topic my-book --backend openai --model <vision-model> --scans 1-10
uv run mmo ocr run my-topic my-book --backend fabric --workers 2   # the homelab OCR service (ADR 0005)
uv run mmo ocr compare my-topic my-book          # add sources/my-book/ground-truth/scan-0001.txt for real CER
uv run mmo ocr numbers my-topic my-book                  # printed page numbers from the page edges
uv run mmo ocr order my-topic my-book --variant fabric   # reading order by printed page numbers
uv run mmo ocr book my-topic my-book --variant fabric    # whole text in reading order -> ingest/text/fabric.md
uv run mmo source finalize my-topic my-book   # text.md for the analysis, from `text: {variant: ...}` in source.yaml
uv run mmo segment my-topic my-book --variant tesseract
```

## OCR through the homelab (backend `fabric`)

The owner's AI Fabric runs an OCR service (dots.ocr for photos and scans, the main model for page numbers). This
project uses it through its client library `fabric-ocr`, vendored in `vendor/wheels/` (ADR 0005), so installing the
project needs no homelab access (CI on GitHub's runners works); **calling** the service works only from the owner's
LAN or VPN.

`uv run mmo ingest <topic> <source> --backend fabric` runs all of it; the steps one by one:

| Step | Command | Result |
| :--- | :--- | :--- |
| page text | `uv run mmo ocr run <topic> <source> --backend fabric --workers 2` | `sources/<source>/ingest/ocr/fabric/scan-NNNN.json` |
| page numbers | `uv run mmo ocr numbers <topic> <source>` | `sources/<source>/ingest/page-numbers.json` |
| reading order | `uv run mmo ocr order <topic> <source> --variant fabric` | `sources/<source>/ingest/order/fabric.yaml` + a report of gaps, duplicates and pages without a number |
| whole text | `uv run mmo ocr book <topic> <source> --variant fabric` | `sources/<source>/ingest/text/fabric.md` in reading order |
| final text | `uv run mmo source finalize <topic> <source>` | `sources/<source>/text.md`, the text the analysis reads, from the variant chosen in `source.yaml` (`text: {variant: ...}`) |

Every step saves page by page; a rerun reads only what is missing, so an interrupted run is simply started again.
Fix page numbers by hand with `printed_pages: {<image>: <page>}` in `source.yaml`, then run `mmo ingest` again.
How it works: section Pipeline above; the first book: `docs/progress.md` (T2a).

**Setup on the owner's Windows computer:**

1. **uv 0.13 or newer** - older uv (0.6.8 was installed) cannot resolve the relative flat index `./vendor/wheels` and
   `uv sync` fails. Run `uv self update`, or call `uvx --from uv==0.13.5 uv ...`.
2. **Keep the virtual environment off Google Drive** - creating `.venv` on `G:` is very slow. Set
   `UV_PROJECT_ENVIRONMENT` to a folder on `C:` (e.g. `C:/Users/<you>/.venvs/mmo`).
3. **Address and token** come from `~/.config/fabric-ocr/env` (`FABRIC_OCR_URL`, `FABRIC_OCR_TOKEN`; the owner's is
   already set, token `cli-vlastnik`), or from `FABRIC_OCR_URL` / `FABRIC_OCR_TOKEN` in `.env` (`.env.example`).

Agents follow the skill `ingest-sources` (`.agents/skills/`) for this workflow.
