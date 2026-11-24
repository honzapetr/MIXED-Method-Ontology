"""Blind probe: what a model knows of a source from training, on record before it meets the source (T45, ADR 0015).

The lead starts a run of the role `blind-probe` for one source and one model (its own, or the critic's); the run's
input is only the source's title and author from `source.yaml`. The probe answers in a `reflexive` memo marked as
prior knowledge:

```yaml
prior_knowledge:
  source: kniha
  model: claude-opus-5-5
  before_search: true        # no round of the context search had been recorded when it was written
  met_source_before: false   # the model had no record quoting the source or about it before
```

Later context memos compare it (`--about memo:<probe>`): which of it a source confirmed, which not. `mmo` records
when the probe was written and what the model had met before; what the model recalls is the probe's.
"""

from __future__ import annotations

from typing import Any

import yaml

from mmo.analysis.context import rounds
from mmo.analysis.quote import FRONT_MATTER
from mmo.analysis.store import Author, Store, StoreError, is_model
from mmo.core.topic import ROLE_PRIMARY, Topic

ROLE = "blind-probe"


def title_and_authors(topic: Topic, source_id: str) -> tuple[str, list[str]]:
    """What the probe is given: the title and the authors of `source.yaml`, nothing else."""
    meta = topic.source(source_id).metadata()
    if not meta:
        raise StoreError(f"no source {source_id} in the study")
    citation = meta.get("citation") or {}
    title = str(citation.get("title") or meta.get("title") or "").strip()
    authors = [str(a) for a in citation.get("authors") or []]
    if not title or not authors:
        raise StoreError(
            f"the probe is given the title and the author of {source_id}: fill citation.title (or title) and "
            "citation.authors in its source.yaml"
        )
    return title, authors


def start_probe(store: Store, author: Author, source_id: str, analyst: str) -> dict[str, Any]:
    title, authors = title_and_authors(store.topic, source_id)
    return store.start_run(
        author,
        analyst,
        ROLE,
        [f"source:{source_id}", f"title: {title}", f"author: {', '.join(authors)}"],
        note="blind: only the title and the author; no text, no web, no study data",
    )


def task(event: dict[str, Any], slug: str) -> str:
    """The whole task the lead hands to the probe - and nothing more."""
    source = event["input"][0]
    return (
        f"Blind probe, study {slug}, run {event['run']} (role blind-probe). "
        f"{event['input'][1]}; {event['input'][2]}. "
        "What do you know of this source, its author and its reception from training? Recall, do not infer; keep "
        "what you infer apart; say how sure you are. No web, no files of the study. "
        f"Write it with: mmo memo add {slug} --by {event['analyst']} --run {event['run']} --type reflexive "
        f'--prior-knowledge {source} --title "Prior knowledge of {source.removeprefix("source:")}" --file <answer>'
    )


def _meta(path) -> dict[str, Any]:
    match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
    return (yaml.safe_load(match.group(1)) or {}) if match else {}


def met_source(topic: Topic, store: Store, analyst: str, source_id: str) -> bool:
    """Whether the model has a record that quotes the source or is about it (it has met the source)."""
    if any(c.get("author") == analyst and (c.get("target") or {}).get("source") == source_id for c in store.codings):
        return True
    for path in sorted((topic.root / "memos").glob("*.md")):
        meta = _meta(path)
        if meta.get("author") != analyst or meta.get("prior_knowledge"):
            continue
        quoted = {str(q.get("source")) for q in (meta.get("basis") or {}).get("quotations") or []}
        if source_id in quoted or f"source:{source_id}" in (meta.get("about") or []):
            return True
    return False


def prior_record(topic: Topic, store: Store, author: Author, ref: str) -> dict[str, Any]:
    """The `prior_knowledge` field of a probe memo, computed before the memo is written."""
    source_id = ref.removeprefix("source:")
    store.check_ref(f"source:{source_id}")
    return {
        "source": source_id,
        "model": author.id,
        "before_search": not rounds(store.history()),
        "met_source_before": met_source(topic, store, author.id, source_id),
    }


def probes(topic: Topic) -> list[dict[str, Any]]:
    """Prior-knowledge memos, each with the memos that compare it (`about: memo:<id>`)."""
    metas = {path.stem: _meta(path) for path in sorted((topic.root / "memos").glob("*.md"))}
    found = []
    for memo_id, meta in metas.items():
        prior = meta.get("prior_knowledge")
        if not prior:
            continue
        compared = [other for other, m in metas.items() if f"memo:{memo_id}" in (m.get("about") or [])]
        found.append({"memo": memo_id, "status": meta.get("status"), **prior, "compared_in": compared})
    return found


def positioned_models(topic: Topic) -> list[str]:
    """The models with a position in the study."""
    folder = topic.root / "positions"
    if not folder.is_dir():
        return []
    return [p.stem for p in sorted(folder.glob("*.md")) if is_model(topic, p.stem)]


def summary(topic: Topic) -> tuple[list[str], list[str]]:
    """Lines for `mmo status`, and reminders: a studied source a positioned model has not been probed on."""
    found = probes(topic)
    lines = []
    if found:
        lines.append("prior knowledge (blind probes):")
        for probe in found:
            flags = []
            if not probe.get("before_search"):
                flags.append("written after the context search began")
            if probe.get("met_source_before"):
                flags.append("the model had met the source before")
            compared = f"compared in {len(probe['compared_in'])} memos" if probe["compared_in"] else "not compared yet"
            extra = f" - {'; '.join(flags)}" if flags else ""
            lines.append(f"    {probe['source']} by {probe['model']}: {probe['memo']} ({compared}){extra}")
    probed = {(p["source"], p["model"]) for p in found}
    primary = [s.id for s in topic.sources() if s.metadata().get("role", ROLE_PRIMARY) == ROLE_PRIMARY]
    reminders = [
        f"no blind probe of {model} on {source} (mmo probe start {topic.slug} --source {source} --analyst {model})"
        for model in positioned_models(topic)
        for source in primary
        if (source, model) not in probed
    ]
    return lines, reminders
