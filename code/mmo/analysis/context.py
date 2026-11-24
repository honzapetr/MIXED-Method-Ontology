"""Context search by the method and the research questions: plans, rounds, requests, web (T44, ADR 0015).

* A **search plan** is a memo of type `search-plan`: per research question the context it needs, the types and
  character of sources and why they matter, where to look (not only the web), how independence is judged, when to
  stop. A model proposes it; the researcher approves it (`mmo review`), or writes it.
* A **round** of the search follows an approved plan (`op: search-round` in the history); a gap found later - in a
  phase or by the critic - starts a new round of the same plan, with the gap as its reason.
* A **request to the researcher** names what a model cannot reach (a paid media archive, a printed source, a
  recording, an interview) and why (`op: request`); the researcher closes it with what came of it
  (`op: request-closed`).
* **Web search** by a model is allowed for a study only when the researcher lists the model in
  `analysis.web_search` of `topic.yaml`.

`mmo` keeps the search traceable; what a study counts as relevant context is the method's and the researcher's.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import yaml

from mmo.analysis.method import study_methods, study_settings
from mmo.analysis.quote import FRONT_MATTER
from mmo.analysis.store import Author, Store, StoreError
from mmo.core.topic import ROLE_CONTEXT, Topic

PLAN_TYPE = "search-plan"
APPROVED = {"accepted", "edited"}


@dataclass
class Plan:
    id: str
    title: str
    author: str
    status: str
    approved: bool


def plans(topic: Topic, store: Store | None = None) -> list[Plan]:
    """The study's search-plan memos; a model's plan is approved once the researcher accepts or edits it."""
    store = store or Store(topic)
    found = []
    for path in sorted((topic.root / "memos").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = FRONT_MATTER.match(text)
        meta = (yaml.safe_load(match.group(1)) or {}) if match else {}
        if meta.get("type") != PLAN_TYPE:
            continue
        title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")), path.stem)
        status = str(meta.get("status", ""))
        by_model = bool(meta.get("generated_by"))
        approved = status in APPROVED or (not by_model and status not in {"rejected", "withdrawn"})
        found.append(Plan(path.stem, title, str(meta.get("author", "?")), status, approved))
    return found


def plan_of(topic: Topic, ref: str) -> Plan:
    key = ref.removeprefix("memo:")
    for plan in plans(topic):
        if plan.id == key:
            return plan
    raise StoreError(f"{ref} is not a search-plan memo of the study (mmo memo add ... --type {PLAN_TYPE})")


def rounds(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in history if e.get("op") == "search-round"]


def requests(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Requests to the researcher, each with `closed` (the closing event) when it has one."""
    closed = {e["request"]: e for e in history if e.get("op") == "request-closed"}
    return [{**e, "closed": closed.get(e["request"])} for e in history if e.get("op") == "request"]


def open_requests(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in requests(history) if not r["closed"]]


def _next(prefix: str, ids: list[str]) -> str:
    numbers = [int(i.rsplit("-", 1)[1]) for i in ids if i.startswith(prefix + "-")]
    return f"{prefix}-{max(numbers, default=0) + 1:04d}"


def start_round(store: Store, author: Author, plan_ref: str, reason: str, gaps: list[str] | None = None) -> dict:
    """A round of the search by an approved plan; a later round names the gap that started it."""
    plan = plan_of(store.topic, plan_ref)
    if not plan.approved:
        raise StoreError(
            f"the search plan {plan.id} is {plan.status}: the researcher approves it first (mmo review accept)"
        )
    if not reason.strip():
        raise StoreError("why this round? give --reason (the plan's first round, or the gap a phase or critic found)")
    refs = [store.check_ref(g) for g in gaps or []]
    earlier = [r for r in rounds(store.history()) if r.get("plan") == plan.id]
    if earlier and not refs:
        raise StoreError("a new round of the same plan names the gap that started it: --gap memo:<id>")
    return store.save(
        author,
        "search-round",
        plan=plan.id,
        round=len(earlier) + 1,
        reason=reason.strip(),
        **({"gaps": refs} if refs else {}),
    )


def add_request(
    store: Store,
    author: Author,
    what: str,
    why: str,
    where: str | None = None,
    question: str | None = None,
    plan: str | None = None,
) -> dict:
    """What a model cannot reach, written for the researcher."""
    if not what.strip() or not why.strip():
        raise StoreError("a request says what is needed (--what) and why (--why)")
    questions = {str(q.get("id")) for q in store.topic.data.get("questions") or [] if isinstance(q, dict)}
    if question and questions and question not in questions:
        raise StoreError(f"--question {question} is not in topic.yaml ({', '.join(sorted(questions))})")
    details: dict[str, Any] = {"request": _next("request", [r["request"] for r in requests(store.history())])}
    details.update({"what": what.strip(), "why": why.strip()})
    for key, value in (("where", where), ("question", question)):
        if value:
            details[key] = value
    if plan:
        details["plan"] = plan_of(store.topic, plan).id
    return store.save(author, "request", **details)


def close_request(store: Store, author: Author, request_id: str, outcome: str, sources: list[str] | None = None):
    """The researcher says what came of a request (a source brought in, not obtainable, ...)."""
    store.researcher_only(author, "closes a request to the researcher")
    found = {r["request"]: r for r in requests(store.history())}
    if request_id not in found:
        raise StoreError(f"no {request_id} (mmo context list)")
    if found[request_id]["closed"]:
        raise StoreError(f"{request_id} is closed already")
    if not outcome.strip():
        raise StoreError("what came of it? give --outcome")
    refs = [store.check_ref(f"source:{s.removeprefix('source:')}") for s in sources or []]
    return store.save(
        author, "request-closed", request=request_id, outcome=outcome.strip(), **({"sources": refs} if refs else {})
    )


def web_allowed(topic: Topic, model_id: str) -> bool:
    """Whether the researcher let this model search the web for this study (`analysis.web_search`)."""
    return model_id in [str(m) for m in study_settings(topic)["web_search"]]


def context_sources(topic: Topic) -> list[tuple[str, dict[str, Any]]]:
    """Context sources with their provenance (empty when missing)."""
    out = []
    for source in topic.sources():
        meta = source.metadata()
        if meta.get("role") == ROLE_CONTEXT:
            out.append((source.id, meta.get("provenance") or {}))
    return out


def summary(topic: Topic, store: Store | None = None) -> list[str]:
    """Lines for `mmo status` and `mmo context list`."""
    store = store or Store(topic)
    history = store.history()
    lines: list[str] = []
    found = plans(topic, store)
    done = rounds(history)
    lines.append(
        f"context search: search plans {len(found)} ({sum(p.approved for p in found)} approved), rounds {len(done)}"
        if found
        else "context search: no search plan yet (a memo of type search-plan, approved by the researcher)"
    )
    described = [m.id for m in study_methods(topic) if m.context_search]
    if described:
        lines.append(f"    what relevant context is: context_search of {', '.join(described)} (method.yaml)")
    sources = context_sources(topic)
    if sources:
        by_relation: dict[str, int] = {}
        for _, prov in sources:
            key = str(prov.get("relation") or "provenance missing")
            by_relation[key] = by_relation.get(key, 0) + 1
        lines.append(
            f"    context sources: {len(sources)} ("
            + ", ".join(f"{k} {n}" for k, n in sorted(by_relation.items()))
            + ")"
        )
    web = [str(m) for m in study_settings(topic)["web_search"]]
    lines.append(f"    web search approved for: {', '.join(web) if web else 'no model (analysis.web_search)'}")
    waiting = open_requests(history)
    if waiting:
        lines.append(f"    requests to the researcher: {len(waiting)} open")
        lines += [f"      {r['request']}: {r['what']} - {r['why']}" for r in waiting]
    return lines
