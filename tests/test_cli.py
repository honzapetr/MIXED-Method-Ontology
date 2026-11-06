import json
from pathlib import Path

from mixed_method_ontology.cli import main, ocr_backend_dir, parse_pages


def test_parse_pages() -> None:
    assert parse_pages("1-3,7") == {1, 2, 3, 7}
    assert parse_pages(None) is None


def test_variant_folder_name() -> None:
    assert ocr_backend_dir("tesseract", None) == "tesseract"
    assert ocr_backend_dir("openai", "qwen2.5-vl:7b") == "openai-qwen2.5-vl-7b"


def write_page(topic: Path, variant: str, page: int, text: str) -> None:
    out = topic / "work" / "ocr" / variant / "book"
    out.mkdir(parents=True, exist_ok=True)
    record = {"source": "book", "page": page, "backend": variant, "text": text}
    (out / f"page-{page:04d}.json").write_text(json.dumps(record), encoding="utf-8")


def test_topic_compare_and_segment(tmp_path: Path, capsys) -> None:
    assert main(["--topics", str(tmp_path), "topic", "new", "t1", "--title", "T"]) == 0
    topic = tmp_path / "t1"
    write_page(topic, "a", 1, "Ahoj světe.")
    write_page(topic, "b", 1, "Ahoj svete.")
    report = tmp_path / "report.json"
    assert main(["--topics", str(tmp_path), "ocr", "compare", "t1", "book", "--json", str(report)]) == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["b"]["reference"] == "a" and data["b"]["pages"]["1"] > 0

    truth = topic / "ground-truth" / "book"
    truth.mkdir(parents=True)
    (truth / "page-0001.txt").write_text("Ahoj světe.", encoding="utf-8")
    assert main(["--topics", str(tmp_path), "ocr", "compare", "t1", "book", "--json", str(report)]) == 0
    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["a"]["mean_cer"] == 0.0 and data["b"]["reference"] == "ground-truth"

    assert main(["--topics", str(tmp_path), "segment", "t1", "book", "--variant", "a"]) == 0
    lines = (topic / "work" / "segments" / "book.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["id"] == "book:p1:1"


def test_errors_are_reported_not_raised(tmp_path: Path, capsys) -> None:
    assert main(["--topics", str(tmp_path), "segment", "missing", "book"]) == 1
    assert "error" in capsys.readouterr().err
