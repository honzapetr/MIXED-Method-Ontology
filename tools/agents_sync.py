#!/usr/bin/env python3
"""Generate Claude Code files from the provider-neutral sources in `.agents/`.

* `.agents/skills/<name>/**`  -> `.claude/skills/<name>/**` (verbatim copy)
* `.agents/roles/<name>.md`   -> `.claude/agents/<name>.md` (subagent; read-only roles get read-only tools)

Antigravity reads `.agents/` and `AGENTS.md` natively, so it needs no copies.
`--check` exits 1 when the generated files differ from the sources (used by CI). Standard library only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_SKILLS = ROOT / ".agents" / "skills"
SOURCE_ROLES = ROOT / ".agents" / "roles"
CLAUDE_SKILLS = ROOT / ".claude" / "skills"
CLAUDE_AGENTS = ROOT / ".claude" / "agents"
READ_ONLY_TOOLS = "Read, Grep, Glob, Bash"
GENERATED = "<!-- Generated from .agents/roles/{name}.md by tools/agents_sync.py - edit the source, not this file. -->"


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    """Split `---` front matter of flat `key: value` lines from the body."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing front matter")
    end = next((i for i, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
    if end is None:
        raise ValueError("unterminated front matter")
    meta: dict[str, str] = {}
    for line in lines[1:end]:
        key, sep, value = line.partition(":")
        if sep:
            meta[key.strip()] = value.strip()
    return meta, "\n".join(lines[end + 1 :]).lstrip("\n")


def render_agent(role_file: Path) -> str:
    meta, body = parse_front_matter(role_file.read_text(encoding="utf-8"))
    name = meta.get("name") or role_file.stem
    header = ["---", f"name: {name}", f"description: {meta.get('description', '')}"]
    if meta.get("access") == "read":
        header.append(f"tools: {READ_ONLY_TOOLS}")
    header.append("---")
    return "\n".join([*header, GENERATED.format(name=role_file.stem), "", body.rstrip(), ""])


def expected_files() -> dict[Path, bytes]:
    files: dict[Path, bytes] = {}
    if SOURCE_SKILLS.is_dir():
        for src in sorted(SOURCE_SKILLS.rglob("*")):
            if src.is_file():
                files[CLAUDE_SKILLS / src.relative_to(SOURCE_SKILLS)] = src.read_bytes()
    if SOURCE_ROLES.is_dir():
        for role in sorted(SOURCE_ROLES.glob("*.md")):
            files[CLAUDE_AGENTS / role.name] = render_agent(role).encode("utf-8")
    return files


def existing_files() -> set[Path]:
    found: set[Path] = set()
    for base in (CLAUDE_SKILLS, CLAUDE_AGENTS):
        if base.is_dir():
            found.update(p for p in base.rglob("*") if p.is_file())
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="only report drift, change nothing")
    args = parser.parse_args(argv)

    expected = expected_files()
    stale = sorted(existing_files() - expected.keys())
    changed = sorted(p for p, data in expected.items() if not p.is_file() or p.read_bytes() != data)

    if args.check:
        for path in changed + stale:
            print(f"out of sync: {path.relative_to(ROOT).as_posix()}", file=sys.stderr)
        if changed or stale:
            print("run: python3 tools/agents_sync.py", file=sys.stderr)
            return 1
        return 0

    for path in changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected[path])
    for path in stale:
        path.unlink()
    print(f"agents_sync: {len(changed)} written, {len(stale)} removed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
