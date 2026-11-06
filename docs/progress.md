# Progress

> One entry per finished step, newest last: what was done, how it was verified, what the next session must know.

## T1 – 2026-11-06
- Done: repository rendered from the Project Lab template (`honzapetr/aiops-homelab`, `fabric/services/project-lab`,
  language python) and extended: `mmo` CLI (topics, source manifest, OCR with `tesseract` and OpenAI-compatible
  backends, CER comparison, segmentation), LinkML draft `ontology/schema/mmo.yaml` + `ontology/mapping.md`, method
  modules `methods/grounded-theory.yaml` and `methods/thematic-analysis.yaml`, skill `ingest-sources`, sample topic
  `topics/sample-masaryk-suicide`, brief, answers, spec, plan, ADRs 0002-0004.
- Verified: `uv run pytest` (27 passed), `ruff check`, `ruff format --check`, `tools/agents_sync.py --check`.
  OCR backends were tested with fakes only: no Tesseract binary and no homelab access in the cloud session.
- Next: T2 on the owner's computer – install `tesseract-ocr tesseract-ocr-ces`, fill `.env` from `.env.example`
  (gateway URL, key, a vision model), put sample scans into `topics/<topic>/sources/<id>/` and follow the
  `ingest-sources` skill. `.copier-answers.yml` was not kept (it pointed to a temporary path); the lab import adds
  what it needs. Project Lab requires the default branch `main`.
