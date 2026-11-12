# 5. The homelab's OCR service as a backend, its client vendored

- Status: accepted (2026-11-11)

## Context

The owner's AI Fabric (repository `honzapetr/aiops-homelab`) runs an OCR service: it turns phone photos upright,
reads them with a dedicated OCR model (dots.ocr, the winner of the owner's Czech OCR benchmark), starts that model on
demand and falls back to Tesseract when it cannot run. The service publishes a client library, `fabric-ocr`, in a
package index reachable only from the home network. This repository's CI runs on GitHub's runners, outside it.

## Decision

A third OCR backend, `fabric`, sends each page image to that service through `fabric-ocr` and stores the route,
quality and warnings it reports. The client's wheel is vendored in `vendor/wheels/` and pinned by an explicit flat uv
index (`fabric-vendor`) - the same way the Project Lab vendors Fabric clients into its projects - so `uv sync` works
in CI and in the image build without the homelab, and no PyPI package of the same name can replace it. The service's
address and token come from `.env` (`FABRIC_OCR_URL`, `FABRIC_OCR_TOKEN`) or the client's own config file.

## Consequences

One more dependency (`fabric-ocr`, which brings `httpx`). A newer client is a manual update of the wheel, the version
and the lock (`vendor/wheels/README.md`). The service owns the prompt and the model, so a result records
`fabric/<route>` rather than a model name; comparing it with other variants goes through `mmo ocr compare` as before.
