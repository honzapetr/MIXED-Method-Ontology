"""The homelab AI Fabric's OCR service: photos and scans read by its OCR model, turned upright first.

The service picks the model, the prompt and the fallback (Tesseract on its CPU when the model cannot run - then
`quality` is `basic`), so this backend only sends the image and records what came back. It uses the service's own
client library `fabric-ocr` (vendored in `vendor/wheels/`, see ADR 0005). Address and token: `FABRIC_OCR_URL` and
`FABRIC_OCR_TOKEN` in `.env` or the environment, else the client's config file `~/.config/fabric-ocr/env`.
"""

from __future__ import annotations

import sys
from pathlib import Path

from fabric_ocr.cli import settings as client_settings
from fabric_ocr.client import OcrApiError, OcrClient, Source, connect

from mmo.ingest.ocr.base import OcrResult
from mmo.ingest.page_numbers import INSTRUCTION, SCHEMA

PROMPT_VERSION = "fabric-service"  # the service owns its prompt; the route it took is recorded in `model`
MODES = ("auto", "accurate", "fast")  # fast = CPU only (Tesseract), never wakes the model


class FabricOcrBackend:
    name = "fabric"

    def __init__(self, client: OcrClient, mode: str = "auto") -> None:
        if mode not in MODES:
            raise ValueError(f"unknown fabric OCR mode {mode!r}; known: {', '.join(MODES)}")
        self.client = client
        self.mode = mode

    def recognize(self, image: Path) -> OcrResult:
        try:
            answer = self.client.read(Source(data=image.read_bytes()), mode=self.mode)
        except OcrApiError as err:
            raise RuntimeError(f"OCR service failed for {image.name}: {err}") from err
        return OcrResult(
            text=str(answer.get("markdown") or "").strip(),
            model=f"fabric/{answer.get('route') or 'unknown'}",
            prompt_version=PROMPT_VERSION,
            quality=answer.get("quality"),
            warnings=[str(w) for w in answer.get("warnings") or []],
        )


class FabricPageNumbers:
    """Page numbers from the edges of a page through the service's Extract (the main model looks at the image)."""

    name = "fabric-extract"

    def __init__(self, client: OcrClient) -> None:
        self.client = client

    def read(self, edges: bytes) -> int | None:
        try:
            answer = self.client.extract(Source(data=edges), instruction=INSTRUCTION, schema=SCHEMA)
        except OcrApiError as err:
            raise RuntimeError(f"OCR service failed: {err}") from err
        page = (answer.get("data") or {}).get("page")
        return page if isinstance(page, int) and page > 0 else None


def connect_client(url: str, token: str) -> OcrClient:
    """A client on its own HTTP connection; empty `url`/`token` fall back to the client's config file."""
    url, token = client_settings({"FABRIC_OCR_URL": url, "FABRIC_OCR_TOKEN": token})
    return OcrClient(connect(url, token), on_outdated=lambda message: print(f"warning: {message}", file=sys.stderr))


def connect_backend(url: str, token: str, mode: str = "auto") -> FabricOcrBackend:
    return FabricOcrBackend(connect_client(url, token), mode)
