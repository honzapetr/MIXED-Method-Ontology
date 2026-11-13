import json
from pathlib import Path

from PIL import Image

from mmo.cli import main
from mmo.core.check import check_source
from mmo.core.topic import Topic, sha256_file
from mmo.ingest.clean import clean_record, clean_text, import_record, merge_variants
from mmo.ingest.ocr import load_pages

LOOP = "Občané Unie by šli jen stěží do války pod evropskou vlajkou."


def test_a_clean_page_is_left_as_it_is() -> None:
    text = "NAZÍ V AI DOBĚ\n\nPrvní odstavec.\n\nDruhý odstavec.\n\n39\n"
    result = clean_text(text)
    assert result.text == text and result.removed == [] and result.stuck == []


def test_separators_go_but_do_not_mark_the_page_stuck() -> None:
    result = clean_text("NAZÍ V AI DOBĚ\n---\nText.\n\n39")
    assert result.text == "NAZÍ V AI DOBĚ\nText.\n\n39\n"
    assert [(r.line, r.rule) for r in result.removed] == [(2, "separator")]
    assert result.stuck == []


def test_a_counting_loop_goes_but_a_page_number_stays() -> None:
    result = clean_text("Text strany.\n\n1\n2\n\n3\n4\n\nDalší text.\n\n39")
    assert result.text == "Text strany.\n\nDalší text.\n\n39\n"
    assert [r.text for r in result.removed] == ["1", "2", "3", "4"]
    assert {r.rule for r in result.removed} == {"number-run"}
    assert result.stuck == ["4 number-only lines in a row"]


def test_repeated_long_lines_go_short_ones_stay() -> None:
    text = "\n".join(["Úvod.", LOOP, "a", LOOP, "a", LOOP, LOOP, "Konec."])
    result = clean_text(text)
    assert result.text == "\n".join(["Úvod.", LOOP, "a", "a", "Konec."]) + "\n"
    assert [r.line for r in result.removed] == [4, 6, 7]
    assert result.stuck == ["3 repeated lines"]


def test_one_repeated_line_is_not_yet_a_loop() -> None:
    assert clean_text(f"{LOOP}\n{LOOP}").stuck == []


def test_a_phrase_repeated_within_a_line_is_shortened_and_logged() -> None:
    line = f"{LOOP} {LOOP} {LOOP} a dál"
    result = clean_text(f"Úvod.\n{line}")
    assert result.text == f"Úvod.\n{LOOP} a dál\n"
    assert [(r.line, r.rule, r.text) for r in result.removed] == [(2, "repeated-phrase", line)]
    assert result.stuck == ["1 lines with a repeated phrase"]


def record(scan: int, text: str, sha: str = "abc") -> dict:
    image = f"IMG_{scan}.png"
    return {"source": "kniha", "scan": scan, "image": image, "image_sha256": sha, "model": "m", "text": text}


def test_a_stuck_page_takes_the_fallback_text_and_keeps_the_log() -> None:
    raw = record(1, "\n".join([LOOP] * 4))
    fallback = {**record(1, "Celá strana přečtená znovu.\n\n115"), "model": "other", "backend": "import"}
    out = clean_record(raw, "fabric", fallback, "claude")
    assert out["text"] == "Celá strana přečtená znovu.\n\n115\n" and out["model"] == "other"
    assert out["cleaning"]["replaced_from"] == "claude" and len(out["cleaning"]["removed"]) == 3
    assert raw["text"] == "\n".join([LOOP] * 4), "the raw record is not changed"
    assert "replaced_from" not in clean_record(record(2, "Dobrá strana."), "fabric", None, "claude")["cleaning"]
    short = clean_record(record(3, "Strana, kterou model ukončil"), "fabric", fallback, "claude")
    assert short["cleaning"]["replaced_from"] == "claude", "a new reading wins even without a loop"


def test_a_fallback_from_another_image_is_refused() -> None:
    try:
        clean_record(record(1, "\n".join([LOOP] * 4)), "fabric", record(1, "x", sha="other"), "claude")
    except ValueError as err:
        assert "different image" in str(err)
    else:
        raise AssertionError("expected ValueError")


def test_cli_import_clean_and_check(tmp_path: Path, capsys) -> None:
    topics = ["--topics", str(tmp_path)]
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.add_source("kniha", "book", title="Kniha", language="ces")
    raw_dir = source.ocr_dir("fabric")
    raw_dir.mkdir(parents=True)
    texts = {1: "Dobrá strana.\n---\n\n11", 2: "\n".join([LOOP] * 5), 3: "Text.\n1\n2\n3\n4"}
    for scan, text in texts.items():
        image = source.files_dir / f"IMG_{scan}.png"
        Image.new("RGB", (300 + scan, 400), "white").save(image)
        rec = record(scan, text, sha256_file(image)) | {"image": image.name}
        (raw_dir / f"scan-{scan:04d}.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")

    assert main([*topics, "ocr", "clean", "t1", "kniha", "--variant", "fabric"]) == 0
    assert "2 stuck scans without a replacement" in capsys.readouterr().out
    assert any(f.startswith("stuck OCR (fabric-clean): scans 2, 3") for f in check_source(source))

    reread = tmp_path / "reread"
    reread.mkdir()
    (reread / "scan-0002.txt").write_text("Strana přečtená znovu.\n\n12", encoding="utf-8")
    args = ["--variant", "claude", "--model", "claude-opus-5-5", "--prompt-version", "reread-v1"]
    assert main([*topics, "ocr", "import", "t1", "kniha", str(reread), *args]) == 0
    imported = load_pages(source.ocr_dir("claude"))
    assert [(r["scan"], r["model"], r["backend"]) for r in imported] == [(2, "claude-opus-5-5", "import")]
    assert imported[0]["image_sha256"] == sha256_file(source.files_dir / "IMG_2.png")

    assert main([*topics, "ocr", "clean", "t1", "kniha", "--variant", "fabric", "--fallback", "claude"]) == 0
    cleaned = {r["scan"]: r for r in load_pages(source.ocr_dir("fabric-clean"))}
    assert cleaned[1]["text"] == "Dobrá strana.\n\n11\n"
    assert cleaned[2]["text"] == "Strana přečtená znovu.\n\n12\n"
    assert [r["text"] for r in load_pages(raw_dir)] == list(texts.values()), "raw variant untouched"
    assert any(f.startswith("stuck OCR (fabric-clean): scans 3 ") for f in check_source(source))


def test_import_takes_the_rotation_line_out_of_the_text(tmp_path: Path) -> None:
    rec = import_record("kniha", 4, tmp_path / "IMG_4.jpg", "abc", "ROTATION: 90cw\nStrana.\n\n54", "m", "p")
    assert rec["rotation"] == "90cw" and rec["text"] == "Strana.\n\n54\n"
    plain = import_record("kniha", 5, tmp_path / "IMG_5.jpg", "abc", "ROTATION nic\nStrana.", "m", "p")
    assert plain["rotation"] is None and plain["text"] == "ROTATION nic\nStrana.\n"


def test_merge_takes_each_scan_from_the_first_variant_that_has_it() -> None:
    first = [{"scan": 2, "model": "opus", "text": "B"}]
    second = [{"scan": 1, "model": "sonnet", "text": "a"}, {"scan": 2, "model": "sonnet", "text": "b"}]
    merged = merge_variants({"claude": first, "sonnet": second})
    taken = [(r["scan"], r["model"], r["merged_from"]) for r in merged]
    assert taken == [(1, "sonnet", "sonnet"), (2, "opus", "claude")]


def test_cli_merge(tmp_path: Path, capsys) -> None:
    topic = Topic.create(tmp_path, "t1", "T")
    source = topic.add_source("kniha", "book", title="Kniha", language="ces")
    for scan in (1, 2, 3):
        Image.new("RGB", (300 + scan, 400), "white").save(source.files_dir / f"IMG_{scan}.png")
    for variant, scans in {"claude": [2], "sonnet": [1, 2]}.items():
        folder = source.ocr_dir(variant)
        folder.mkdir(parents=True)
        for scan in scans:
            rec = {"scan": scan, "image": f"IMG_{scan}.png", "model": variant, "text": f"{variant} {scan}\n"}
            (folder / f"scan-{scan:04d}.json").write_text(json.dumps(rec), encoding="utf-8")
    args = ["--topics", str(tmp_path), "ocr", "merge", "t1", "kniha", "--variants", "claude", "sonnet"]
    assert main([*args, "--into", "book"]) == 0
    out = capsys.readouterr().out
    assert "1 from claude, 1 from sonnet" in out and "scans in no variant: 3" in out
    assert [r["text"] for r in load_pages(source.ocr_dir("book"))] == ["sonnet 1\n", "claude 2\n"]
