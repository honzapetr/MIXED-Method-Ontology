"""Context search by the method and the research questions: plan, rounds, requests, provenance, web (T44, ADR 0015)."""

from pathlib import Path

import pytest
import yaml

from mmo.analysis.context import plans, start_round, summary, web_allowed
from mmo.analysis.method import SettingsError, check_context_search, check_method, study_settings
from mmo.analysis.review import decide
from mmo.analysis.status import study_status
from mmo.analysis.store import Store, StoreError, author_of, write_memo
from mmo.cli import main
from mmo.core.check import check_source
from mmo.core.provenance import provenance_problems, provenance_record
from mmo.core.topic import Topic

MODEL_PROFILE = "# m – model profile\n\n> Status: confirmed\n"  # noqa: RUF001 - profiles use the en dash
SEARCHER = """---
name: context-searcher
description: Carries out one item of an approved context-search plan.
version: "2026-11-24"
writes: memo
---
"""
POSITION = "---\nanalyst: m\nstatus: confirmed\nprofile_version: '1'\nroles:\n  - context-searcher\n---\n\n# P\n"
CONTEXT_SEARCH = {
    "derived_from": "the research questions and the arenas of the discourse field",
    "source_types": ["review - an independent reading", "interview - the author's own voice"],
    "character": "the author's own voice, the author's circle, an independent voice",
    "where": ["library catalogues", "Webarchiv NK", "the web, when the study allows it"],
    "repeat": "after content structure, and when a gap is found",
}


@pytest.fixture
def topic(tmp_path: Path) -> Topic:
    env = tmp_path / "env"
    (env / "analysts").mkdir(parents=True)
    (env / "analysts" / "m.md").write_text(MODEL_PROFILE, encoding="utf-8")
    (env / ".agents" / "roles").mkdir(parents=True)
    (env / ".agents" / "roles" / "context-searcher.md").write_text(SEARCHER, encoding="utf-8")
    topic = Topic.create(env / "topics", "st", "S")
    topic.data["questions"] = [{"id": "q3", "text": "reception outside the author's circle"}]
    topic.save()
    (topic.root / "positions").mkdir()
    (topic.root / "positions" / "m.md").write_text(POSITION, encoding="utf-8")
    topic.add_source("kniha", "book", "Kniha")
    topic.add_source("rozhovor", "interview", "Rozhovor", role="context", about=["kniha"])
    return topic


def lead(topic: Topic):
    return author_of(topic, "m", "skad/corpus@1")


def owner(topic: Topic):
    return author_of(topic, "owner")


def plan_memo(topic: Topic, author) -> str:
    body = "## q3\nContext needed: reception outside the author's circle.\nTypes and character: reviews ..."
    return write_memo(topic, author, "search-plan", "Search plan", body).stem


def test_method_yaml_describes_context_search(tmp_path: Path) -> None:
    assert check_context_search(CONTEXT_SEARCH) == []
    assert check_context_search(None) == [], "a method without it is still a method"
    broken = {**CONTEXT_SEARCH, "source_types": "reviews", "extra": 1}
    del broken["repeat"]
    problems = check_context_search(broken)
    assert "context_search: missing repeat" in problems
    assert "context_search: source_types must be a list" in problems
    assert "context_search: extra is not a field" in problems
    folder = tmp_path / "toy"
    folder.mkdir()
    (folder / "method.yaml").write_text(yaml.safe_dump({"id": "toy", "context_search": "web"}), encoding="utf-8")
    assert any(p.startswith("context_search: a mapping") for p in check_method(folder))


def test_web_search_is_approved_per_study_and_per_model(topic: Topic) -> None:
    assert study_settings(topic)["web_search"] == [] and not web_allowed(topic, "m")
    event = Store(topic).start_run(lead(topic), "m", "context-searcher", ["q3: reviews"])
    assert event["web"] is False
    topic.data["analysis"] = {"web_search": ["m"]}
    topic.save()
    topic = Topic.load(topic.root)
    assert web_allowed(topic, "m") and not web_allowed(topic, "n")
    store = Store(topic)
    assert store.start_run(lead(topic), "m", "context-searcher", ["q3: reviews"])["web"] is True
    assert store.start_run(lead(topic), "m", "context-searcher", ["q3"], web=False)["web"] is False
    assert any("web open in runs: run-0002" in line for line in summary(topic))
    with pytest.raises(StoreError, match="a subagent does not close runs"):
        store.close_run(author_of(topic, "m", run="run-0002"), "run-0002")
    assert store.close_run(lead(topic), "run-0002", "came back")["op"] == "run-closed"
    with pytest.raises(StoreError, match="closed already"):
        store.close_run(lead(topic), "run-0002")
    assert not any("web open in runs" in line for line in summary(topic))
    topic.data["analysis"] = {"web_search": "m"}
    with pytest.raises(SettingsError, match="web_search"):
        study_settings(topic)


def test_a_context_source_carries_its_provenance(topic: Topic) -> None:
    source = topic.source("rozhovor")
    assert any(f.startswith("provenance:") for f in check_source(source))
    assert not any("provenance" in f for f in check_source(topic.source("kniha"))), "the studied source needs none"
    with pytest.raises(ValueError, match="--query"):
        provenance_record("search", "review", "critical", "a critic", "independent", place="the web")
    with pytest.raises(ValueError, match="--relation"):
        provenance_record("researcher", "review", "critical", "a critic", "friend")
    with pytest.raises(ValueError, match="--place"):
        provenance_record("reference", "review", "critical", "a critic", "independent")
    code = main(
        [
            "source", "provenance", str(topic.root), "rozhovor", "--how", "search", "--query", "Kniha rozhovor",
            "--place", "Webarchiv NK", "--date", "2026-11-24", "--found-by", "m", "--type", "interview",
            "--character", "promotional", "--speaker", "the author", "--relation", "author",
        ]
    )  # fmt: skip
    assert code == 0
    meta = source.metadata()
    assert meta["provenance"]["found"] == {
        "how": "search",
        "query": "Kniha rozhovor",
        "place": "Webarchiv NK",
        "date": "2026-11-24",
        "by": "m",
    }
    assert provenance_problems(meta) == []
    assert not any("provenance" in f for f in check_source(source))
    meta["provenance"]["relation"] = "fan"
    assert "provenance.relation: one of author, author-circle, independent" in provenance_problems(meta)


def test_a_search_round_follows_an_approved_plan(topic: Topic) -> None:
    store = Store(topic)
    proposed = plan_memo(topic, lead(topic))
    assert [(p.id, p.approved) for p in plans(topic)] == [(proposed, False)]
    with pytest.raises(StoreError, match="the researcher approves it first"):
        start_round(store, lead(topic), f"memo:{proposed}", "first round")
    with pytest.raises(StoreError, match="not a search-plan memo"):
        start_round(store, lead(topic), "memo:nothing", "first round")
    decide(topic, owner(topic), f"memo:{proposed}", "accept")
    first = start_round(Store(topic), lead(topic), f"memo:{proposed}", "first round: q3")
    assert (first["plan"], first["round"], first["author"]) == (proposed, 1, "m")
    with pytest.raises(StoreError, match="names the gap"):
        start_round(Store(topic), lead(topic), proposed, "again")
    gap = write_memo(topic, lead(topic), "analytic", "Gap: no reader voices", "...").stem
    second = start_round(Store(topic), lead(topic), proposed, "the critic found no readers", [f"memo:{gap}"])
    assert (second["round"], second["gaps"]) == (2, [f"memo:{gap}"])
    own = plan_memo(topic, owner(topic))
    assert next(p for p in plans(topic) if p.id == own).approved, "the researcher's own plan needs no review"


def test_requests_to_the_researcher_are_listed_until_closed(topic: Topic, capsys) -> None:
    root = str(topic.root)
    assert main(["context", "request", root, "--by", "m", "--prompt-version", "p@1", "--what", "x", "--why", "y",
                 "--question", "q9"]) == 1  # fmt: skip
    assert "q9 is not in topic.yaml" in capsys.readouterr().err
    request = ["--what", "reviews in Newton Media", "--why", "reception outside the circle", "--where", "Newton"]
    assert main(["context", "request", root, "--by", "m", "--prompt-version", "p@1", "--question", "q3", *request]) == 0
    status = "\n".join(study_status(Topic.load(topic.root)))
    assert "requests to the researcher: 1 open" in status
    assert "request-0001: reviews in Newton Media - reception outside the circle" in status
    assert "web search approved for: no model" in status and "context sources: 1 (provenance missing 1)" in status
    assert main(["context", "close", root, "request-0001", "--by", "m", "--prompt-version", "p@1",
                 "--outcome", "x"]) == 1  # fmt: skip
    assert "the researcher closes" in capsys.readouterr().err
    assert main(["context", "close", root, "request-0001", "--by", "owner", "--outcome", "no access to Newton"]) == 0
    assert "requests to the researcher" not in "\n".join(study_status(Topic.load(topic.root)))
    capsys.readouterr()
    assert main(["context", "list", root]) == 0
    listed = capsys.readouterr().out
    assert "request-0001 (m): reviews in Newton Media" in listed and "[closed: no access to Newton]" in listed
    assert "source rozhovor: ?, ?, ? (provenance missing)" in listed
