"""Topics and their sources on disk (layout: docs/spec.md, section Topic folder)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import yaml

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"}
SLUG = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}[a-z0-9]$")


def natural_key(name: str) -> list[Any]:
    """Sort key that orders `page-2` before `page-10`."""
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", name)]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_slug(value: str, what: str) -> str:
    if not SLUG.match(value):
        raise ValueError(f"{what} must be lowercase letters, digits and dashes (2-64 chars): {value!r}")
    return value


@dataclass
class Page:
    number: int
    image: Path


@dataclass
class Source:
    topic: Topic
    id: str

    @property
    def root(self) -> Path:
        return self.topic.root / "sources" / self.id

    def metadata(self) -> dict[str, Any]:
        path = self.root / "source.yaml"
        if not path.is_file():
            return {}
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def images(self) -> list[Path]:
        if not self.root.is_dir():
            return []
        files = [p for p in self.root.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
        return sorted(files, key=lambda p: natural_key(p.name))

    def pages(self) -> list[Page]:
        """Pages in natural file-name order, numbered from 1 (scan order, not the printed page number)."""
        return [Page(number=i, image=image) for i, image in enumerate(self.images(), start=1)]

    def write_manifest(self) -> dict[str, Any]:
        """Record every page image with its hash in `source.yaml`, keeping the other metadata."""
        meta = self.metadata()
        meta.setdefault("id", self.id)
        meta["pages"] = [
            {"page": page.number, "file": page.image.name, "sha256": sha256_file(page.image)} for page in self.pages()
        ]
        (self.root / "source.yaml").write_text(
            yaml.safe_dump(meta, sort_keys=False, allow_unicode=True), encoding="utf-8"
        )
        return meta


@dataclass
class Topic:
    root: Path
    data: dict[str, Any] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        return self.root.name

    @classmethod
    def load(cls, root: Path) -> Topic:
        path = root / "topic.yaml"
        if not path.is_file():
            raise FileNotFoundError(f"not a topic (no topic.yaml): {root}")
        return cls(root=root, data=yaml.safe_load(path.read_text(encoding="utf-8")) or {})

    @classmethod
    def create(cls, topics_dir: Path, slug: str, title: str) -> Topic:
        root = topics_dir / check_slug(slug, "topic slug")
        if root.exists():
            raise FileExistsError(f"topic already exists: {root}")
        data = {
            "title": title,
            "created": date.today().isoformat(),
            "questions": [],
            "goals": [],
            "sources": [],
        }
        for sub in ("sources", "work", "ground-truth", "graph"):
            (root / sub).mkdir(parents=True)
            (root / sub / ".gitkeep").touch()
        (root / "topic.yaml").write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
        return cls(root=root, data=data)

    def source(self, source_id: str) -> Source:
        return Source(topic=self, id=check_slug(source_id, "source id"))

    def sources(self) -> list[Source]:
        base = self.root / "sources"
        if not base.is_dir():
            return []
        return [Source(topic=self, id=p.name) for p in sorted(base.iterdir()) if p.is_dir()]

    def ocr_dir(self, backend: str, source_id: str) -> Path:
        return self.root / "work" / "ocr" / backend / source_id

    def segments_file(self, source_id: str) -> Path:
        return self.root / "work" / "segments" / f"{source_id}.jsonl"

    def ground_truth_dir(self, source_id: str) -> Path:
        return self.root / "ground-truth" / source_id
