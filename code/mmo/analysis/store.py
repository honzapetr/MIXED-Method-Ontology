"""The analysis store of a study and the free toolbox (T32, ADR 0013, docs/analysis-store.md).

`topics/<slug>/analysis/` is the source of truth of the analysis - text files in git, sorted, readable in a diff:

- `codebook.yaml`  - the codes (ontology `Code`): any label and any type; a method's vocabulary only orients;
- `codings.jsonl`  - a code applied to a quotation (ontology `Annotation`: body = code, target = quotation);
- `relations.yaml` - a typed relation between any two items (ontology `Relation`);
- `history.jsonl`  - every operation, who did it and when, and the state of the files after it.

Memos stay in `topics/<slug>/memos/` (format: the research environment's `docs/memos.md`); `mmo memo add` writes
them in that format. The tools check integrity only - a quotation that is not in `text.md`, a missing author, a
reference to nothing - never the method: a code type the method does not list is as welcome as one it does.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from mmo.analysis.quote import GONE, OK, Quotation, check_record, read_final_text
from mmo.core.topic import Topic

ACTIVE_STATUSES = {"accepted", "edited", "proposed"}  # ontology ProposalStatus; the rest are kept for the history
FILES = ("codebook.yaml", "codings.jsonl", "relations.yaml")
REF = re.compile(r"^(code|coding|relation|memo|source):(.+)$")


class StoreError(ValueError):
    """An operation that would break integrity (not a method rule - those do not exist here)."""


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def slug(text: str) -> str:
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")[:60] or "code"


def file_sha(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


@dataclass
class Author:
    """Who does an operation: a person or a model (a model also names the prompt version it worked from)."""

    id: str
    kind: str  # person | model
    prompt_version: str | None = None

    def stamp(self) -> dict[str, Any]:
        stamp: dict[str, Any] = {"author": self.id, "created": now()}
        if self.kind == "model":
            stamp["generated_by"] = {"model": self.id, "prompt_version": self.prompt_version}
        return stamp

    @property
    def status(self) -> str:
        """A model's record is a proposal until the researcher decides (T29); the researcher's own is accepted."""
        return "proposed" if self.kind == "model" else "accepted"


def analysts_dir(topic: Topic) -> Path:
    return topic.root.parent.parent / "analysts"  # <environment>/topics/<slug> -> <environment>/analysts


def author_of(topic: Topic, by: str | None, prompt_version: str | None = None) -> Author:
    if not by or not by.strip():
        raise StoreError("who does this? give --by <analyst id> (the researcher or the exact model id)")
    by = by.strip()
    profile = analysts_dir(topic) / f"{by}.md"
    is_model = profile.is_file() and "model profile" in profile.read_text(encoding="utf-8").splitlines()[0].lower()
    if is_model and not prompt_version:
        raise StoreError(
            f"{by} is a model: give --prompt-version (the skill or prompt it works from and its version, "
            "e.g. skad-fine-analysis@1, or chat@<date> for a dialogue with the researcher)"
        )
    return Author(by, "model" if is_model else "person", prompt_version if is_model else None)


class Store:
    """The analysis files of one study, loaded; every change goes through an operation that records itself."""

    def __init__(self, topic: Topic) -> None:
        self.topic = topic
        self.dir = topic.root / "analysis"
        self.codes: list[dict[str, Any]] = self._yaml("codebook.yaml", "codes")
        self.codings: list[dict[str, Any]] = self._jsonl("codings.jsonl")
        self.relations: list[dict[str, Any]] = self._yaml("relations.yaml", "relations")

    # ------------------------------------------------------------ files

    def _yaml(self, name: str, key: str) -> list[dict[str, Any]]:
        path = self.dir / name
        return list((yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get(key) or []) if path.is_file() else []

    def _jsonl(self, name: str) -> list[dict[str, Any]]:
        path = self.dir / name
        if not path.is_file():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def state(self) -> dict[str, str | None]:
        return {name: file_sha(self.dir / name) for name in FILES}

    def last_state(self) -> dict[str, str | None] | None:
        for event in reversed(self.history()):
            if "state" in event:
                return event["state"]
        return None

    def history(self) -> list[dict[str, Any]]:
        return self._jsonl("history.jsonl")

    def save(self, author: Author | None, op: str, **details: Any) -> dict[str, Any]:
        """Write the files sorted, then append the operation with the state of the files after it."""
        self.dir.mkdir(parents=True, exist_ok=True)
        codebook = {"codes": sorted(self.codes, key=lambda c: c["id"])}
        (self.dir / "codebook.yaml").write_text(
            yaml.safe_dump(codebook, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n"
        )
        rows = sorted(self.codings, key=lambda c: c["id"])
        (self.dir / "codings.jsonl").write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n"
        )
        relations = {"relations": sorted(self.relations, key=lambda r: r["id"])}
        (self.dir / "relations.yaml").write_text(
            yaml.safe_dump(relations, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n"
        )
        event: dict[str, Any] = {"at": now(), "op": op}
        if author is not None:
            event["author"] = author.id
            if author.kind == "model":
                event["generated_by"] = {"model": author.id, "prompt_version": author.prompt_version}
        event.update(details)
        event["state"] = self.state()
        with (self.dir / "history.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    # ------------------------------------------------------------ lookups

    def code(self, code_id: str) -> dict[str, Any]:
        for code in self.codes:
            if code["id"] == code_id:
                return code
        raise StoreError(f"no code {code_id!r} in the codebook (mmo code list)")

    def coding(self, coding_id: str) -> dict[str, Any]:
        for coding in self.codings:
            if coding["id"] == coding_id:
                return coding
        raise StoreError(f"no coding {coding_id!r}")

    def find_code(self, name_or_id: str) -> dict[str, Any] | None:
        for code in self.codes:
            if name_or_id in (code["id"], code["label"]):
                return code
        return None

    def _next_id(self, prefix: str, items: list[dict[str, Any]]) -> str:
        numbers = [int(i["id"].rsplit("-", 1)[1]) for i in items if re.match(rf"^{prefix}-\d+$", i["id"])]
        return f"{prefix}-{max(numbers, default=0) + 1:04d}"

    def check_ref(self, ref: str) -> str:
        """A reference to an item: code:<id>, coding:<id>, relation:<id>, memo:<id>, source:<id>."""
        match = REF.match(ref)
        if not match:
            raise StoreError(
                f"not a reference: {ref!r} (code:<id>, coding:<id>, relation:<id>, memo:<id>, source:<id>)"
            )
        kind, key = match.groups()
        found = {
            "code": lambda: any(c["id"] == key for c in self.codes),
            "coding": lambda: any(c["id"] == key for c in self.codings),
            "relation": lambda: any(r["id"] == key for r in self.relations),
            "memo": lambda: (self.topic.root / "memos" / f"{key}.md").is_file(),
            "source": lambda: (self.topic.root / "sources" / key / "source.yaml").is_file(),
        }[kind]()
        if not found:
            raise StoreError(f"{ref} does not exist in the study")
        return ref

    # ------------------------------------------------------------ operations

    def add_code(
        self,
        author: Author,
        label: str,
        code_type: str | None = None,
        method: str | None = None,
        definition: str | None = None,
        broader: str | None = None,
    ) -> dict[str, Any]:
        if not label.strip():
            raise StoreError("a code needs a label")
        if self.find_code(label.strip()):
            raise StoreError(f"a code {label!r} exists already")
        if broader:
            self.code(broader)
        base, n = slug(label), 1
        code_id = base
        while any(c["id"] == code_id for c in self.codes):
            n += 1
            code_id = f"{base}-{n}"
        code: dict[str, Any] = {"id": code_id, "label": label.strip()}
        for key, value in (("code_type", code_type), ("method", method), ("definition", definition)):
            if value:
                code[key] = value
        if broader:
            code["broader"] = broader
        code["status"] = author.status
        code.update(author.stamp())
        self.codes.append(code)
        self.save(author, "add-code", code=code_id)
        return code

    def apply_code(
        self, author: Author, code_ref: str, quotation: Quotation, method: str | None = None, note: str | None = None
    ) -> dict[str, Any]:
        """Code a quotation; a code that does not exist yet is created with that label (coding is free)."""
        code = self.find_code(code_ref) or self.add_code(author, code_ref, method=method)
        if code["status"] in ("superseded", "withdrawn", "rejected"):
            raise StoreError(
                f"code {code['id']} is {code['status']}; use {code.get('superseded_by') or 'another code'}"
            )
        coding: dict[str, Any] = {
            "id": self._next_id("cd", self.codings),
            "body": code["id"],
            "target": quotation.record(),
        }
        if method:
            coding["method"] = method
        if note:
            coding["note"] = note
        coding["status"] = author.status
        coding.update(author.stamp())
        self.codings.append(coding)
        self.save(author, "apply-code", coding=coding["id"], code=code["id"])
        return coding

    def rename_code(self, author: Author, code_id: str, label: str) -> dict[str, Any]:
        code = self.code(code_id)
        if self.find_code(label) not in (None, code):
            raise StoreError(f"a code {label!r} exists already")
        old = code["label"]
        code["label"] = label
        self.save(author, "rename-code", code=code_id, old_label=old, new_label=label)
        return code

    def merge_codes(self, author: Author, into: str, sources: list[str], reason: str | None = None) -> dict[str, Any]:
        target = self.code(into)
        moved: list[str] = []
        for source_id in sources:
            if source_id == into:
                raise StoreError("a code cannot be merged into itself")
            code = self.code(source_id)
            code["status"] = "superseded"
            code["superseded_by"] = [into]
            for coding in self.codings:
                if coding["body"] == source_id and coding["status"] in ACTIVE_STATUSES:
                    coding["body"] = into
                    coding.setdefault("was", []).append(source_id)
                    moved.append(coding["id"])
        self.save(author, "merge-codes", into=into, merged=sources, codings=moved, reason=reason)
        return target

    def split_code(
        self, author: Author, code_id: str, labels: list[str], reason: str | None = None
    ) -> list[dict[str, Any]]:
        """New codes from one; its codings stay with it until recoded (the researcher decides each)."""
        old = self.code(code_id)
        new = [
            self.add_code(author, label, old.get("code_type"), old.get("method"), broader=old.get("broader"))
            for label in labels
        ]
        old["status"] = "superseded"
        old["superseded_by"] = [c["id"] for c in new]
        waiting = [c["id"] for c in self.codings if c["body"] == code_id and c["status"] in ACTIVE_STATUSES]
        self.save(author, "split-code", code=code_id, into=old["superseded_by"], to_recode=waiting, reason=reason)
        return new

    def recode(self, author: Author, coding_id: str, code_ref: str) -> dict[str, Any]:
        coding = self.coding(coding_id)
        code = self.find_code(code_ref) or self.add_code(author, code_ref)
        old = coding["body"]
        coding["body"] = code["id"]
        coding.setdefault("was", []).append(old)
        self.save(author, "recode", coding=coding_id, old_code=old, new_code=code["id"])
        return coding

    def withdraw(self, author: Author, ref: str, reason: str | None = None) -> None:
        """Take back a coding, a code or a relation; it stays in the files with its status, for the history."""
        kind, key = REF.match(self.check_ref(ref)).groups()  # type: ignore[union-attr]
        item = {"coding": self.coding, "code": self.code, "relation": self._relation}.get(kind)
        if item is None:
            raise StoreError(f"{kind} cannot be withdrawn here")
        record = item(key)
        record["status"] = "withdrawn"
        if reason:
            record["withdrawn_because"] = reason
        self.save(author, "withdraw", target=ref, reason=reason)

    def _relation(self, relation_id: str) -> dict[str, Any]:
        for relation in self.relations:
            if relation["id"] == relation_id:
                return relation
        raise StoreError(f"no relation {relation_id!r}")

    def relate(
        self,
        author: Author,
        subject: str,
        relation_type: str,
        obj: str,
        method: str | None = None,
        note: str | None = None,
        evidence: list[Quotation] | None = None,
    ) -> dict[str, Any]:
        if not relation_type.strip():
            raise StoreError("a relation needs a type (any word; the method's types only orient)")
        relation: dict[str, Any] = {
            "id": self._next_id("rel", self.relations),
            "relation_type": relation_type.strip(),
            "subject": self.check_ref(subject),
            "object": self.check_ref(obj),
        }
        if method:
            relation["method"] = method
        if note:
            relation["description"] = note
        if evidence:
            relation["evidence"] = [q.record() for q in evidence]
        relation["status"] = author.status
        relation.update(author.stamp())
        self.relations.append(relation)
        self.save(author, "relate", relation=relation["id"])
        return relation


# ---------------------------------------------------------------- memos


def write_memo(
    topic: Topic,
    author: Author,
    memo_type: str,
    title: str,
    body: str = "",
    about: list[str] | None = None,
    quotations: list[Quotation] | None = None,
    method: str | None = None,
    phase: str | None = None,
) -> Path:
    """A memo in `memos/` in the format of `docs/memos.md`; quotations go to `basis`."""
    store = Store(topic)
    refs = [store.check_ref(ref) for ref in about or []]
    created = datetime.now(UTC).date().isoformat()
    base = f"{created}-{slug(title)}"
    memo_id, n = base, 1
    while (topic.root / "memos" / f"{memo_id}.md").exists():
        n += 1
        memo_id = f"{base}-{n}"
    meta: dict[str, Any] = {
        "id": memo_id,
        "type": memo_type,
        "author": author.id,
        "created": created,
        "status": "proposed" if author.kind == "model" else "draft",
        "about": refs,
    }
    if quotations:
        meta["basis"] = {"quotations": [q.record() for q in quotations]}
    if method:
        meta["method"] = method
    if phase:
        meta["phase"] = phase
    if author.kind == "model":
        meta["generated_by"] = {"model": author.id, "prompt_version": author.prompt_version}
    path = topic.root / "memos" / f"{memo_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    front = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False)
    path.write_text(f"---\n{front}---\n\n# {title}\n\n{body.strip()}\n", encoding="utf-8", newline="\n")
    store.save(author, "memo", memo=memo_id, about=refs)
    return path


# ---------------------------------------------------------------- integrity check


@dataclass
class Finding:
    where: str
    problem: str


def check_store(topic: Topic, record_hand_edits: bool = False, by: str | None = None) -> list[Finding]:
    """Integrity of the analysis files: authors, references, quotations, and edits made by hand.

    The researcher may edit the files by hand (the analysis is free); such an edit is noticed by the state of the
    files recorded after every operation, and `record_hand_edits` writes it into the history with its author.
    """
    store = Store(topic)
    findings: list[Finding] = []
    last = store.last_state()
    current = store.state()
    if last is not None and last != current:
        changed = [name for name in FILES if last.get(name) != current.get(name)]
        if record_hand_edits:
            event = {"at": now(), "op": "hand-edit", "author": by, "files": changed, "state": current}
            with (store.dir / "history.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")
        else:
            findings.append(Finding(", ".join(changed), "edited by hand since the last mmo operation (--record)"))
    texts: dict[str, str | None] = {}
    for kind, items in (("code", store.codes), ("coding", store.codings), ("relation", store.relations)):
        for item in items:
            where = f"{kind} {item.get('id', '?')}"
            if not item.get("author") or not item.get("created"):
                findings.append(Finding(where, "no author or time"))
    code_ids = {c["id"] for c in store.codes}
    for code in store.codes:
        for ref in [code.get("broader"), *(code.get("superseded_by") or [])]:
            if ref and ref not in code_ids:
                findings.append(Finding(f"code {code['id']}", f"points to a code that does not exist: {ref}"))
    for coding in store.codings:
        if coding.get("body") not in code_ids:
            findings.append(Finding(f"coding {coding['id']}", f"code {coding.get('body')} does not exist"))
        target = coding.get("target") or {}
        source_id = str(target.get("source"))
        if source_id not in texts:
            try:
                texts[source_id] = read_final_text(topic.source(source_id))
            except (FileNotFoundError, ValueError):
                texts[source_id] = None
        text = texts[source_id]
        if text is None:
            findings.append(Finding(f"coding {coding['id']}", f"no text.md for the source {source_id}"))
            continue
        status = check_record(target, text).status
        if status != OK:
            hint = "mmo quote check --update" if status != GONE else "the words are gone: recode or withdraw"
            findings.append(Finding(f"coding {coding['id']}", f"quotation {status} ({hint})"))
    for relation in store.relations:
        for key in ("subject", "object"):
            try:
                store.check_ref(str(relation.get(key)))
            except StoreError as err:
                findings.append(Finding(f"relation {relation['id']}", str(err)))
    return findings
