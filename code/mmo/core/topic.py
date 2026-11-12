"""Topics and their sources on disk (layout: docs/spec.md, section Topic folder; ADR 0006).

Everything about one source lives in `sources/<id>/`: what the researcher writes (`source.yaml`, `notes.md`), the
original files (`files/`), the readable text (`text/`), segments, ground truth, and what the machine produces
(`ingest/`). A file's `scan` number is its position in file-name order - the identity of an image; `page` is the
printed page number.
"""

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
SOURCE_KINDS = ("book", "interview", "field-note", "document", "article", "web", "dataset")
ROLE_PRIMARY, ROLE_CONTEXT = "primary", "context"
ROLES = (ROLE_PRIMARY, ROLE_CONTEXT)
# fields of source.yaml, all written by the researcher (docs/spec.md, section Topic folder)
SOURCE_FIELDS = (
    "id",
    "title",
    "kind",
    "role",
    "about",
    "language",
    "citation",
    "attributes",
    "questions",
    "printed_pages",
    "note",
)
NOTES_TEMPLATE = """# {title}

Context memo, written by the researcher: why this source is in the topic, how it came about, what to keep in mind
when reading it.
"""


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


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def variant_name(name: str) -> str:
    if not name or "/" in name or "\\" in name or name.startswith("."):
        raise ValueError(f"not a variant name: {name!r}")
    return name


@dataclass
class Page:
    scan: int  # position in file-name order, from 1 - not the printed page number
    image: Path


@dataclass
class Source:
    topic: Topic
    id: str

    # --- folders and files (docs/spec.md, section Topic folder)

    @property
    def root(self) -> Path:
        return self.topic.root / "sources" / self.id

    @property
    def metadata_file(self) -> Path:
        return self.root / "source.yaml"

    @property
    def notes_file(self) -> Path:
        return self.root / "notes.md"

    @property
    def files_dir(self) -> Path:
        return self.root / "files"

    @property
    def ingest_dir(self) -> Path:
        return self.root / "ingest"

    @property
    def files_manifest(self) -> Path:
        return self.ingest_dir / "files.yaml"

    @property
    def numbers_file(self) -> Path:
        return self.ingest_dir / "page-numbers.json"

    @property
    def ground_truth_dir(self) -> Path:
        return self.root / "ground-truth"

    def ocr_dir(self, variant: str) -> Path:
        return self.ingest_dir / "ocr" / variant_name(variant)

    def ocr_variants(self) -> list[str]:
        base = self.ingest_dir / "ocr"
        return sorted(p.name for p in base.iterdir() if p.is_dir()) if base.is_dir() else []

    def order_file(self, variant: str) -> Path:
        return self.ingest_dir / "order" / f"{variant_name(variant)}.yaml"

    def text_file(self, variant: str) -> Path:
        return self.root / "text" / f"{variant_name(variant)}.md"

    def segments_file(self, variant: str) -> Path:
        return self.root / "segments" / f"{variant_name(variant)}.jsonl"

    # --- what the researcher writes

    def metadata(self) -> dict[str, Any]:
        return read_yaml(self.metadata_file)

    @property
    def title(self) -> str:
        return str(self.metadata().get("title") or self.id)

    def manual_page_numbers(self) -> dict[str, int]:
        """`printed_pages` of `source.yaml`: image file name -> printed page number, set by hand where OCR failed."""
        return {str(name): int(number) for name, number in (self.metadata().get("printed_pages") or {}).items()}

    # --- original files

    def images(self) -> list[Path]:
        if not self.files_dir.is_dir():
            return []
        files = [p for p in self.files_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES]
        return sorted(files, key=lambda p: natural_key(p.name))

    def pages(self) -> list[Page]:
        """Page images in natural file-name order, numbered from 1 (scan order, not the printed page number)."""
        return [Page(scan=i, image=image) for i, image in enumerate(self.images(), start=1)]

    def write_manifest(self) -> dict[str, Any]:
        """Record every original image with its scan number and hash in `ingest/files.yaml`."""
        manifest = {
            "source": self.id,
            "files": [
                {"scan": page.scan, "file": page.image.name, "sha256": sha256_file(page.image)} for page in self.pages()
            ],
        }
        write_yaml(self.files_manifest, manifest)
        self.topic.register_source(self.id)
        return manifest


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
        return cls(root=root, data=read_yaml(path))

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
        for sub in ("sources", "memos", "graph"):
            (root / sub).mkdir(parents=True)
            (root / sub / ".gitkeep").touch()
        write_yaml(root / "topic.yaml", data)
        return cls(root=root, data=data)

    def save(self) -> None:
        write_yaml(self.root / "topic.yaml", self.data)

    def register_source(self, source_id: str) -> None:
        """Add a source id to `sources` in `topic.yaml` (kept sorted, once)."""
        listed = [str(s) for s in self.data.get("sources") or []]
        if source_id not in listed:
            self.data["sources"] = sorted([*listed, source_id])
            self.save()

    def source(self, source_id: str) -> Source:
        return Source(topic=self, id=check_slug(source_id, "source id"))

    def sources(self) -> list[Source]:
        base = self.root / "sources"
        if not base.is_dir():
            return []
        return [Source(topic=self, id=p.name) for p in sorted(base.iterdir()) if p.is_dir()]
