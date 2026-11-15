"""Create a test copy of the research environment in `zkusebna/` (ADR 0011).

Copies what git would see in the research environment (tracked files and untracked files that are not ignored), so
`.venv/`, `.env`, caches, `scratch/` and `.git/` stay behind. By default the copy holds only what the agent reads
(instructions, skills, methods, analysts, studies): the project files for git, uv and the editor (dotfiles other
than `.agents/` and `.claude/`, `pyproject.toml`, `uv.lock`, `tools/`) are added with `--with-project-files`, and
then the path dependency on the workshop is rewritten so `uv sync` works in the copy. Page images and other
git-ignored source files are copied only with `--with-source-files`. The copy has no git unless `--git` is given.

Usage (from the workshop):
    python tools/new_test_env.py                       # zkusebna/test<N>, next free number
    python tools/new_test_env.py profile-start --without-profile claude-opus-5-5
    python tools/new_test_env.py --dry-run

Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath

WORKSHOP = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = WORKSHOP.parent / "MIXED-Method-Ontology"
DEFAULT_ZKUSEBNA = WORKSHOP.parent / "zkusebna"
MARKERS = ("AGENTS.md", "CLAUDE.md", ".git")
SOURCE_FILES = re.compile(r"^topics/[^/]+/sources/")
AGENT_DOTDIRS = {".agents", ".claude"}
PROJECT_FILES = {"pyproject.toml", "uv.lock", "tools"}
LOG = "_log.tsv"


def git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *args], capture_output=True, text=True, encoding="utf-8", check=True
    )
    return result.stdout


def is_secret(rel: str) -> bool:
    """Never copy `.env` files, whatever git says about them (`.env.example` is fine)."""
    name = PurePosixPath(rel).name
    return name.startswith(".env") and name != ".env.example"


def is_project_file(rel: str) -> bool:
    """Files for git, uv and the editor, not read by the agent: top-level dotfiles (but `.agents/`, `.claude/`),
    `pyproject.toml`, `uv.lock`, `tools/`."""
    top = PurePosixPath(rel).parts[0]
    return (top.startswith(".") and top not in AGENT_DOTDIRS) or top in PROJECT_FILES


def files_to_copy(source: Path, with_source_files: bool, with_project_files: bool = False) -> list[str]:
    """Paths relative to `source`, as git sees them: tracked plus untracked-not-ignored (plus ignored sources)."""
    files = set(git(source, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0"))
    if with_source_files:
        ignored = git(source, "ls-files", "-z", "--others", "--ignored", "--exclude-standard").split("\0")
        files |= {f for f in ignored if SOURCE_FILES.match(f)}
    return sorted(
        f
        for f in files
        if f and not is_secret(f) and (with_project_files or not is_project_file(f)) and (source / f).is_file()
    )


def marker_above(dest: Path) -> Path | None:
    """First AGENTS.md, CLAUDE.md or .git in a folder above `dest`: it would leak other instructions into the test."""
    for parent in dest.parents:
        for marker in MARKERS:
            if (parent / marker).exists():
                return parent / marker
    return None


def next_name(zkusebna: Path) -> str:
    taken = {int(m.group(1)) for p in zkusebna.glob("test*") if (m := re.fullmatch(r"test(\d+)", p.name))}
    return f"test{max(taken, default=0) + 1}"


def rel_posix(target: Path, start: Path) -> str:
    return Path(os.path.relpath(target, start)).as_posix()


def rewrite_workshop_path(dest: Path, source: Path, workshop: Path) -> list[str]:
    """Point the editable path dependency on the workshop from the copy's location."""
    old, new = rel_posix(workshop, source), rel_posix(workshop, dest)
    changed = []
    for name in ("pyproject.toml", "uv.lock"):
        path = dest / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        updated = text.replace(f'"{old}"', f'"{new}"')
        if updated != text:
            path.write_text(updated, encoding="utf-8", newline="\n")
            changed.append(name)
    return changed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("name", nargs="?", help="folder name in zkusebna/ (default: test<N>, next free number)")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="research environment to copy")
    parser.add_argument("--zkusebna", type=Path, default=DEFAULT_ZKUSEBNA, help="folder of the test copies")
    parser.add_argument("--workshop", type=Path, default=WORKSHOP, help="workshop the copy's `mmo` comes from")
    parser.add_argument(
        "--without-profile",
        action="append",
        default=[],
        metavar="MODEL_ID",
        help="leave out analysts/<MODEL_ID>.md, e.g. to simulate a model's first start (repeatable)",
    )
    parser.add_argument("--with-source-files", action="store_true", help="also copy git-ignored page images etc.")
    parser.add_argument(
        "--with-project-files",
        action="store_true",
        help="also copy dotfiles, pyproject.toml, uv.lock and tools/ (needed for uv sync and mmo)",
    )
    parser.add_argument("--git", action="store_true", help="git init and commit the copy")
    parser.add_argument("--dry-run", action="store_true", help="only list what would be copied")
    args = parser.parse_args(argv)

    source, zkusebna, workshop = args.source.resolve(), args.zkusebna.resolve(), args.workshop.resolve()
    if not (source / ".git").exists():
        parser.error(f"not a git repository: {source}")
    name = args.name or next_name(zkusebna)
    dest = zkusebna / name
    if dest.exists():
        parser.error(f"already exists: {dest}")
    if marker := marker_above(dest):
        parser.error(f"{marker} lies above the test folder; its instructions would apply there too")

    files = files_to_copy(source, args.with_source_files, args.with_project_files)
    for model_id in args.without_profile:
        profile = f"analysts/{model_id}.md"
        if profile not in files:
            parser.error(f"no such profile in the source: {profile}")
        files.remove(profile)

    branch = git(source, "branch", "--show-current").strip() or "(detached)"
    commit = git(source, "rev-parse", "--short", "HEAD").strip()
    dirty = bool(git(source, "status", "--porcelain").strip())
    print(f"{source} @ {branch} {commit}{' (uncommitted changes included)' if dirty else ''}")
    print(f"-> {dest}: {len(files)} files")
    if args.dry_run:
        print("\n".join(files))
        return 0

    for rel in files:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / rel, target)
    changed = rewrite_workshop_path(dest, source, workshop)
    if changed:
        print(f"workshop path rewritten to {rel_posix(workshop, dest)} in {', '.join(changed)}")

    if args.git:
        subprocess.run(["git", "init", "-q", "-b", "main", str(dest)], check=True)
        subprocess.run(["git", "-C", str(dest), "add", "-A"], check=True)
        message = f"chore: test copy of the research environment ({branch} {commit})"
        subprocess.run(["git", "-C", str(dest), "commit", "-q", "-m", message], check=True)

    options = " ".join(
        [f"--without-profile {m}" for m in args.without_profile]
        + (["--with-source-files"] if args.with_source_files else [])
        + (["--with-project-files"] if args.with_project_files else [])
        + (["--git"] if args.git else [])
    )
    state = "dirty" if dirty else "clean"
    row = [dt.datetime.now().isoformat(timespec="seconds"), name, branch, commit, state, options]
    with (zkusebna / LOG).open("a", encoding="utf-8", newline="\n") as log:
        log.write("\t".join(row) + "\n")
    print(f"done; recorded in {zkusebna / LOG}")
    sync = " && uv sync" if args.with_project_files else ""
    print(f'next: cd "{dest}"{sync}, then start Claude Code there')
    return 0


if __name__ == "__main__":
    sys.exit(main())
