"""Where a context source came from and whose voice it is: `provenance` of `source.yaml` (T44, ADR 0015).

```yaml
provenance:
  found:
    how: search            # search | reference (cited in another source) | researcher (the researcher brought it)
    query: "..."           # the query, for a search
    place: Webarchiv NK    # where it was found: a catalogue, the web archive, a register, a database, the web, ...
    date: 2026-11-24       # when it was found
    by: claude-opus-5-5    # who found it (a model id or the researcher)
    plan: 2026-11-24-search-plan   # the search-plan memo, and its round
    round: 1
  type: review             # review, interview, register entry, archive record, readers' discussion, ...
  character: critical      # promotional, critical, neutral, ... - in the words of the study
  speaker: "..."           # who speaks in it
  relation: independent    # author | author-circle | independent: the speaker's relation to the object of the study
  judged: "..."            # how the relation was judged
```

`mmo` checks that the provenance is there and traceable, never what the study counts as context.
"""

from __future__ import annotations

from datetime import date
from typing import Any

FOUND_HOW = ("search", "reference", "researcher")
RELATIONS = ("author", "author-circle", "independent")
REQUIRED = ("type", "character", "speaker", "relation")


def provenance_problems(meta: dict[str, Any]) -> list[str]:
    """What the provenance of a context source lacks, in plain language; empty when it is complete."""
    prov = meta.get("provenance")
    hint = "mmo source provenance <topic> <source> ..."
    if not prov:
        return [f"provenance: how it was found, its type and character, speaker and relation are missing ({hint})"]
    if not isinstance(prov, dict):
        return [f"provenance: a mapping ({hint})"]
    problems: list[str] = []
    found = prov.get("found") or {}
    how = found.get("how")
    if how not in FOUND_HOW:
        problems.append(f"provenance.found.how: one of {', '.join(FOUND_HOW)}")
    if how == "search" and not found.get("query"):
        problems.append("provenance.found.query: the query of the search")
    if how != "researcher" and not found.get("place"):
        problems.append("provenance.found.place: where it was found")
    if not found.get("date"):
        problems.append("provenance.found.date: when it was found")
    for key in REQUIRED:
        if not prov.get(key):
            problems.append(f"provenance.{key}: missing")
    if prov.get("relation") and prov["relation"] not in RELATIONS:
        problems.append(f"provenance.relation: one of {', '.join(RELATIONS)}")
    return problems


def provenance_record(
    how: str,
    type_: str,
    character: str,
    speaker: str,
    relation: str,
    query: str | None = None,
    place: str | None = None,
    found_on: str | None = None,
    by: str | None = None,
    plan: str | None = None,
    round_: int | None = None,
    judged: str | None = None,
) -> dict[str, Any]:
    """A provenance block; refuses what could not be traced."""
    if how not in FOUND_HOW:
        raise ValueError(f"--how: one of {', '.join(FOUND_HOW)}")
    if relation not in RELATIONS:
        raise ValueError(f"--relation: one of {', '.join(RELATIONS)}")
    if how == "search" and not query:
        raise ValueError("a source found by a search needs --query")
    if how != "researcher" and not place:
        raise ValueError("where was it found? give --place")
    found: dict[str, Any] = {"how": how}
    for key, value in (("query", query), ("place", place)):
        if value:
            found[key] = value
    found["date"] = found_on or date.today().isoformat()
    for key, value in (("by", by), ("plan", plan), ("round", round_)):
        if value:
            found[key] = value
    record: dict[str, Any] = {
        "found": found,
        "type": type_,
        "character": character,
        "speaker": speaker,
        "relation": relation,
    }
    if judged:
        record["judged"] = judged
    return record
