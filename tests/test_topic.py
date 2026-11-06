from pathlib import Path

import pytest
import yaml

from mixed_method_ontology.topic import Topic, natural_key


def test_natural_key_orders_numbers() -> None:
    names = ["page-10.jpg", "page-2.jpg", "page-1.jpg"]
    assert sorted(names, key=natural_key) == ["page-1.jpg", "page-2.jpg", "page-10.jpg"]


def test_create_and_load_topic(tmp_path: Path) -> None:
    topic = Topic.create(tmp_path, "my-topic", "My topic")
    for sub in ("sources", "work", "ground-truth", "graph"):
        assert (topic.root / sub).is_dir()
    assert Topic.load(tmp_path / "my-topic").data["title"] == "My topic"
    with pytest.raises(FileExistsError):
        Topic.create(tmp_path, "my-topic", "again")


def test_invalid_slug(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        Topic.create(tmp_path, "Bad Slug", "x")


def test_manifest_records_pages_and_keeps_metadata(tmp_path: Path) -> None:
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.source("book")
    source.root.mkdir()
    (source.root / "source.yaml").write_text("title: A book\n", encoding="utf-8")
    for name in ("p-10.png", "p-2.png", "notes.txt"):
        (source.root / name).write_bytes(name.encode())
    meta = source.write_manifest()
    assert meta["title"] == "A book"
    assert [p["file"] for p in meta["pages"]] == ["p-2.png", "p-10.png"]
    assert [p["page"] for p in meta["pages"]] == [1, 2]
    saved = yaml.safe_load((source.root / "source.yaml").read_text(encoding="utf-8"))
    assert len(saved["pages"][0]["sha256"]) == 64


def test_sample_topic_is_valid() -> None:
    root = Path(__file__).resolve().parent.parent / "topics"
    for path in root.glob("*/topic.yaml"):
        topic = Topic.load(path.parent)
        assert topic.data["title"]
        for source_id in topic.data.get("sources", []):
            assert (topic.root / "sources" / source_id / "source.yaml").is_file()
