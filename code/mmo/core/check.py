"""What a source still lacks for qualitative work (`mmo source check`): metadata, links, ingest, review."""

from __future__ import annotations

from mmo.core.provenance import provenance_problems
from mmo.core.topic import NOTES_TEMPLATE, ROLE_CONTEXT, ROLES, SOURCE_KINDS, Source, read_yaml
from mmo.ingest.ocr import load_pages
from mmo.ingest.segment import read_segments, stale_segments


def check_source(source: Source) -> list[str]:
    """Plain-language findings, empty when nothing is missing."""
    found: list[str] = []
    if not source.metadata_file.is_file():
        return [f"no source.yaml - create the source with: mmo source add {source.topic.slug} {source.id} --kind ..."]
    meta = source.metadata()
    topic_questions = {str(q.get("id")) for q in source.topic.data.get("questions") or [] if isinstance(q, dict)}

    if not meta.get("title") or meta.get("title") == source.id:
        found.append("title: a human-readable title is missing")
    if meta.get("kind") not in SOURCE_KINDS:
        found.append(f"kind: one of {', '.join(SOURCE_KINDS)}")
    role = meta.get("role", "primary")
    if role not in ROLES:
        found.append(f"role: {role!r} is not one of {', '.join(ROLES)}")
    citation = meta.get("citation") or {}
    if not (citation.get("authors") and citation.get("year") and (citation.get("title") or meta.get("title"))):
        found.append("citation: authors and year are needed to quote the source")
    if not meta.get("attributes"):
        found.append("attributes: none yet (e.g. author's background, date, place - the document variables)")
    questions = [str(q) for q in meta.get("questions") or []]
    if not questions:
        found.append("questions: which research questions of the topic does the source serve?")
    unknown_questions = [q for q in questions if topic_questions and q not in topic_questions]
    if unknown_questions:
        found.append(f"questions: not in topic.yaml: {', '.join(unknown_questions)}")
    if role == ROLE_CONTEXT:
        about = [str(a) for a in meta.get("about") or []]
        known = {s.id for s in source.topic.sources()}
        if not about:
            found.append("about: a context source must name the source(s) it is about")
        elif [a for a in about if a not in known]:
            found.append(f"about: unknown sources: {', '.join(a for a in about if a not in known)}")
        found += provenance_problems(meta)  # T44, ADR 0015: whose voice a context source is, and how it was found
    notes = source.notes_file.read_text(encoding="utf-8") if source.notes_file.is_file() else ""
    title = meta.get("title") or source.id
    if not notes.strip() or notes == NOTES_TEMPLATE.format(title=title):
        found.append("notes.md: the context memo is still empty")

    if not source.images() and not source.texts():
        found.append(f"files: no originals in {source.files_dir}")
    elif not source.ocr_variants():
        found.append(f"ingest: not run yet - mmo ingest {source.topic.slug} {source.id}")
    if source.ocr_variants():
        chosen = (meta.get("text") or {}).get("variant")
        if not chosen:
            found.append(
                f"final text: choose the variant for the analysis (text: {{variant: <variant>}} in source.yaml), "
                f"then mmo source finalize {source.topic.slug} {source.id}"
            )
        elif chosen not in source.ocr_variants():
            found.append(f"final text: variant {chosen!r} of source.yaml has no OCR results")
        elif not source.final_text_file.is_file():
            found.append(f"final text: not built yet - mmo source finalize {source.topic.slug} {source.id}")
        elif not source.segments_file.is_file():
            found.append(f"segments: not cut yet - mmo segment {source.topic.slug} {source.id}")
        elif stale := stale_segments(
            source.final_text_file.read_text(encoding="utf-8"), read_segments(source.segments_file)
        ):
            found.append(
                f"segments: {len(stale)} no longer match text.md (it changed) - mmo segment {source.topic.slug} "
                f"{source.id}"
            )
    for variant in source.ocr_variants():
        order = read_yaml(source.order_file(variant))
        summary = order.get("summary") or {}
        unknown, duplicates = summary.get("unknown") or 0, summary.get("duplicates") or {}
        if unknown or duplicates:
            found.append(
                f"reading order ({variant}): {unknown} pages without a number, {len(duplicates)} numbers twice - "
                f"see {source.order_file(variant)}"
            )
        stuck = [
            r["scan"]
            for r in load_pages(source.ocr_dir(variant))
            if (r.get("cleaning") or {}).get("stuck") and not r["cleaning"].get("replaced_from")
        ]
        if stuck:
            found.append(
                f"stuck OCR ({variant}): scans {', '.join(map(str, stuck))} looped and have no replacement - "
                f"read them again and run mmo ocr clean with --fallback"
            )
    return found
