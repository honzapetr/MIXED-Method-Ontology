import json
from pathlib import Path

import yaml

from mmo.cli import main
from mmo.core.migrate import migrate_topic, needs_migration
from mmo.core.topic import Topic
from mmo.ingest.ocr import load_pages


def old_topic(tmp_path: Path) -> Topic:
    """A topic as T1-T2a wrote it: results by processing step under work/."""
    root = tmp_path / "t1"
    for sub in ("sources", "work", "ground-truth", "graph"):
        (root / sub).mkdir(parents=True)
        (root / sub / ".gitkeep").touch()
    (root / "topic.yaml").write_text("title: T\nsources: []\n", encoding="utf-8")
    source = root / "sources" / "book"
    source.mkdir()
    (source / "IMG_1.jpg").write_bytes(b"one")
    meta = {
        "id": "book",
        "title": "Kniha",
        "pages": [
            {"page": 1, "file": "IMG_1.jpg", "sha256": "a" * 64},
            {"page": 2, "file": "IMG_2.jpg", "sha256": "b" * 64},  # not present here: git-ignored elsewhere
        ],
        "printed_pages": {"IMG_2.jpg": 8},
    }
    (source / "source.yaml").write_text(yaml.safe_dump(meta, sort_keys=False), encoding="utf-8")
    ocr = root / "work" / "ocr" / "fabric" / "book"
    ocr.mkdir(parents=True)
    for page, text in ((1, "První strana.\n\n7"), (2, "Druhá 2013 „uvozovky“.")):
        record = {"source": "book", "page": page, "image": f"IMG_{page}.jpg", "image_sha256": "c" * 64,
                  "backend": "fabric", "seconds": 11.52, "text": text}  # fmt: skip
        (ocr / f"page-{page:04d}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", "utf-8")
    (root / "work" / "numbers").mkdir()
    (root / "work" / "numbers" / "book.json").write_text('{"pages": {}}\n', encoding="utf-8")
    (root / "work" / "order" / "fabric").mkdir(parents=True)
    (root / "work" / "order" / "fabric" / "book.yaml").write_text("variant: fabric\n", encoding="utf-8")
    (root / "work" / "text" / "fabric").mkdir(parents=True)
    (root / "work" / "text" / "fabric" / "book.md").write_text("# Kniha\n", encoding="utf-8")
    (root / "work" / "segments").mkdir()
    segment = {"id": "book:p1:1", "source": "book", "page": 1, "index": 1, "start": 0, "end": 13,
               "text": "První strana.", "backend": "fabric", "continues": False}  # fmt: skip
    (root / "work" / "segments" / "book.jsonl").write_text(json.dumps(segment, ensure_ascii=False) + "\n", "utf-8")
    (root / "ground-truth" / "book").mkdir()
    (root / "ground-truth" / "book" / "page-0001.txt").write_text("První strana.", encoding="utf-8")
    return Topic.load(root)


def test_migration_moves_everything_into_the_source_folder(tmp_path: Path) -> None:
    topic = old_topic(tmp_path)
    before = {(r["page"], r["text"], r["image_sha256"], r["seconds"]) for r in load_pages_raw(topic)}
    assert needs_migration(topic)

    migrate_topic(topic, log=lambda _: None)

    source = topic.source("book")
    assert not (topic.root / "work").exists() and not (topic.root / "ground-truth").exists()
    assert (topic.root / "memos").is_dir() and source.notes_file.read_text(encoding="utf-8").startswith("# Kniha")
    assert (source.files_dir / "IMG_1.jpg").read_bytes() == b"one"
    assert source.metadata() == {"id": "book", "title": "Kniha", "printed_pages": {"IMG_2.jpg": 8}}
    files = yaml.safe_load(source.files_manifest.read_text(encoding="utf-8"))["files"]
    assert files[1] == {"scan": 2, "file": "IMG_2.jpg", "sha256": "b" * 64}, "hashes come from the old manifest"
    after = {(r["scan"], r["text"], r["image_sha256"], r["seconds"]) for r in load_pages(source.ocr_dir("fabric"))}
    assert after == before, "OCR text and provenance are unchanged"
    record = (source.ocr_dir("fabric") / "scan-0002.json").read_text(encoding="utf-8")
    assert record.startswith('{\n  "source": "book",\n  "scan": 2,') and "„uvozovky“" in record
    assert source.numbers_file.is_file() and source.order_file("fabric").is_file()
    assert source.text_file("fabric").read_text(encoding="utf-8") == "# Kniha\n"
    segment = json.loads(source.segments_file("fabric").read_text(encoding="utf-8"))
    assert segment["id"] == "book:s1:1" and segment["scan"] == 1
    assert (source.ground_truth_dir / "scan-0001.txt").read_text(encoding="utf-8") == "První strana."
    assert Topic.load(topic.root).data["sources"] == ["book"]
    assert not needs_migration(Topic.load(topic.root))


def load_pages_raw(topic: Topic) -> list[dict]:
    folder = topic.root / "work" / "ocr" / "fabric" / "book"
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(folder.glob("page-*.json"))]


def test_second_migration_changes_nothing(tmp_path: Path) -> None:
    topic = old_topic(tmp_path)
    migrate_topic(topic, log=lambda _: None)
    snapshot = {p: p.read_bytes() for p in topic.root.rglob("*") if p.is_file()}
    migrate_topic(Topic.load(topic.root), log=lambda _: None)
    assert {p: p.read_bytes() for p in topic.root.rglob("*") if p.is_file()} == snapshot


def test_commands_refuse_an_old_layout_and_migrate_fixes_it(tmp_path: Path, capsys) -> None:
    old_topic(tmp_path)
    args = ["--topics", str(tmp_path), "ocr", "order", "t1", "book", "--variant", "fabric"]
    assert main(args) == 1
    assert "mmo topic migrate t1" in capsys.readouterr().err
    assert main(["--topics", str(tmp_path), "topic", "migrate", "t1"]) == 0
    assert main(args) == 0
    assert main(["--topics", str(tmp_path), "topic", "migrate", "t1"]) == 0
    assert "already" in capsys.readouterr().out


def test_records_with_the_old_page_key_still_load(tmp_path: Path) -> None:
    (tmp_path / "page-0001.json").write_text('{"source": "b", "page": 1, "text": "x"}', encoding="utf-8")
    assert load_pages(tmp_path) == [{"source": "b", "scan": 1, "text": "x"}]
