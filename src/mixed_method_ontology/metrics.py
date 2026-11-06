"""Text comparison for OCR evaluation."""

from __future__ import annotations

import re
import unicodedata


def normalize(text: str) -> str:
    """NFC, unified whitespace: OCR variants differ in line breaks, which should not count as errors."""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def levenshtein(a: str, b: str) -> int:
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        previous = current
    return previous[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate of `hypothesis` against `reference` after normalisation (0.0 = identical)."""
    ref, hyp = normalize(reference), normalize(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return levenshtein(ref, hyp) / len(ref)
