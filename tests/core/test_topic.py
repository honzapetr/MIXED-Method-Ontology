from pathlib import Path

import pytest
import yaml

from mmo.core.topic import Topic, natural_key


def test_natural_key_orders_numbers() -> None:
    names = ["page-10.jpg", "page-2.jpg", "page-1.jpg"]
    assert sorted(names, key=natural_key) == ["page-1.jpg", "page-2.jpg", "page-10.jpg"]


def test_create_and_load_topic(tmp_path: Path) -> None:
    topic = Topic.create(tmp_path, "my-topic", "My topic")
    for sub in ("sources", "memos", "graph"):
        assert (topic.root / sub).is_dir()
    assert not (topic.root / "work").exists()
    assert Topic.load(tmp_path / "my-topic").data["title"] == "My topic"
    with pytest.raises(FileExistsError):
        Topic.create(tmp_path, "my-topic", "again")


def test_invalid_slug(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        Topic.create(tmp_path, "Bad Slug", "x")


def test_manifest_records_scans_apart_from_metadata(tmp_path: Path) -> None:
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.source("book")
    source.files_dir.mkdir(parents=True)
    (source.root / "source.yaml").write_text("title: A book\n", encoding="utf-8")
    for name in ("p-10.png", "p-2.png", "notes.txt"):
        (source.files_dir / name).write_bytes(name.encode())
    manifest = source.write_manifest()
    assert [f["file"] for f in manifest["files"]] == ["p-2.png", "p-10.png", "notes.txt"]
    assert [f["scan"] for f in manifest["files"]] == [1, 2, 1], "text files are numbered apart from images"
    assert manifest["files"][2]["kind"] == "text" and "kind" not in manifest["files"][0]
    saved = yaml.safe_load(source.files_manifest.read_text(encoding="utf-8"))
    assert len(saved["files"][0]["sha256"]) == 64
    assert source.metadata() == {"title": "A book"}, "source.yaml holds only what the researcher wrote"
    assert Topic.load(topic.root).data["sources"] == ["book"]


def test_sample_topic_is_valid() -> None:
    root = Path(__file__).resolve().parent.parent / "topics"
    for path in root.glob("*/topic.yaml"):
        topic = Topic.load(path.parent)
        assert topic.data["title"]
        for source_id in topic.data.get("sources", []):
            assert (topic.root / "sources" / source_id / "source.yaml").is_file()
