"""Local Tesseract backend: free, offline baseline. Needs the `tesseract` binary and its Czech data (`ces`)."""

from __future__ import annotations

import csv
import io
import shutil
import subprocess
from pathlib import Path

from mixed_method_ontology.ocr.base import OcrResult


def text_from_tsv(tsv: str) -> tuple[str, float | None]:
    """Rebuild text from Tesseract's TSV output: words -> lines -> paragraphs (blank line between paragraphs).

    Returns the text and the mean word confidence (None when no word has one).
    """
    paragraphs: dict[tuple[int, int, int], dict[int, list[str]]] = {}
    confidences: list[float] = []
    reader = csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE)
    for row in reader:
        if row.get("level") != "5":  # 5 = word
            continue
        word = (row.get("text") or "").strip()
        if not word:
            continue
        key = (int(row["page_num"]), int(row["block_num"]), int(row["par_num"]))
        paragraphs.setdefault(key, {}).setdefault(int(row["line_num"]), []).append(word)
        conf = float(row.get("conf") or -1)
        if conf >= 0:
            confidences.append(conf)
    blocks = []
    for key in sorted(paragraphs):
        lines = paragraphs[key]
        blocks.append("\n".join(" ".join(lines[n]) for n in sorted(lines)))
    mean = round(sum(confidences) / len(confidences), 2) if confidences else None
    return "\n\n".join(blocks), mean


class TesseractBackend:
    name = "tesseract"

    def __init__(self, cmd: str = "tesseract", lang: str = "ces", extra_args: list[str] | None = None) -> None:
        self.cmd = cmd
        self.lang = lang
        self.extra_args = extra_args or []

    def check(self) -> None:
        if shutil.which(self.cmd) is None:
            raise RuntimeError(
                f"Tesseract not found ({self.cmd!r}). "
                "Install it, e.g. `sudo apt install tesseract-ocr tesseract-ocr-ces`."
            )

    def version(self) -> str:
        out = subprocess.run([self.cmd, "--version"], capture_output=True, text=True, check=False)
        first = (out.stdout or out.stderr).splitlines()
        return first[0].strip() if first else "tesseract"

    def recognize(self, image: Path) -> OcrResult:
        self.check()
        proc = subprocess.run(
            [self.cmd, str(image), "stdout", "-l", self.lang, *self.extra_args, "tsv"],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"tesseract failed on {image}: {proc.stderr.strip()}")
        text, confidence = text_from_tsv(proc.stdout)
        return OcrResult(text=text, model=f"{self.version()} lang={self.lang}", confidence=confidence)
