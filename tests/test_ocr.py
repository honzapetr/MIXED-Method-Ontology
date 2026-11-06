import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from mixed_method_ontology.config import Settings
from mixed_method_ontology.ocr import OcrResult, load_pages, make_backend, run_ocr
from mixed_method_ontology.ocr.openai_compat import PROMPT_VERSION, OpenAICompatBackend
from mixed_method_ontology.ocr.tesseract import text_from_tsv
from mixed_method_ontology.topic import Topic

TSV_HEADER = "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n"


def word(block: int, par: int, line: int, n: int, conf: float, text: str) -> str:
    return f"5\t1\t{block}\t{par}\t{line}\t{n}\t0\t0\t0\t0\t{conf}\t{text}\n"


def test_text_from_tsv_rebuilds_lines_and_paragraphs() -> None:
    tsv = (
        TSV_HEADER
        + "1\t1\t0\t0\t0\t0\t0\t0\t0\t0\t-1\t\n"
        + word(1, 1, 1, 1, 90, "První")
        + word(1, 1, 1, 2, 80, "řádek")
        + word(1, 1, 2, 1, 70, "druhý")
        + word(2, 1, 1, 1, 60, "Odstavec")
    )
    text, conf = text_from_tsv(tsv)
    assert text == "První řádek\ndruhý\n\nOdstavec"
    assert conf == 75.0


class FakeBackend:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[Path] = []

    def recognize(self, image: Path) -> OcrResult:
        self.calls.append(image)
        return OcrResult(text=f"text of {image.name}", model="fake-1")


def make_source(tmp_path: Path, pages: int):
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.source("book")
    source.root.mkdir()
    for i in range(1, pages + 1):
        (source.root / f"page-{i}.png").write_bytes(b"img%d" % i)
    return topic, source


def test_run_ocr_writes_records_and_skips_existing(tmp_path: Path) -> None:
    topic, source = make_source(tmp_path, 3)
    out = topic.ocr_dir("fake", source.id)
    backend = FakeBackend()
    run_ocr(source, backend, out, pages={1, 3}, log=lambda _: None)
    assert [p.name for p in backend.calls] == ["page-1.png", "page-3.png"]
    record = json.loads((out / "page-0001.json").read_text(encoding="utf-8"))
    assert record["text"] == "text of page-1.png"
    assert record["backend"] == "fake" and record["model"] == "fake-1"
    assert len(record["image_sha256"]) == 64
    run_ocr(source, backend, out, log=lambda _: None)
    assert [p.name for p in backend.calls][2:] == ["page-2.png"]  # pages 1 and 3 kept
    assert [r["page"] for r in load_pages(out)] == [1, 2, 3]


def test_make_backend_validates_settings() -> None:
    with pytest.raises(ValueError, match="MMO_OPENAI_BASE_URL"):
        make_backend("openai", Settings(), model="m")
    with pytest.raises(ValueError, match="model"):
        make_backend("openai", Settings(openai_base_url="http://x"))
    with pytest.raises(ValueError, match="unknown"):
        make_backend("nope", Settings())


def test_openai_backend_sends_image_and_reads_answer(tmp_path: Path) -> None:
    seen: dict = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            seen["path"] = self.path
            seen["auth"] = self.headers.get("Authorization")
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            body = json.dumps({"model": "vision-x", "choices": [{"message": {"content": " Přepis \n"}}]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        image = tmp_path / "p.png"
        image.write_bytes(b"\x89PNG")
        backend = OpenAICompatBackend(f"http://127.0.0.1:{server.server_address[1]}/v1/", "vision-x", api_key="k")
        result = backend.recognize(image)
    finally:
        server.shutdown()
    assert result.text == "Přepis"
    assert result.model == "vision-x" and result.prompt_version == PROMPT_VERSION
    assert seen["path"] == "/v1/chat/completions"
    assert seen["auth"] == "Bearer k"
    content = seen["body"]["messages"][1]["content"]
    assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_settings_env_wins_over_dotenv(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("# c\nMMO_OCR_MODEL='from-file'\nMMO_TESSERACT_LANG=ces+deu\n", encoding="utf-8")
    settings = Settings.load(env_file, environ={"MMO_OCR_MODEL": "from-env"})
    assert settings.ocr_model == "from-env"
    assert settings.tesseract_lang == "ces+deu"
