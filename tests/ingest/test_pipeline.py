import json
from pathlib import Path

import pytest
import yaml
from PIL import Image

from mmo.cli import main
from mmo.core.check import check_source
from mmo.core.topic import Topic
from mmo.ingest.ocr import OcrResult
from mmo.ingest.pipeline import TEXT_VARIANT, ingest_source, write_final_text

PAGES = {"IMG_1.png": "Konec odstavce.\n\n12", "IMG_2.png": "Začátek knihy,\n\n11", "IMG_3.png": "Obrázek."}


class FakeBackend:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[str] = []

    def recognize(self, image: Path) -> OcrResult:
        self.calls.append(image.name)
        return OcrResult(text=PAGES[image.name], model="fake-1")


class FakeNumbers:
    name = "fake-numbers"

    def read(self, edges: bytes) -> int | None:
        return None  # numbers come from the text in this test


def topic_with_book(tmp_path: Path) -> Topic:
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.add_source("kniha", "book", title="Kniha", language="ces")
    for width, name in enumerate(PAGES, start=300):
        Image.new("RGB", (width, 400), "white").save(source.files_dir / name)
    return topic


def test_add_source_creates_the_researcher_files(tmp_path: Path) -> None:
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.add_source("kniha", "book", title="Kniha")
    assert source.files_dir.is_dir() and source.notes_file.read_text(encoding="utf-8").startswith("# Kniha")
    assert source.metadata() == {
        "id": "kniha",
        "title": "Kniha",
        "kind": "book",
        "role": "primary",
        "citation": {},
        "attributes": {},
        "questions": [],
    }
    assert Topic.load(topic.root).data["sources"] == ["kniha"]
    context = topic.add_source("recenze", "article", role="context", about=["kniha"])
    assert context.metadata()["about"] == ["kniha"]
    assert Topic.load(topic.root).data["sources"] == ["kniha", "recenze"]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"kind": "poem"}, "unknown kind"),
        ({"kind": "article", "role": "context"}, "needs --about"),
        ({"kind": "article", "role": "context", "about": ["nothing"]}, "unknown sources: nothing"),
        ({"kind": "article", "about": ["kniha"]}, "for context sources"),
    ],
)
def test_add_source_validates(tmp_path: Path, kwargs: dict, message: str) -> None:
    topic = topic_with_book(tmp_path)
    with pytest.raises(ValueError, match=message):
        topic.add_source("x1", **kwargs)
    with pytest.raises(FileExistsError):
        topic.add_source("kniha", "book")


def test_ingest_runs_every_step_and_is_resumable(tmp_path: Path) -> None:
    source = topic_with_book(tmp_path).source("kniha")
    backend = FakeBackend()
    report = ingest_source(source, backend, "fake", numbers=FakeNumbers(), log=lambda _: None)

    assert sorted(backend.calls) == ["IMG_1.png", "IMG_2.png", "IMG_3.png"]
    assert len(yaml.safe_load(source.files_manifest.read_text(encoding="utf-8"))["files"]) == 3
    assert json.loads(source.numbers_file.read_text(encoding="utf-8"))["reader"] == "fake-numbers"
    order = yaml.safe_load(source.order_file("fake").read_text(encoding="utf-8"))
    assert [e["scan"] for e in order["order"]] == [2, 3, 1], "scan 3 has no number: it follows scan 2"
    assert source.text_file("fake").read_text(encoding="utf-8").startswith("# Kniha")
    assert not source.segments_file.exists(), "segments are cut from text.md, after the researcher chose the variant"
    assert report.variants == ["fake"]
    assert any("1 pages without a number" in line for line in report.review)
    assert any("mmo source finalize t1 kniha" in line for line in report.review)

    source.metadata_file.write_text("id: kniha\ntitle: Kniha\ntext: {variant: fake}\n", encoding="utf-8")
    _variant, _order, count = write_final_text(source)
    first = json.loads(source.segments_file.read_text(encoding="utf-8").splitlines()[0])
    assert first["id"] == "kniha:s2:1" and first["page"] == 11 and count == 3, "page numbers are not segments"
    furniture = yaml.safe_load(source.furniture_file("fake").read_text(encoding="utf-8"))
    assert furniture["summary"] == {"running head": 0, "page number": 2}
    text = source.final_text_file.read_text(encoding="utf-8")
    assert text[first["start"] : first["end"]] == first["text"], "offsets point into text.md"

    again = FakeBackend()
    ingest_source(source, again, "fake", numbers=FakeNumbers(), log=lambda _: None)
    assert again.calls == [], "a rerun reads only what is missing"


def test_text_files_are_taken_without_ocr(tmp_path: Path) -> None:
    topic = topic_with_book(tmp_path)
    source = topic.add_source("rozhovor", "interview", title="Rozhovor s autorem", role="context", about=["kniha"])
    (source.files_dir / "part-2.md").write_text("Druhá část.\n\n15\n", encoding="utf-8")
    (source.files_dir / "part-1.txt").write_text("Otázka: proč?\n\nOdpověď: protože.", encoding="utf-8")

    report = ingest_source(source, None, "unused", log=lambda _: None)

    assert report.variants == [TEXT_VARIANT] and not (source.ingest_dir / "order").exists()
    text = source.text_file(TEXT_VARIANT).read_text(encoding="utf-8")
    assert text.index("Otázka") < text.index("Druhá část"), "text files keep their file-name order"
    assert "<!-- file part-1.txt · scan 1 -->" in text
    source.metadata_file.write_text(
        source.metadata_file.read_text(encoding="utf-8") + "text: {variant: original}\n", encoding="utf-8"
    )
    write_final_text(source)
    segments = [json.loads(line) for line in source.segments_file.read_text("utf-8").splitlines()]
    assert [s["id"] for s in segments] == ["rozhovor:s1:1", "rozhovor:s1:2", "rozhovor:s2:1", "rozhovor:s2:2"]
    assert all(s["page"] is None for s in segments)
    record = json.loads((source.ocr_dir(TEXT_VARIANT) / "scan-0001.json").read_text(encoding="utf-8"))
    assert record["backend"] == TEXT_VARIANT and record["image"] == "part-1.txt" and len(record["image_sha256"]) == 64

    created = record["created"]
    (source.files_dir / "part-1.txt").write_text("Otázka: proč ne?", encoding="utf-8")
    ingest_source(source, None, "unused", log=lambda _: None)
    changed = json.loads((source.ocr_dir(TEXT_VARIANT) / "scan-0001.json").read_text(encoding="utf-8"))
    assert changed["text"] == "Otázka: proč ne?"
    unchanged = json.loads((source.ocr_dir(TEXT_VARIANT) / "scan-0002.json").read_text(encoding="utf-8"))
    assert unchanged["created"] <= changed["created"] and created <= changed["created"]


def test_images_need_a_backend(tmp_path: Path) -> None:
    source = topic_with_book(tmp_path).source("kniha")
    with pytest.raises(ValueError, match="--backend"):
        ingest_source(source, None, "x", log=lambda _: None)


def test_check_lists_what_is_missing(tmp_path: Path) -> None:
    topic = topic_with_book(tmp_path)
    topic.data["questions"] = [{"id": "q1", "text": "Proč?"}]
    topic.save()
    topic = Topic.load(topic.root)
    source = topic.source("kniha")
    findings = check_source(source)
    for expected in ("citation", "attributes", "questions", "notes.md", "ingest: not run yet"):
        assert any(f.startswith(expected) for f in findings), expected

    meta = source.metadata()
    meta.update(
        citation={"authors": ["A. Autor"], "year": 2024},
        attributes={"genre": "essay"},
        questions=["q1", "q9"],
    )
    source.metadata_file.write_text(yaml.safe_dump(meta, allow_unicode=True), encoding="utf-8")
    source.notes_file.write_text("# Kniha\n\nPůjčená z knihovny.\n", encoding="utf-8")
    ingest_source(source, FakeBackend(), "fake", log=lambda _: None)
    findings = check_source(source)
    assert findings == [
        "questions: not in topic.yaml: q9",
        "final text: choose the variant for the analysis (text: {variant: <variant>} in source.yaml), "
        "then mmo source finalize t1 kniha",
        f"reading order (fake): 1 pages without a number, 0 numbers twice - see {source.order_file('fake')}",
    ]


def test_cli_add_ingest_check(tmp_path: Path, capsys) -> None:
    topics = ["--topics", str(tmp_path)]
    assert main([*topics, "topic", "new", "t1", "--title", "T"]) == 0
    assert main([*topics, "source", "add", "t1", "kniha", "--kind", "book", "--title", "Kniha"]) == 0
    assert main([*topics, "source", "add", "t1", "recenze", "--kind", "article", "--role", "context"]) == 1
    assert "needs --about" in capsys.readouterr().err
    assert main([*topics, "source", "add", "t1", "recenze", "--kind", "article", "--role", "context",
                 "--about", "kniha"]) == 0  # fmt: skip
    (tmp_path / "t1" / "sources" / "recenze" / "files" / "recenze.md").write_text("Dobrá kniha.", encoding="utf-8")
    capsys.readouterr()
    assert main([*topics, "ingest", "t1", "recenze"]) == 0
    out = capsys.readouterr().out
    assert "original: text ->" in out and "mmo source finalize t1 recenze" in out
    assert "mmo source check t1 recenze" in out
    assert main([*topics, "source", "check", "t1"]) == 0
    out = capsys.readouterr().out
    assert "kniha (primary):" in out and "recenze (context):" in out and "files: no originals" in out


def test_finalize_writes_the_text_for_the_analysis(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    topic = topic_with_book(tmp_path)
    source = topic.source("kniha")
    ingest_source(source, FakeBackend(), "fake", numbers=FakeNumbers(), log=lambda _: None)
    assert source.text_file("fake") == source.ingest_dir / "text" / "fake.md", "working variants stay in ingest/"
    assert any("final text: choose the variant" in f for f in check_source(source))
    assert main(["--topics", str(tmp_path), "source", "finalize", "t1", "kniha"]) == 1
    assert "choose the final variant" in capsys.readouterr().err

    meta = source.metadata() | {"text": {"variant": "fake"}}
    source.metadata_file.write_text(yaml.safe_dump(meta, allow_unicode=True), encoding="utf-8")
    assert any("final text: not built yet" in f for f in check_source(source))
    assert main(["--topics", str(tmp_path), "source", "finalize", "t1", "kniha"]) == 0
    assert "3 pages of variant fake" in capsys.readouterr().out

    text = source.final_text_file.read_text(encoding="utf-8")
    assert source.final_text_file == source.root / "text.md"
    header = yaml.safe_load(text.split("---")[1])
    assert header["variant"] == "fake" and header["pages"] == 3
    assert header["printed_pages"] == "11-12" and header["missing_pages"] == "1-10"
    assert header["pages_without_number"] == ["scan 3 IMG_3.png"]
    assert header["read_by"] == {"fake-1": 3} and header["unclear_words"] == 0
    assert header["left_out"] == {"running_heads": 0, "page_numbers": 2}
    assert "\n12\n" not in text and "\n11\n" not in text, "page numbers only in the location comments"
    assert text.index("Začátek knihy") < text.index("Obrázek.") < text.index("Konec odstavce."), "reading order"
    assert "<!-- page 11 (printed) · scan 2 · IMG_2.png -->" in text
    assert not any(f.startswith(("final text", "segments")) for f in check_source(source))

    source.final_text_file.write_text(text.replace("Začátek knihy", "Začátek celé knihy"), encoding="utf-8")
    assert any(f.startswith("segments: 3 no longer match text.md") for f in check_source(source)), "offsets shift"
    assert main(["--topics", str(tmp_path), "segment", "t1", "kniha"]) == 0
    assert not any(f.startswith("segments") for f in check_source(source))
    source.segments_file.unlink()
    assert any(f.startswith("segments: not cut yet") for f in check_source(source))


def test_final_text_joins_words_hyphenated_at_line_ends(tmp_path: Path) -> None:
    topic = topic_with_book(tmp_path)
    source = topic.source("kniha")
    out = source.ocr_dir("typed")
    out.mkdir(parents=True)
    record = {"source": "kniha", "scan": 1, "image": "IMG_1.png", "backend": "typed", "text": "spo-\nlečenský\n\n11"}
    (out / "scan-0001.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf-8")
    source.metadata_file.write_text("id: kniha\ntitle: Kniha\ntext: {variant: typed}\n", encoding="utf-8")
    write_final_text(source)
    assert "společenský" in source.final_text_file.read_text(encoding="utf-8")
    kept = json.loads((out / "scan-0001.json").read_text(encoding="utf-8"))
    assert kept["text"].startswith("spo-\nlečenský"), "the working variant is left as it was read"


def test_images_for_a_vision_model(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    topic = topic_with_book(tmp_path)
    source = topic.source("kniha")
    ingest_source(source, FakeBackend(), "fake", log=lambda _: None)
    out = tmp_path / "img"
    assert main(["--topics", str(tmp_path), "ocr", "images", "t1", "kniha", "--out", str(out), "--size", "200"]) == 0
    assert sorted(p.name for p in out.iterdir()) == ["scan-0001.jpg", "scan-0002.jpg", "scan-0003.jpg"]
    with Image.open(out / "scan-0001.jpg") as image:
        assert image.mode == "L" and max(image.size) == 200
    assert "3 images" in capsys.readouterr().out

    again = tmp_path / "img2"
    main(["--topics", str(tmp_path), "ocr", "images", "t1", "kniha", "--out", str(again), "--missing-from", "fake"])
    assert not list(again.iterdir()), "every scan already has a reading in fake"
