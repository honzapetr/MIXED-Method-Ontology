import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
import pytest
from fabric_ocr.client import OcrClient

from mixed_method_ontology.config import Settings
from mixed_method_ontology.ocr import OcrResult, load_pages, make_backend, run_ocr
from mixed_method_ontology.ocr.fabric import PROMPT_VERSION as FABRIC_PROMPT_VERSION
from mixed_method_ontology.ocr.fabric import FabricOcrBackend
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


def fabric_service(answers: list[httpx.Response], seen: list[httpx.Request]) -> OcrClient:
    """The OCR service's REST API faked: each request gets the next answer."""

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return answers.pop(0)

    http = httpx.Client(base_url="http://ocr.test", transport=httpx.MockTransport(handler))
    return OcrClient(http, sleep=lambda _: None)


def test_fabric_backend_sends_the_image_and_waits_for_the_job(tmp_path: Path) -> None:
    image = tmp_path / "IMG_1.jpg"
    image.write_bytes(b"\xff\xd8photo")
    seen: list[httpx.Request] = []
    answers = [
        httpx.Response(202, json={"job_id": "j1", "state": "running"}, headers={"Retry-After": "1"}),
        httpx.Response(
            200,
            json={
                "markdown": " Text stránky\n\n15 ",
                "route": "model",
                "quality": "full",
                "warnings": ["page 1: turned 90°"],
            },
        ),
    ]
    backend = FabricOcrBackend(fabric_service(answers, seen), mode="accurate")
    result = backend.recognize(image)
    assert result.text == "Text stránky\n\n15"
    assert result.model == "fabric/model" and result.prompt_version == FABRIC_PROMPT_VERSION
    assert result.quality == "full" and result.warnings == ["page 1: turned 90°"]
    assert seen[0].url.path == "/v1/read" and seen[0].url.params["mode"] == "accurate"
    assert seen[0].content == b"\xff\xd8photo"
    assert seen[1].url.path == "/v1/jobs/j1"


def test_fabric_backend_turns_service_errors_into_runtime_errors(tmp_path: Path) -> None:
    image = tmp_path / "IMG_1.jpg"
    image.write_bytes(b"x")
    backend = FabricOcrBackend(fabric_service([httpx.Response(413, json={"detail": "too big"})], []))
    with pytest.raises(RuntimeError, match=r"IMG_1\.jpg.*413"):
        backend.recognize(image)
    with pytest.raises(ValueError, match="mode"):
        FabricOcrBackend(fabric_service([], []), mode="slow")


class FlakyBackend(FakeBackend):
    def recognize(self, image: Path) -> OcrResult:
        if image.name == "page-2.png":
            raise RuntimeError("service went away")
        return super().recognize(image)


def test_run_ocr_in_parallel_keeps_going_after_a_failed_page(tmp_path: Path) -> None:
    topic, source = make_source(tmp_path, 4)
    out = topic.ocr_dir("fake", source.id)
    with pytest.raises(RuntimeError, match=r"1 of 4 pages failed \(2\)"):
        run_ocr(source, FlakyBackend(), out, log=lambda _: None, workers=2)
    assert [r["page"] for r in load_pages(out)] == [1, 3, 4]
    record = load_pages(out)[0]
    assert record["quality"] is None and record["warnings"] == []
    written = run_ocr(source, FakeBackend(), out, log=lambda _: None, workers=2)
    assert [p.name for p in written] == ["page-0002.json"], "a rerun reads only the failed page"
