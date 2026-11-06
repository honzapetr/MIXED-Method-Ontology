# Topics

One folder per research topic (layout: `docs/spec.md`, section Topic folder). Create one with
`uv run mmo topic new <slug> --title "..."`.

Page images are git-ignored; `sources/<id>/source.yaml` keeps their hashes (`uv run mmo source scan <topic> <id>`).
OCR results (`work/ocr/`) and segments (`work/segments/`) are text and are committed, so variants can be compared
and reviewed in git.
