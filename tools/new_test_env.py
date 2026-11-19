"""Create a test copy of the research environment in `zkusebna/` (ADR 0011).

Copies what git would see in the research environment (tracked files and untracked files that are not ignored), so
`.venv/`, `.env`, caches, `scratch/` and `.git/` stay behind. The copy includes the project files (dotfiles,
`pyproject.toml`, `uv.lock`, `tools/`): the path dependency on the workshop is rewritten and `uv sync` is run in the
copy, so `mmo` and the hooks of `.claude/settings.json` (`mmo-guard`) work there. `--without-project-files` leaves
them out (then the hooks cannot run); `--no-sync` skips `uv sync`. Page images and other
git-ignored source files are copied only with `--with-source-files`. The copy has no git unless `--git` is given.

`--carry <copy>` carries the work of an earlier test copy into the new one, so a study can grow over several test
copies: the files of the study state (`topics/`, `analysts/`, but not the environment's own files there and not
what the machine rebuilds: `text.md`, `segments.jsonl`, `ingest/`, `files/`, `ground-truth/`, `work/`) that the
earlier copy created, changed or deleted since it was made - compared with the commit of the research environment
recorded for it in `_log.tsv` - are applied to the new copy. Everything else comes new from the research
environment. A file changed both in the earlier copy and in the research environment is a conflict: nothing is
created until `--on-conflict copy` or `--on-conflict env` says which side wins. Changes of the earlier copy outside
the study state (instructions, methods, skills) are listed, never carried: they are feedback for the workshop.
Carrying again from a copy that was itself carried carries everything it holds.

Usage (from the workshop):
    python tools/new_test_env.py                       # zkusebna/test<N>, next free number
    python tools/new_test_env.py profile-start --without-profile claude-opus-5-5
    python tools/new_test_env.py --carry test7 --git   # the study work of test7 on the current environment
    python tools/new_test_env.py --dry-run

Standard library only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
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
STUDY_AREAS = ("topics", "analysts")
# the environment's own files inside the study areas: never carried
ENVIRONMENT_IN_STUDY = re.compile(
    r"^(topics/README\.md|topics/\.gitignore|analysts/README\.md|analysts/_template-[^/]*)$"
)
MACHINE_IN_SOURCE = {"text.md", "segments.jsonl", "ingest", "files", "ground-truth"}  # rebuilt, never carried
NOT_IN_COPY = {".git", ".venv", "__pycache__", "scratch", ".pytest_cache", ".ruff_cache"}


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


def files_to_copy(source: Path, with_source_files: bool, with_project_files: bool = True) -> list[str]:
    """Paths relative to `source`, as git sees them: tracked plus untracked-not-ignored (plus ignored sources)."""
    files = set(git(source, "ls-files", "-z", "--cached", "--others", "--exclude-standard").split("\0"))
    # Input documents kept out of git (`topics/.gitignore`) are still copied; only the root rules (scans) apply.
    if (source / ".gitignore").is_file():
        files |= set(git(source, "ls-files", "-z", "--others", "--exclude-from=.gitignore", "--", "topics").split("\0"))
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


# ---------------------------------------------------------------- carrying the work of an earlier copy


def is_study_state(rel: str) -> bool:
    """A file of the study state: under `topics/` or `analysts/`, not the environment's, not rebuilt by the machine."""
    parts = PurePosixPath(rel).parts
    if not parts or parts[0] not in STUDY_AREAS or ENVIRONMENT_IN_STUDY.match(rel):
        return False
    if parts[0] == "topics" and len(parts) >= 3 and parts[2] == "work":
        return False
    return not (len(parts) >= 5 and parts[0] == "topics" and parts[2] == "sources" and parts[4] in MACHINE_IN_SOURCE)


def blob_id(data: bytes) -> str:
    """Git's blob id of a file's content, to compare a file with a commit without reading the commit file by file.

    Line ends of a text file are taken as `\\n`, as git stores them, so a CRLF checkout is not a change.
    """
    if b"\0" not in data:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def files_in(copy: Path) -> dict[str, str]:
    """Every file of a test copy (without git, environments, caches, scratch) -> its blob id."""
    found = {}
    for folder, dirs, names in os.walk(copy):
        dirs[:] = [d for d in dirs if d not in NOT_IN_COPY]
        for name in names:
            path = Path(folder) / name
            rel = path.relative_to(copy).as_posix()
            if rel != LOG and not is_secret(rel):
                found[rel] = blob_id(path.read_bytes())
    return found


def files_at(source: Path, commit: str) -> dict[str, str]:
    """Every file of the research environment at `commit` -> its blob id."""
    found = {}
    for line in git(source, "ls-tree", "-r", "-z", commit).split("\0"):
        if line:
            meta, rel = line.split("\t", 1)
            found[rel] = meta.split()[2]
    return found


def log_row(zkusebna: Path, name: str) -> list[str] | None:
    """The row of `_log.tsv` for a test copy: time, name, branch, commit, clean/dirty, options."""
    log = zkusebna / LOG
    rows = [line.split("\t") for line in log.read_text(encoding="utf-8").splitlines()] if log.is_file() else []
    found = [row for row in rows if len(row) > 3 and row[1] == name]
    return found[-1] if found else None


class Carry:
    """What an earlier copy changed since it was made, sorted into what is carried and what is only reported."""

    def __init__(self, source: Path, earlier: Path, base: str) -> None:
        then, copy = files_at(source, base), files_in(earlier)
        current = {rel: blob_id((source / rel).read_bytes()) for rel in files_to_copy(source, False)}
        self.write: list[str] = []  # created or changed in the earlier copy: copied into the new one
        self.delete: list[str] = []  # deleted in the earlier copy: deleted in the new one
        self.conflicts: list[str] = []  # changed both in the earlier copy and in the research environment
        self.feedback: list[str] = []  # environment files the earlier copy changed: reported, not carried
        for rel in sorted(set(copy) | set(then)):
            mine, old, now = copy.get(rel), then.get(rel), current.get(rel)
            if mine in (old, now):
                continue  # untouched in the copy, or the environment has the same already
            if not is_study_state(rel):
                if mine is not None and old is not None and not is_project_file(rel):
                    self.feedback.append(rel)
                continue
            if now != old and not (old is None and now is None):
                self.conflicts.append(rel)
            elif mine is None:
                self.delete.append(rel)
            else:
                self.write.append(rel)

    def apply(self, earlier: Path, dest: Path, winner: str | None) -> list[str]:
        """Change the new copy; on a conflict the copy or the environment wins as `winner` says."""
        changed = []
        for rel in self.write + (self.conflicts if winner == "copy" else []):
            target = dest / rel
            if (earlier / rel).is_file():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(earlier / rel, target)
            elif target.exists():
                target.unlink()
            changed.append(rel)
        for rel in self.delete:
            if (dest / rel).exists():
                (dest / rel).unlink()
                changed.append(rel)
        return changed


def version_mismatches(dest: Path) -> list[str]:
    """Positions written from another profile version than the analyst's profile in `dest` (the guard would close
    the study's text to that model)."""
    found = []
    for position in sorted(dest.glob("topics/*/positions/*.md")):
        text = position.read_text(encoding="utf-8")
        wrote = re.search(r"(?m)^profile_version:\s*['\"]?([\w.-]+)", text)
        profile = dest / "analysts" / position.name
        if not wrote or not profile.is_file():
            continue
        current = re.search(r"(?m)^>?\s*Version:\s*([\w.-]+)", profile.read_text(encoding="utf-8"))
        if current and current.group(1) != wrote.group(1):
            rel = position.relative_to(dest).as_posix()
            found.append(f"{rel}: profile_version {wrote.group(1)}, profile now {current.group(1)}")
    return found


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
        "--without-project-files",
        action="store_true",
        help="leave out dotfiles, pyproject.toml, uv.lock and tools/ (then mmo and the hooks cannot run)",
    )
    parser.add_argument("--no-sync", action="store_true", help="do not run uv sync in the copy")
    parser.add_argument("--git", action="store_true", help="git init and commit the copy")
    parser.add_argument("--dry-run", action="store_true", help="only list what would be copied")
    parser.add_argument("--carry", metavar="COPY", help="carry the study work of an earlier test copy in zkusebna/")
    parser.add_argument(
        "--on-conflict", choices=("copy", "env"), help="with --carry: which side wins a file changed on both sides"
    )
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

    files = files_to_copy(source, args.with_source_files, not args.without_project_files)
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

    carry = None
    if args.carry:
        earlier = zkusebna / args.carry
        row = log_row(zkusebna, args.carry)
        if not earlier.is_dir() or row is None:
            parser.error(f"no test copy {args.carry} recorded in {zkusebna / LOG}")
        base = row[3]
        if row[4] != "clean":
            print(f"warning: {args.carry} was made with uncommitted changes; they count as its own work")
        carry = Carry(source, earlier, base)
        print(
            f"carry from {args.carry} (made from {base}): "
            f"{len(carry.write)} changed or new, {len(carry.delete)} deleted"
        )
        for rel in carry.write:
            print(f"  carry   {rel}")
        for rel in carry.delete:
            print(f"  delete  {rel}")
        for rel in carry.feedback:
            print(f"  not carried (environment, changed in {args.carry}): {rel}")
        for rel in carry.conflicts:
            print(f"  CONFLICT (changed in {args.carry} and in the research environment): {rel}")
        if carry.conflicts and not args.on_conflict:
            print(
                "nothing created: choose --on-conflict copy (keep the test's version) or env (keep the environment's)"
            )
            return 1
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

    if carry is not None:
        changed = carry.apply(zkusebna / args.carry, dest, args.on_conflict)
        print(f"carried from {args.carry}: {len(changed)} files")
        if args.git and changed:
            subprocess.run(["git", "-C", str(dest), "add", "-A"], check=True)
            message = f"chore: study work carried from {args.carry}"
            subprocess.run(["git", "-C", str(dest), "commit", "-q", "-m", message], check=True)
        for problem in version_mismatches(dest):
            print(f"warning: {problem} - the guard keeps the study text closed to this model until it is stated again")

    options = " ".join(
        [f"--without-profile {m}" for m in args.without_profile]
        + (["--with-source-files"] if args.with_source_files else [])
        + (["--without-project-files"] if args.without_project_files else [])
        + (["--git"] if args.git else [])
        + ([f"--carry {args.carry}"] if args.carry else [])
        + ([f"--on-conflict {args.on_conflict}"] if args.on_conflict else [])
    )
    state = "dirty" if dirty else "clean"
    row = [dt.datetime.now().isoformat(timespec="seconds"), name, branch, commit, state, options]
    with (zkusebna / LOG).open("a", encoding="utf-8", newline="\n") as log:
        log.write("\t".join(row) + "\n")
    print(f"done; recorded in {zkusebna / LOG}")
    if not args.without_project_files and not args.no_sync:
        synced = subprocess.run(["uv", "sync", "-q"], cwd=dest).returncode == 0
        print("uv sync in the copy: " + ("done" if synced else "FAILED - the hooks will report 'Guards: NOT running'"))
    print(f'next: cd "{dest}", then start Claude Code there')
    return 0


if __name__ == "__main__":
    sys.exit(main())
