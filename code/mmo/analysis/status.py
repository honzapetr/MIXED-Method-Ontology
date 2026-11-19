"""`mmo status`: the map of phases of a study's methods, where it is, what was made, reminders (T33).

Everything here orients; nothing is a condition. Reminders come from the method's practices and from what the
study itself asked for in `analysis:` of `topic.yaml`.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

import yaml

from mmo.analysis.method import current_phases, study_methods, study_settings, vocabulary
from mmo.analysis.quote import FRONT_MATTER
from mmo.analysis.store import ACTIVE_STATUSES, Store
from mmo.core.topic import Topic


def memo_headers(topic: Topic) -> list[dict[str, Any]]:
    headers = []
    for path in sorted((topic.root / "memos").glob("*.md")):
        match = FRONT_MATTER.match(path.read_text(encoding="utf-8"))
        if match:
            headers.append(yaml.safe_load(match.group(1)) or {})
    return headers


def study_status(topic: Topic) -> list[str]:
    store = Store(topic)
    history = store.history()
    settings = study_settings(topic)
    now = current_phases(history)
    memos = memo_headers(topic)
    memo_types = Counter(str(m.get("type")) for m in memos)
    lines: list[str] = [f"{topic.data.get('title', topic.slug)} ({topic.slug})"]

    methods = study_methods(topic)
    if not methods:
        lines.append("methods: none in topic.yaml")
    for method in methods:
        lines.append("")
        lines.append(f"method {method.id} - {method.name} (version {method.version})")
        current = now.get(method.id)
        for phase in method.phases:
            mark = "->" if phase["id"] == current else "  "
            lines.append(f" {mark} {phase['id']}: {phase['goal']}")
        if current is None:
            lines.append(f"    where the study is: not set (mmo phase {topic.slug} <phase> --method {method.id})")
            continue
        phase = method.phase(current) or {}
        lines.append(f"    the model here: {phase.get('model_role', '-')}")
        lines.append(f"    the researcher decides: {phase.get('researcher_decides', '-')}")
        expected = [str(t) for t in phase.get("memos") or []]
        if expected:
            have = ", ".join(f"{t} {memo_types.get(t, 0)}" for t in expected)
            lines.append(f"    memos this phase usually has: {have}")

    active_codes = [c for c in store.codes if c.get("status") in ACTIVE_STATUSES]
    active_codings = [c for c in store.codings if c.get("status") in ACTIVE_STATUSES]
    active_relations = [r for r in store.relations if r.get("status") in ACTIVE_STATUSES]
    waiting = sum(
        1 for item in [*store.codes, *store.codings, *store.relations] if item.get("status") == "proposed"
    ) + sum(1 for m in memos if m.get("status") == "proposed")
    lines.append("")
    lines.append(
        f"made: {len(active_codes)} codes, {len(active_codings)} codings, {len(active_relations)} relations, "
        f"{len(memos)} memos" + (f" ({', '.join(f'{t} {n}' for t, n in sorted(memo_types.items()))})" if memos else "")
    )
    lines.append(f"proposals of models waiting for the researcher: {waiting}")
    changed = settings.changed()
    lines.append(
        "settings: free defaults" if not changed else "settings: " + ", ".join(f"{k}={v}" for k, v in changed.items())
    )

    reminders: list[str] = []
    for event in history:
        if event.get("op") in ("merge-codes", "split-code") and not event.get("reason"):
            what = event.get("into") if event["op"] == "merge-codes" else event.get("code")
            reminders.append(f"{event['op']} of {what} ({event['at'][:10]}) has no reason - a memo would say why")
    if settings["own_types"] == "ask_memo":
        code_types, relation_types = vocabulary(topic)
        for code in active_codes:
            if code.get("code_type") and code["code_type"] not in code_types:
                reminders.append(f"code {code['id']}: own type {code['code_type']!r} - the study asks for a memo why")
        for relation in active_relations:
            if relation["relation_type"] not in relation_types:
                reminders.append(
                    f"relation {relation['id']}: own type {relation['relation_type']!r} - the study asks for a memo"
                )
    for method in methods:
        reminders += [f"{method.id}: {practice}" for practice in method.practices]
    if reminders:
        lines.append("")
        lines.append("reminders (orientation, not conditions):")
        lines += [f"  - {r}" for r in reminders]
    return lines


def own_type_reminder(topic: Topic, kind: str, type_name: str | None) -> str | None:
    """A reminder after `code add` or `relation add` when the study asks for a memo on types of its own."""
    if not type_name or study_settings(topic)["own_types"] != "ask_memo":
        return None
    code_types, relation_types = vocabulary(topic)
    known = code_types if kind == "code" else relation_types
    if type_name in known:
        return None
    return (
        f"reminder: {type_name!r} is not in the vocabulary of the study's methods - welcome, and the study asks for a "
        f"short memo on why it arose (mmo memo add {topic.slug} --type analytic ...)"
    )
