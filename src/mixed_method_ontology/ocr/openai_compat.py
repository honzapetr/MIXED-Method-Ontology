"""Vision models behind an OpenAI-compatible `chat/completions` endpoint.

Works with the homelab LiteLLM gateway, Ollama (`/v1`) and vLLM. Any model the endpoint serves with image input can
be tried; Claude can sit behind the same gateway. Standard library only.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import urllib.error
import urllib.request
from pathlib import Path

from mixed_method_ontology.ocr.base import OcrResult

PROMPT_VERSION = "ocr-v1"
SYSTEM_PROMPT = (
    "You are a precise OCR engine. Transcribe the text of the scanned page exactly as printed, in its original "
    "language, keeping all diacritics, punctuation and spelling, including errors. Keep the line breaks of the page. "
    "Separate paragraphs with one empty line. Put running headers, page numbers and footnotes on their own lines. "
    "Do not translate, correct, summarise or comment. Output only the transcription."
)
USER_PROMPT = "Transcribe this page."


def data_url(image: Path) -> str:
    mime = mimetypes.guess_type(image.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(image.read_bytes()).decode('ascii')}"


class OpenAICompatBackend:
    name = "openai"

    def __init__(self, base_url: str, model: str, api_key: str = "", timeout: float = 600.0) -> None:
        if not base_url:
            raise ValueError("MMO_OPENAI_BASE_URL is not set (see .env.example)")
        if not model:
            raise ValueError("no model given: pass --model or set MMO_OCR_MODEL")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def payload(self, image: Path) -> dict:
        return {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url(image)}},
                    ],
                },
            ],
        }

    def recognize(self, image: Path) -> OcrResult:
        body = json.dumps(self.payload(image)).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(f"{self.base_url}/chat/completions", data=body, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.load(response)
        except urllib.error.HTTPError as err:
            detail = err.read().decode("utf-8", "replace")[:500]
            raise RuntimeError(f"OCR request failed ({err.code}) for {image.name}: {detail}") from err
        text = data["choices"][0]["message"].get("content") or ""
        return OcrResult(text=text.strip(), model=data.get("model") or self.model, prompt_version=PROMPT_VERSION)
