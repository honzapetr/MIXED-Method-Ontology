"""Proposals of models and the researcher's review (T29, ADR 0013).

A proposal is not a separate kind of file: it is a record of the toolbox - a code, a coding, a relation or a memo -
written by a model and therefore with `status: proposed`. The researcher decides it in place:

- `accepted` - as proposed;
- `edited` - accepted with changes; the old and new values are kept, so it stays visible what came from the model
  and what from the researcher;
- `rejected` - with a reason (required).

The decision is written into the record (`decided: {verdict, by, at, reason | note, changes}`) and into the
history; the model's provenance (`author`, `generated_by`) is never removed. Only a person decides. The
researcher's own records are never proposals and need no decision.

Many at once (T47): `select()` picks the waiting proposals by kind, author, role, run and the phase the study was in
when each was written (from the history); `decide_many()` decides each as its own decision with the same reason or
note and one `batch` id in each history event.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mmo.analysis.quote import AnalyticFile
from mmo.analysis.store import REF, Author, Store, StoreError, now
from mmo.core.topic import Topic

VERDICTS = {"accept": "accepted", "edit": "edited", "reject": "rejected"}
EDITABLE = {
    "code": {"label", "code_type", "definition", "broader"},
    "coding": {"code"},
    "relation": {"relation_type", "description"},
    "memo": set(),  # the researcher edits the memo's text by hand, then marks it edited with a note
}


@dataclass
class Proposal:
    ref: str
    kind: str
    record: dict[str, Any]
    path: Path | None = None  # the memo's file

    @property
    def summary(self) -> str:
        r = self.record
        if self.kind == "code":
            extra = f" [{r['code_type']}]" if r.get("code_type") else ""
            return f"code {r['label']!r}{extra}" + (f" - {r['definition']}" if r.get("definition") else "")
        if self.kind == "coding":
            q = r.get("target") or {}
            pages = "/".join(str(p) for p in q.get("pages") or []) or "?"
            return f"{r['body']} <- {q.get('source')} p. {pages}: {str(q.get('exact', ''))[:90]!r}"
        if self.kind == "relation":
            return f"{r['subject']} -{r['relation_type']}-> {r['object']}"
        title = next(
            (
                ln[2:]
                for ln in (self.path.read_text(encoding="utf-8").splitlines() if self.path else [])
                if ln.startswith("# ")
            ),
            "",
        )
        return f"{r.get('type')} memo {title!r} about {', '.join(r.get('about') or []) or '-'}"

    @property
    def provenance(self) -> str:
        made = self.record.get("generated_by") or {}
        return f"{self.record.get('author')}, {made.get('prompt_version', '?')}, {str(self.record.get('created'))[:16]}"


def memo_files(topic: Topic) -> list[AnalyticFile]:
    files = []
    for path in sorted((topic.root / "memos").glob("*.md")):
        item = AnalyticFile.load(path)
        if item is not None and isinstance(item.data, dict):
            files.append(item)
    return files


def proposals(topic: Topic, kind: str | None = None) -> list[Proposal]:
    """Everything that waits for the researcher, in the order it was written."""
    store = Store(topic)
    found = [Proposal(f"code:{c['id']}", "code", c) for c in store.codes if c.get("status") == "proposed"]
    found += [Proposal(f"coding:{c['id']}", "coding", c) for c in store.codings if c.get("status") == "proposed"]
    found += [Proposal(f"relation:{r['id']}", "relation", r) for r in store.relations if r.get("status") == "proposed"]
    found += [
        Proposal(f"memo:{m.data.get('id', m.path.stem)}", "memo", m.data, m.path)
        for m in memo_files(topic)
        if m.data.get("status") == "proposed"
    ]
    found.sort(key=lambda p: str(p.record.get("created", "")))
    return [p for p in found if kind is None or p.kind == kind]


def decide(
    topic: Topic,
    author: Author,
    ref: str,
    verdict: str,
    reason: str | None = None,
    note: str | None = None,
    changes: dict[str, str] | None = None,
    batch: str | None = None,
) -> dict[str, Any]:
    """Accept, edit or reject one proposal; returns the history event."""
    if author.kind == "model":
        raise StoreError("only the researcher decides a proposal; a model may comment on it in a memo")
    if verdict not in VERDICTS:
        raise StoreError(f"verdict must be one of {sorted(VERDICTS)}")
    if verdict == "reject" and not (reason and reason.strip()):
        raise StoreError("a rejection needs a reason (--reason)")
    match = REF.match(ref)
    if not match or match.group(1) not in EDITABLE:
        raise StoreError(f"not a proposal reference: {ref!r} (code:, coding:, relation:, memo:)")
    kind, key = match.groups()
    changes = {k: v for k, v in (changes or {}).items() if v is not None}
    if verdict == "edit" and not changes and not note:
        raise StoreError("an edit says what changed: give the new values, or --note for a memo edited by hand")
    if verdict != "edit" and changes:
        raise StoreError("changes go with `edit`")
    unknown = set(changes) - EDITABLE[kind]
    if unknown:
        raise StoreError(f"a {kind} edit changes only {sorted(EDITABLE[kind]) or 'the text, by hand'}")

    if kind == "memo":
        return _decide_memo(topic, author, key, verdict, reason, note, batch)

    store = Store(topic)
    record = {"code": store.code, "coding": store.coding, "relation": store._relation}[kind](key)
    if record.get("status") != "proposed":
        raise StoreError(f"{ref} is {record.get('status')}, not a proposal waiting for a decision")
    cascade: list[str] = []
    applied: dict[str, list[Any]] = {}
    if verdict == "edit":
        for field, value in changes.items():
            if kind == "coding" and field == "code":
                code = store.find_code(value) or store.add_code(author, value)
                applied["body"] = [record["body"], code["id"]]
                record["body"] = code["id"]
            else:
                if field == "broader":
                    store.code(value)
                if field == "label" and store.find_code(value) not in (None, record):
                    raise StoreError(f"a code {value!r} exists already")
                applied[field] = [record.get(field), value]
                record[field] = value
    if kind == "coding" and verdict in ("accept", "edit"):
        code = store.code(record["body"])
        if code.get("status") == "proposed":  # a coding taken over takes its code with it
            _stamp(code, author, "accept", note=f"with {ref}")
            cascade.append(f"code:{code['id']}")
    if kind == "code" and verdict == "reject":
        used = [c for c in store.codings if c["body"] == key and c.get("status") in ("accepted", "edited")]
        if used:
            raise StoreError(
                f"{ref} is used by codings the researcher holds ({', '.join(c['id'] for c in used)}): recode them, "
                "or accept or edit the code"
            )
        for coding in store.codings:
            if coding["body"] == key and coding.get("status") == "proposed":
                _stamp(coding, author, "reject", reason=f"its code was rejected: {reason}")
                cascade.append(f"coding:{coding['id']}")
    _stamp(record, author, verdict, reason=reason, note=note, changes=applied)
    return store.save(
        author,
        "review",
        target=ref,
        verdict=VERDICTS[verdict],
        reason=reason,
        changes=applied,
        cascade=cascade,
        **({"note": note} if note else {}),
        **({"batch": batch} if batch else {}),
    )


def _stamp(
    record: dict[str, Any],
    author: Author,
    verdict: str,
    reason: str | None = None,
    note: str | None = None,
    changes: dict[str, Any] | None = None,
) -> None:
    record["status"] = VERDICTS[verdict]
    decided: dict[str, Any] = {"verdict": VERDICTS[verdict], "by": author.id, "at": now()}
    if reason:
        decided["reason"] = reason
    if note:
        decided["note"] = note
    if changes:
        decided["changes"] = changes
    record["decided"] = decided


def _decide_memo(
    topic: Topic, author: Author, key: str, verdict: str, reason: str | None, note: str | None, batch: str | None
) -> dict[str, Any]:
    item = next((m for m in memo_files(topic) if m.data.get("id", m.path.stem) == key), None)
    if item is None:
        raise StoreError(f"no memo {key!r} in memos/")
    if item.data.get("status") != "proposed":
        raise StoreError(f"memo:{key} is {item.data.get('status')}, not a proposal waiting for a decision")
    _stamp(item.data, author, verdict, reason=reason, note=note)
    item.write()
    return Store(topic).save(
        author,
        "review",
        target=f"memo:{key}",
        verdict=VERDICTS[verdict],
        reason=reason,
        note=note,
        **({"batch": batch} if batch else {}),
    )


# ---------------------------------------------------------------- many at once (T47)

# the history operation that writes a record -> (its kind, the field with its id)
CREATED_BY = {
    "memo": ("memo", "memo"),
    "add-code": ("code", "code"),
    "apply-code": ("coding", "coding"),
    "relate": ("relation", "relation"),
}


def phases_when_written(history: list[dict[str, Any]]) -> dict[str, set[str]]:
    """Ref -> the phases (of every method) the study was in when the record was written."""
    current: dict[str, str] = {}
    found: dict[str, set[str]] = {}
    for event in history:
        op = event.get("op")
        if op == "phase":
            current[str(event.get("method"))] = str(event.get("phase"))
        elif op in CREATED_BY:
            kind, field = CREATED_BY[op]
            if event.get(field):
                found.setdefault(f"{kind}:{event[field]}", set(current.values()))
    return found


def select(
    topic: Topic,
    refs: list[str] | None = None,
    kind: str | None = None,
    author: str | None = None,
    role: str | None = None,
    run: str | None = None,
    phase: str | None = None,
) -> list[Proposal]:
    """The waiting proposals that match every filter given; `refs` limits them to those references."""
    waiting = proposals(topic, kind)
    if refs:
        known = {p.ref: p for p in waiting}
        missing = [r for r in refs if r not in known]
        if missing:
            raise StoreError(f"not waiting for a decision: {', '.join(missing)} (mmo review list)")
        waiting = [known[r] for r in refs]
    phases = phases_when_written(Store(topic).history()) if phase else {}
    out = []
    for item in waiting:
        made = item.record.get("generated_by") or {}
        if author and item.record.get("author") != author:
            continue
        if role and made.get("role") != role:
            continue
        if run and made.get("run") != run:
            continue
        if phase and phase not in phases.get(item.ref, set()) and item.record.get("phase") != phase:
            continue
        out.append(item)
    return out


def decide_many(
    topic: Topic,
    author: Author,
    refs: list[str],
    verdict: str,
    reason: str | None = None,
    note: str | None = None,
) -> list[dict[str, Any]]:
    """Each proposal as its own decision, with the same reason or note and one batch id.

    A proposal already decided by an earlier one of the batch (a code taken with its coding) is skipped; an error
    in one does not stop the rest.
    """
    if author.kind == "model":
        raise StoreError("only the researcher decides a proposal; a model may comment on it in a memo")
    if verdict not in ("accept", "reject"):
        raise StoreError("many at once: accept or reject (an edit is one proposal at a time)")
    if verdict == "reject" and not (reason and reason.strip()):
        raise StoreError("a rejection needs a reason (--reason)")
    batch = f"batch-{now()}" if len(refs) > 1 else None
    results: list[dict[str, Any]] = []
    for ref in refs:
        if ref not in {p.ref for p in proposals(topic)}:
            results.append({"ref": ref, "skipped": "decided already in this batch (with another proposal)"})
            continue
        try:
            event = decide(topic, author, ref, verdict, reason=reason, note=note, batch=batch)
            results.append({"ref": ref, "event": event})
        except StoreError as err:
            results.append({"ref": ref, "error": str(err)})
    return results
