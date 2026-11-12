"""Rule-based clean-up of OCR text and detection of pages where the OCR model got stuck in a loop.

Nothing is lost: every removed or shortened line is returned with the rule that removed it, so the raw text can be
restored and every decision checked. The raw OCR variant is never changed; the cleaned one is written next to it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

CLEAN_VERSION = "clean-v1"

SEPARATOR = re.compile(r"^\s*(-{3,}|\*{3,}|_{3,})\s*$")
NUMBER_ONLY = re.compile(r"^\s*\d+\s*$")
# A phrase of at least 30 characters repeated right after itself (OCR loop inside one line).
REPEATED_PHRASE = re.compile(r"(.{30,}?)(?:\s*\1)+")

NUMBER_RUN = 3  # this many number-only lines in a row are a counting loop, not page numbers
REPEATED_LINE_MIN = 20  # shorter lines may repeat legitimately ("a", "Ibid.")
STUCK_REPEATS = 3  # this many repeated lines on one page mean the model looped


@dataclass
class Removal:
    line: int  # 1-based line number in the raw text
    text: str
    rule: str  # separator / number-run / repeated-line / repeated-phrase


@dataclass
class Cleaned:
    text: str
    removed: list[Removal] = field(default_factory=list)
    stuck: list[str] = field(default_factory=list)  # why the page looks like an OCR loop; empty = fine


def _number_runs(lines: list[str]) -> set[int]:
    """Indexes of number-only lines that stand in runs of NUMBER_RUN or more (blank lines do not break a run)."""
    found: set[int] = set()
    run: list[int] = []
    for i, line in enumerate([*lines, "end"]):
        if NUMBER_ONLY.match(line):
            run.append(i)
        elif line.strip():
            if len(run) >= NUMBER_RUN:
                found.update(run)
            run = []
    return found


def clean_text(text: str) -> Cleaned:
    lines = text.splitlines()
    numbers = _number_runs(lines)
    kept: list[str] = []
    removed: list[Removal] = []
    seen: set[str] = set()
    phrases = 0
    for i, line in enumerate(lines):
        key = line.strip()
        if SEPARATOR.match(line):
            removed.append(Removal(i + 1, line, "separator"))
            continue
        if i in numbers:
            removed.append(Removal(i + 1, line, "number-run"))
            continue
        if len(key) >= REPEATED_LINE_MIN and key in seen:
            removed.append(Removal(i + 1, line, "repeated-line"))
            continue
        seen.add(key)
        shortened = REPEATED_PHRASE.sub(r"\1", line)
        if shortened != line:
            removed.append(Removal(i + 1, line, "repeated-phrase"))
            phrases += 1
            line = shortened
        kept.append(line)
    stuck: list[str] = []
    if numbers:
        stuck.append(f"{len(numbers)} number-only lines in a row")
    repeats = sum(1 for r in removed if r.rule == "repeated-line")
    if repeats >= STUCK_REPEATS:
        stuck.append(f"{repeats} repeated lines")
    if phrases:
        stuck.append(f"{phrases} lines with a repeated phrase")
    cleaned = re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip() + "\n"
    return Cleaned(cleaned, removed, stuck)


def clean_record(record: dict, variant: str, fallback: dict | None = None, fallback_variant: str | None = None) -> dict:
    """The cleaned copy of one OCR record; it takes the fallback record's text when there is one.

    A fallback is a new reading made on purpose for this scan, so it wins even when the rules found no loop: a model
    that stops early leaves a short page the rules cannot see.
    """
    result = clean_text(record["text"])
    cleaning: dict = {
        "version": CLEAN_VERSION,
        "from_variant": variant,
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "stuck": result.stuck,
        "removed": [{"line": r.line, "rule": r.rule, "text": r.text} for r in result.removed],
    }
    out = {**record, "text": result.text, "cleaning": cleaning}
    if fallback is not None:
        if fallback.get("image_sha256") and fallback["image_sha256"] != record.get("image_sha256"):
            raise ValueError(f"scan {record['scan']}: {fallback_variant} was read from a different image")
        for key in ("backend", "model", "prompt_version", "confidence", "quality", "warnings", "seconds", "created"):
            out[key] = fallback.get(key)
        out["text"] = clean_text(fallback["text"]).text
        cleaning["replaced_from"] = fallback_variant
    return out


def import_record(
    source_id: str, scan: int, image: Path, image_sha256: str, text: str, model: str, prompt: str
) -> dict:
    """An OCR record for a transcription made outside the OCR backends (by hand or by a model in a chat)."""
    return {
        "source": source_id,
        "scan": scan,
        "image": image.name,
        "image_sha256": image_sha256,
        "backend": "import",
        "model": model,
        "prompt_version": prompt,
        "confidence": None,
        "quality": None,
        "warnings": [],
        "seconds": None,
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "text": text if text.endswith("\n") else text + "\n",
    }
