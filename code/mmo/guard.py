"""`mmo-guard` - Claude Code hooks that keep an analyst inside the research environment and its steps (T22).

Two hooks, both reading the hook's JSON from stdin:

* `mmo-guard session-start` - step 1 only: which model this is (when the harness says), its profile with status and
  version, and the note `Guards: on`. Study context is not loaded here; a study is defined with the researcher first.
* `mmo-guard pre-tool-use` - before a tool runs:
  - deny a path outside the project root (the system temp folder and this project's own Claude folder are allowed);
  - deny reading a study's data (`sources/<id>/text.md`, `segments.jsonl`, `ingest/`, `files/`, `ground-truth/`, the
    study's `work/`) until a model has a confirmed profile and a confirmed position in that study written from the
    current profile version;
  - ask the owner (permission prompt) when a profile or a position is being set to `confirmed`;
  - keep a blind probe blind (T45): when the harness names the subagent `blind-probe`, it reads nothing of a
    study but its position, runs no `mmo` but `memo add`, and gets no web tools;
  - keep the critic's brief (`topics/<slug>/critic/`) the researcher's: a model does not write it (T46);
  - the critic runs through `mmo critic run` (`agy`), never as a Claude Code subagent (T46);
  - deny web search and web fetch except during an open run of the model (`mmo run start`, recorded `web: true`, not
    yet `mmo run close`) in a study whose researcher lets it search the web (`analysis.web_search` of `topic.yaml`;
    T44, T48, ADR 0015). A web call names no study, so the run says which study it is for; `MMO_STUDY` (set by
    `mmo critic run`) narrows it to one study.

`mmo-guard agy-pre-tool-use` is the same guard as a `PreToolUse` hook of the Antigravity CLI (`.agents/hooks.json`
of the environment, T46): it maps `agy`'s tools onto the checks above. `agy` treats an answer without a decision as
a denial, so a call the guard does not object to is `allow` inside a critic's run (`MMO_CRITIC_RUN`, set by
`mmo critic run`) and `ask` otherwise. In round 1 of a critic's run (`MMO_CRITIC_ROUND=1`) the lead's memos,
analysis files and the other analysts' positions stay closed: the critic reads independently first.

The Bash checks are heuristics: they read paths out of the command line, not out of everything a shell can do.
Only the standard library and PyYAML, so the hook starts quickly; nothing here imports the rest of `mmo`.
"""

from __future__ import annotations

import glob
import json
import os
import re
import shlex
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

import yaml

GATED_IN_SOURCE = {"text.md", "segments.jsonl", "ingest", "files", "ground-truth"}
CONTENT_SEARCH = {"grep", "egrep", "fgrep", "rg", "ag", "ack", "findstr", "select-string"}
ALWAYS_RECURSIVE = {"rg", "ag", "ack"}
DEVICES = re.compile(r"(?i)^(/dev/\S+|/proc/\S+|nul|con|\\\\\.\\nul)$")  # shell devices, e.g. `2>/dev/null`
CONFIRMED_ANYWHERE = re.compile(r"(?i)status:\s*confirmed")
DRIVE_POSIX = re.compile(r"^/([a-zA-Z])(/|$)")
DRIVE_WIN = re.compile(r"^[a-zA-Z]:[\\/]")
GLOB_CHARS = re.compile(r"[*?\[]")
WEB_TOOLS = {"WebSearch", "WebFetch"}


# ---------------------------------------------------------------- paths


def project_root(env: dict[str, str] | None = None, cwd: str | None = None) -> Path:
    env = os.environ if env is None else env
    return Path(env.get("CLAUDE_PROJECT_DIR") or cwd or os.getcwd()).resolve()


def to_path(token: str, cwd: Path) -> Path:
    """A path as written in a tool call or a command line (Windows, Git Bash `/g/...`, `~`, relative)."""
    text = token.strip().strip("'\"")
    if os.name == "nt":  # Git Bash spellings; on Linux and macOS these are real paths
        if match := DRIVE_POSIX.match(text):
            text = f"{match.group(1).upper()}:/{text[match.end() :]}"
        elif text == "/tmp" or text.startswith("/tmp/"):  # Git Bash maps /tmp to the user's temp folder
            text = tempfile.gettempdir() + text[4:]
    if text.startswith("~"):
        text = str(Path.home()) + text[1:]
    path = Path(text)
    if not path.is_absolute():
        path = cwd / path
    return Path(os.path.normpath(path))


def inside(path: Path, base: Path) -> bool:
    try:
        Path(os.path.normcase(path)).relative_to(Path(os.path.normcase(base)))
        return True
    except ValueError:
        return False


def claude_project_dir(root: Path) -> Path:
    """Claude Code's own folder for this project (session logs, its memory): ~/.claude/projects/<root, dashed>."""
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(root))


def agy_brain_dir() -> Path:
    """The Antigravity CLI's own folder of conversations (its task logs, artifacts): ~/.gemini/antigravity-cli/brain."""
    return Path.home() / ".gemini" / "antigravity-cli" / "brain"


def allowed_outside(path: Path, root: Path) -> bool:
    return (
        inside(path, Path(tempfile.gettempdir()).resolve())
        or inside(path, claude_project_dir(root))
        or inside(path, agy_brain_dir())
    )


# ---------------------------------------------------------------- analysts and studies


def _status(text: str) -> str:
    match = re.search(r"(?im)^\s*>?\s*status:\s*([a-z]+)", text)
    return match.group(1).lower() if match else ""


def _version(text: str) -> str:
    match = re.search(r"(?im)^\s*>?\s*version:\s*([0-9][0-9-]*)", text)
    return match.group(1) if match else ""


def front_matter(text: str) -> dict:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    try:
        data = yaml.safe_load(text[3:end]) if end > 0 else None
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


@dataclass
class Profile:
    model_id: str
    status: str
    version: str


def profiles(root: Path) -> dict[str, Profile]:
    found = {}
    for path in sorted((root / "analysts").glob("*.md")):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        text = path.read_text(encoding="utf-8")
        first_line = text.splitlines()[0].lower() if text else ""
        if "model profile" not in first_line:  # researcher profiles live here too
            continue
        found[path.stem] = Profile(path.stem, _status(text), _version(text))
    return found


def study_open(root: Path, slug: str, model_id: str | None = None) -> tuple[bool, str]:
    """Whether a model may read the data of `topics/<slug>/`, and if not, what is missing."""
    known = profiles(root)
    candidates = [model_id] if model_id else sorted(known)
    if not candidates:
        return False, "no model profile in analysts/ (skill profile-model)"
    reasons = []
    for mid in candidates:
        profile = known.get(mid)
        if profile is None:
            reasons.append(f"{mid}: no profile analysts/{mid}.md (skill profile-model)")
            continue
        if profile.status != "confirmed":
            reasons.append(f"{mid}: profile not confirmed by the owner (status {profile.status or 'missing'})")
            continue
        position = root / "topics" / slug / "positions" / f"{mid}.md"
        if not position.is_file():
            reasons.append(f"{mid}: no position in the study, topics/{slug}/positions/{mid}.md (skill state-position)")
            continue
        meta = front_matter(position.read_text(encoding="utf-8"))
        if str(meta.get("profile_version", "")) != profile.version:
            reasons.append(
                f"{mid}: position written from profile version {meta.get('profile_version')}, "
                f"profile is {profile.version} (skill state-position again)"
            )
            continue
        if str(meta.get("status", "")).lower() != "confirmed":
            reasons.append(f"{mid}: position not confirmed by the owner")
            continue
        return True, ""
    return False, "; ".join(reasons)


def gated_study(path: Path, root: Path) -> str | None:
    """The study slug when `path` is study data, else None."""
    if not inside(path, root):
        return None
    parts = Path(os.path.relpath(path, root)).parts
    if len(parts) >= 3 and parts[0] == "topics" and parts[2] == "work":
        return parts[1]
    if len(parts) >= 5 and parts[0] == "topics" and parts[2] == "sources" and parts[4] in GATED_IN_SOURCE:
        return parts[1]
    return None


def studies_below(path: Path, root: Path) -> list[str]:
    """Studies whose data lie under the folder `path` (a recursive search there would read them)."""
    if not inside(path, root):
        return []
    parts = Path(os.path.relpath(path, root)).parts
    parts = () if parts == (".",) else parts
    topics = root / "topics"
    if not parts:
        return sorted(p.name for p in topics.iterdir() if p.is_dir()) if topics.is_dir() else []
    if parts == ("topics",):
        return studies_below(root, root)
    if parts[0] == "topics" and (len(parts) == 2 or (len(parts) in (3, 4) and parts[2] == "sources")):
        return [parts[1]]
    return []


# ---------------------------------------------------------------- decisions


def decision(kind: str, reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": kind,
            "permissionDecisionReason": reason,
        }
    }


def is_record(path: Path, root: Path) -> bool:
    """A model profile or a position in a study: files the owner confirms."""
    if not inside(path, root) or path.suffix != ".md":
        return False
    parts = Path(os.path.relpath(path, root)).parts
    if len(parts) == 2 and parts[0] == "analysts":
        return not parts[1].startswith("_") and parts[1].lower() != "readme.md"
    return len(parts) == 4 and parts[0] == "topics" and parts[2] == "positions"


def check_path(path: Path, root: Path, model_id: str | None, reading: bool = True) -> dict | None:
    if not inside(path, root):
        if allowed_outside(path, root):
            return None
        return decision(
            "deny",
            f"{path} is outside the research environment ({root}). Everything the analysis needs "
            "is inside it; if something seems missing, ask the owner instead of looking elsewhere.",
        )
    if reading and (slug := gated_study(path, root)):
        ok, missing = study_open(root, slug, model_id)
        if not ok:
            return decision(
                "deny",
                f"The data of the study {slug} stay closed until the steps in AGENTS.md are done "
                f"and confirmed: {missing}.",
            )
    return None


def check_search(path: Path, root: Path, model_id: str | None) -> dict | None:
    if found := check_path(path, root, model_id):
        return found
    for slug in studies_below(path, root):
        ok, missing = study_open(root, slug, model_id)
        if not ok:
            return decision(
                "deny",
                f"A content search in {path} would read the data of the study {slug}, which "
                f"stay closed ({missing}). Search a narrower folder (e.g. methods/, analysts/, "
                f"topics/{slug}/memos/).",
            )
    return None


def text_after(tool: str, data: dict, current: str) -> str:
    """The file's text as it would be after a Write, Edit or MultiEdit."""
    if tool == "Write":
        return data.get("content", "")
    text = current
    for edit in data.get("edits") or [data]:
        old, new = edit.get("old_string", ""), edit.get("new_string", "")
        if old:
            text = text.replace(old, new) if edit.get("replace_all") else text.replace(old, new, 1)
    return text


def ask_if_confirming(path: Path, root: Path, tool: str, data: dict) -> dict | None:
    """Ask the owner when a profile or a position goes from not confirmed to confirmed."""
    if not is_record(path, root):
        return None
    current = path.read_text(encoding="utf-8") if path.is_file() else ""
    if _status(text_after(tool, data, current)) == "confirmed" and _status(current) != "confirmed":
        return decision("ask", f"Setting {path.name} to confirmed: only the owner confirms a profile or a position.")
    return None


def bash_tokens(command: str) -> list[list[str]]:
    """Simple commands of a command line, each as its words."""
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()<>")
    lexer.whitespace_split = True
    try:
        words = list(lexer)
    except ValueError:
        words = command.split()
    commands, current = [], []
    for word in words:
        if word and set(word) <= set(";&|()<>"):
            if current:
                commands.append(current)
            current = []
        else:
            current.append(word)
    if current:
        commands.append(current)
    return commands


def looks_like_path(word: str) -> bool:
    return (
        "/" in word or "\\" in word or word.startswith(("~", ".")) or bool(DRIVE_WIN.match(word))
    ) and "://" not in word


# `mmo` commands that work on a study: `mmo <command> <action> <topic> ...`; they read its text or write its analysis
BLIND_ROLE = "blind-probe"
CRITIC_ROLE = "critic"
CRITIC_HERE = (
    "The critic is a model of another maker: it runs through mmo critic run (the Antigravity CLI), not as a subagent "
    "of the lead (ADR 0014)."
)


def blind_path(path: Path, root: Path) -> bool:
    """A path a blind probe may not touch: anything of a study but its positions."""
    if not inside(path, root):
        return False
    parts = Path(os.path.relpath(path, root)).parts
    return len(parts) >= 2 and parts[0] == "topics" and not (len(parts) >= 3 and parts[2] == "positions")


BLIND = (
    "You are a blind probe: answer from training only, with the title and the author you were given. The study's "
    "files, other mmo commands and the web stay closed to you; write your answer with mmo memo add."
)


def check_blind(tool: str, data: dict, cwd: Path, root: Path) -> dict | None:
    if tool in WEB_TOOLS:
        return decision("deny", BLIND)
    if tool == "Bash":
        for words in bash_tokens(data.get("command", "")):
            args = mmo_args(words)
            if args is not None and args[:2] != ["memo", "add"]:
                return decision("deny", BLIND)
            values = [w.split("=", 1)[1] if w.startswith("-") and "=" in w else w for w in words]
            if any(looks_like_path(v) and blind_path(to_path(v, cwd), root) for v in values):
                return decision("deny", BLIND)
        return None
    raw = data.get("file_path") or data.get("notebook_path") or data.get("path") or "."
    if tool in ("Read", "NotebookRead", "Grep", "Glob") and (
        blind_path(to_path(raw, cwd), root) or to_path(raw, cwd) in (root, root / "topics")
    ):
        return decision("deny", BLIND)
    return None


MMO_NO_ACTION = {"outline"}  # `mmo outline <topic> <source>`: the study is the first argument
MMO_STUDY_COMMANDS = {
    "quote",
    "code",
    "relation",
    "memo",
    "analysis",
    "review",
    "run",
    "context",
    "critic",
    "outline",
    "coverage",
}
WRITES_FILES = re.compile(
    r"(>|\btee\b|\bsed\s+(-\w*i|--in-place)|\b(cp|mv|rm|del|move|copy)\b|Set-Content|Out-File|Add-Content)"
)


def mmo_args(words: list[str]) -> list[str] | None:
    """The arguments of an `mmo` call (`mmo ...`, `uv run mmo ...`), or None for another program."""
    program = Path(words[0]).name.lower().removesuffix(".exe")
    if program == "mmo":
        return words[1:]
    if program == "uv" and words[1:3] == ["run", "mmo"]:
        return words[3:]
    return None


def option(args: list[str], name: str) -> str | None:
    for i, word in enumerate(args):
        if word == name and i + 1 < len(args):
            return args[i + 1]
        if word.startswith(name + "="):
            return word.split("=", 1)[1]
    return None


def check_mmo(words: list[str], root: Path, model_id: str | None) -> dict | None:
    """`mmo` on a study is closed exactly when reading its `text.md` is; a model writes only under its own id."""
    args = mmo_args(words)
    if args and args[0] == "review" and len(args) > 1 and args[1] != "list" and model_id:
        return decision(
            "deny",
            "Only the researcher decides proposals (mmo review). Comment on a proposal in a memo instead.",
        )
    if args and args[0] == "phase" and model_id:
        return decision(
            "deny",
            "The researcher says where the study is (mmo phase): the phase decides what a model may propose. "
            "Suggest a phase in a memo instead.",
        )
    if args is None or len(args) < 3 or args[0] not in MMO_STUDY_COMMANDS:
        return None
    by = option(args, "--by")
    if model_id and by and by != model_id:
        return decision(
            "deny",
            f"You are {model_id}: write under your own id (--by {model_id}). Only the researcher writes as "
            f"themselves; a record of yours is a proposal until they decide.",
        )
    slug = Path(args[1] if args[0] in MMO_NO_ACTION else args[2]).name
    if not (root / "topics" / slug / "topic.yaml").is_file():
        return None
    ok, missing = study_open(root, slug, model_id)
    if ok:
        return None
    return decision(
        "deny",
        f"`mmo {args[0]}` works on the study {slug}, which stays closed until the steps in AGENTS.md are "
        f"done and confirmed: {missing}.",
    )


def in_brief(path: Path, root: Path) -> bool:
    """`topics/<slug>/critic/`: the critic's brief and runs, written by the researcher and by `mmo critic`."""
    if not inside(path, root):
        return False
    parts = Path(os.path.relpath(path, root)).parts
    return len(parts) >= 3 and parts[0] == "topics" and parts[2] == "critic"


BRIEF = (
    "topics/<slug>/critic/ holds the critic's brief, written by the researcher (not by an analyst the critic checks), "
    "and the record of its runs, written by mmo critic run. Propose a change of the brief in a memo."
)


def in_analysis(path: Path, root: Path) -> bool:
    """`topics/<slug>/analysis/...`: the analysis store, written by a model only through `mmo` (ADR 0013)."""
    if not inside(path, root):
        return False
    parts = Path(os.path.relpath(path, root)).parts
    return len(parts) >= 3 and parts[0] == "topics" and parts[2] == "analysis"


ANALYSIS_THROUGH_MMO = (
    "The analysis store topics/<slug>/analysis/ is written through mmo (mmo code, mmo relation, mmo memo), so every "
    "record carries its quotation, author and history. Use the mmo command instead."
)


def check_bash(command: str, cwd: Path, root: Path, model_id: str | None) -> dict | None:
    here = cwd
    for words in bash_tokens(command):
        if words[0] == "cd" and len(words) > 1:
            target = to_path(words[1], here)
            if found := check_path(target, root, model_id, reading=False):
                return found
            here = target
            continue
        program = Path(words[0]).name.lower()
        if found := check_mmo(words, root, model_id):
            return found
        recursive = (
            program in ALWAYS_RECURSIVE
            or (
                program in CONTENT_SEARCH
                and any(
                    w in ("-r", "-R", "--recursive")
                    or (w.startswith("-") and not w.startswith("--") and ("r" in w or "R" in w))
                    for w in words[1:]
                )
            )
            or (program == "git" and len(words) > 1 and words[1] == "grep")
        )
        paths = []
        # words[0] too: after a redirection (`> analysts/x.md`) the target opens a new word list
        for word in words if looks_like_path(words[0]) else words[1:]:
            value = word.split("=", 1)[1] if word.startswith("-") and "=" in word else word
            if word.startswith("-") and "=" not in word:
                continue
            if not looks_like_path(value) or DEVICES.match(value):
                continue
            if GLOB_CHARS.search(value):
                matches = glob.glob(str(to_path(value, here)), recursive=True)
                paths += [Path(m) for m in matches] or [to_path(re.split(r"[*?\[]", value)[0] or ".", here)]
            else:
                paths.append(to_path(value, here))
        for path in paths:
            if found := (check_search(path, root, model_id) if recursive else check_path(path, root, model_id)):
                return found
            if in_analysis(path, root) and mmo_args(words) is None and WRITES_FILES.search(command):
                return decision("deny", ANALYSIS_THROUGH_MMO)
            if in_brief(path, root) and mmo_args(words) is None and WRITES_FILES.search(command):
                return decision("deny", BRIEF)
            if CONFIRMED_ANYWHERE.search(command) and is_record(path, root):
                return decision(
                    "ask", "This command may set a profile or a position to confirmed: only the owner confirms them."
                )
        if recursive and not paths and (found := check_search(here, root, model_id)):
            return found
    return None


def web_approvals(root: Path) -> dict[str, list[str]]:
    """Study slug -> the models its researcher lets search the web (`analysis.web_search` of `topic.yaml`)."""
    found = {}
    for path in sorted((root / "topics").glob("*/topic.yaml")):
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        models = ((data.get("analysis") or {}) if isinstance(data, dict) else {}).get("web_search") or []
        if isinstance(models, list) and models:
            found[path.parent.name] = [str(m) for m in models]
    return found


def study_history(root: Path, slug: str) -> list[dict]:
    path = root / "topics" / slug / "analysis" / "history.jsonl"
    events = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def open_web_runs(root: Path, model_id: str | None, study: str | None = None) -> list[str]:
    """`<slug>/<run>` of the open runs that may search the web: recorded `web: true`, not closed, the model still
    approved by the study (T48)."""
    found = []
    for slug, models in web_approvals(root).items():
        if study and slug != study:
            continue
        history = study_history(root, slug)
        closed = {e.get("run") for e in history if e.get("op") == "run-closed"}
        for event in history:
            analyst = str(event.get("analyst"))
            if (
                event.get("op") == "run"
                and event.get("web") is True
                and event.get("run") not in closed
                and analyst in models
                and (not model_id or analyst == model_id)
            ):
                found.append(f"{slug}/{event.get('run')}")
    return found


def check_web(root: Path, model_id: str | None, study: str | None = None) -> dict | None:
    if open_web_runs(root, model_id, study):
        return None
    return decision(
        "deny",
        "The web is open only during a run in a study whose researcher lets this model search the web "
        "(analysis.web_search in topic.yaml; mmo run start records web: true) until the run is closed (mmo run "
        "close); no such run is open"
        + (f" in {study}" if study else "")
        + ". Search where the approved search plan says without the web, or write a request to the researcher "
        "(mmo context request).",
    )


def pre_tool_use(event: dict, root: Path, model_id: str | None = None) -> dict | None:
    tool = event.get("tool_name", "")
    if event.get("agent_type") == CRITIC_ROLE:
        return decision("deny", CRITIC_HERE)
    if event.get("agent_type") == BLIND_ROLE and (
        found := check_blind(tool, event.get("tool_input") or {}, Path(event.get("cwd") or root), root)
    ):
        return found
    if tool in WEB_TOOLS:
        return check_web(root, model_id, os.environ.get("MMO_STUDY"))
    data = event.get("tool_input") or {}
    cwd = Path(event.get("cwd") or root)
    if tool == "Bash":
        return check_bash(data.get("command", ""), cwd, root, model_id)
    if tool in ("Read", "NotebookRead"):
        return check_path(to_path(data.get("file_path") or data.get("notebook_path") or "", cwd), root, model_id)
    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = to_path(data.get("file_path") or data.get("notebook_path") or "", cwd)
        if found := check_path(path, root, model_id, reading=False):
            return found
        if in_analysis(path, root):
            return decision("deny", ANALYSIS_THROUGH_MMO)
        if in_brief(path, root):
            return decision("deny", BRIEF)
        return ask_if_confirming(path, root, tool, data)
    if tool == "Grep":
        return check_search(to_path(data.get("path") or ".", cwd), root, model_id)
    if tool == "Glob":
        base = to_path(data.get("path") or ".", cwd)
        pattern = data.get("pattern", "")
        if os.path.isabs(pattern) or DRIVE_POSIX.match(pattern):
            base = to_path(re.split(r"[*?\[]", pattern)[0] or "/", cwd)
        return check_path(base, root, model_id, reading=False)
    return None


# ---------------------------------------------------------------- the Antigravity CLI (agy)

AGY_WEB = re.compile(r"^(search_web|read_url_content|open_browser_url|read_browser_page|browser_.*|.*_browser_.*)$")
AGY_WRITE = re.compile(r"(write|replace|edit|sed_file|delete|move|rename|create)")
AGY_SEARCH = re.compile(r"(grep|search|find|list)")
PATH_KEY = re.compile(r"(?i)(path|file|dir|cwd|target|uri)")


def agy_paths(args: dict) -> list[str]:
    found = []
    for key, value in args.items():
        if isinstance(value, str) and PATH_KEY.search(key):
            found.append(value)
        elif isinstance(value, list) and PATH_KEY.search(key):
            found += [v for v in value if isinstance(v, str)]
    return found


def round_one_closed(path: Path, root: Path, model_id: str | None) -> bool:
    """In round 1 the critic reads independently: the lead's memos, analysis and positions stay closed."""
    if not inside(path, root):
        return False
    parts = Path(os.path.relpath(path, root)).parts
    if len(parts) < 3 or parts[0] != "topics":
        return False
    if parts[2] in ("memos", "analysis"):
        return True
    return parts[2] == "positions" and len(parts) >= 4 and Path(parts[3]).stem != model_id


ROUND_ONE = (
    "Round 1: read the sources whole and only the labels and definitions of the codes (mmo code list) - not the "
    "lead's memos, codings or positions. They open in round 2."
)


def agy_check(event: dict, root: Path, model_id: str | None, round_no: str | None) -> dict | None:
    """One `agy` tool call through the checks of the guard; a Claude-style decision or None."""
    call = event.get("toolCall") or {}
    name = str(call.get("name") or "")
    args = call.get("args") or {}
    cwd = Path(str(args.get("Cwd") or event.get("cwd") or root))
    if AGY_WEB.match(name):
        return check_web(root, model_id, os.environ.get("MMO_STUDY"))
    if name == "run_command":
        command = str(args.get("CommandLine") or "")
        if round_no == "1":
            mmo = [mmo_args(words) for words in bash_tokens(command)]
            if any(a and a[0] in ("memo", "review", "relation") and a[1:2] != ["add"] for a in mmo):
                return decision("deny", ROUND_ONE)
            if any(a and a[:2] in (["code", "show"], ["quote", "check"]) for a in mmo):
                return decision("deny", ROUND_ONE)
            for words in bash_tokens(command):
                for word in words[1:]:
                    if looks_like_path(word) and round_one_closed(to_path(word, cwd), root, model_id):
                        return decision("deny", ROUND_ONE)
        return check_bash(command, cwd, root, model_id)
    for raw in agy_paths(args):
        path = to_path(raw, cwd)
        if round_no == "1" and (
            round_one_closed(path, root, model_id)
            or (AGY_SEARCH.search(name) and not name.startswith("list") and studies_below(path, root))
        ):
            return decision("deny", ROUND_ONE)
        if AGY_WRITE.search(name):
            if found := check_path(path, root, model_id, reading=False):
                return found
            if in_analysis(path, root):
                return decision("deny", ANALYSIS_THROUGH_MMO)
            if in_brief(path, root):
                return decision("deny", BRIEF)
            if os.environ.get("MMO_CRITIC_RUN"):
                return decision("deny", "The critic writes only through mmo (mmo memo add, mmo code apply).")
            current = path.read_text(encoding="utf-8") if path.is_file() else ""
            text = str(args.get("Content") or args.get("CodeContent") or args.get("ReplacementContent") or "")
            if is_record(path, root) and _status(text or current) == "confirmed" and _status(current) != "confirmed":
                return decision("ask", "Only the owner confirms a profile or a position.")
        elif found := (
            check_search(path, root, model_id) if AGY_SEARCH.search(name) else check_path(path, root, model_id)
        ):
            return found
    return None


def agy_pre_tool_use(event: dict, root: Path, model_id: str | None = None, round_no: str | None = None) -> dict:
    """The answer `agy` expects: `{"decision": "allow"|"ask"|"deny"|"force_ask", "reason": ...}`."""
    found = agy_check(event, root, model_id, round_no)
    if found is None:
        return {"decision": "allow" if os.environ.get("MMO_CRITIC_RUN") else "ask"}
    out = found["hookSpecificOutput"]
    kind = "force_ask" if out["permissionDecision"] == "ask" else out["permissionDecision"]
    return {"decision": kind, "reason": out["permissionDecisionReason"]}


# ---------------------------------------------------------------- session start


def model_of(event: dict) -> str | None:
    model = event.get("model")
    if isinstance(model, dict):
        model = model.get("id") or model.get("model")
    if not model:
        return None
    return str(model).strip() or None


def session_start(event: dict, root: Path) -> str:
    known = profiles(root)
    lines = [
        f"Guards: on (mmo-guard). Work only inside {root}; the study data stay closed until the steps in "
        "AGENTS.md are confirmed; only the owner confirms a profile or a position.",
        "",
    ]
    model_id = model_of(event)
    if model_id:
        lines.append(f"The harness names this model `{model_id}`.")
        profile = known.get(model_id)
        if profile is None:
            lines.append(f"There is no profile analysts/{model_id}.md: step 1 is the skill profile-model.")
        else:
            lines.append(
                f"Profile analysts/{model_id}.md: status {profile.status or 'missing'}, version "
                f"{profile.version or 'missing'}. Its text follows; read it as who you are while you work."
            )
            lines += ["", (root / "analysts" / f"{model_id}.md").read_text(encoding="utf-8")]
    else:
        lines.append(
            "The harness did not name the model to this hook: take your exact id from what the harness "
            "states, then read analysts/<model-id>.md (step 1 of AGENTS.md)."
        )
        listing = (
            ", ".join(f"{p.model_id} ({p.status or 'no status'}, version {p.version or '-'})" for p in known.values())
            or "none"
        )
        lines.append(f"Model profiles here: {listing}.")
    lines += [
        "",
        "What is studied and by which method is not loaded here: it is settled with the researcher "
        "(AGENTS.md, step 2).",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- entry


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] not in ("session-start", "pre-tool-use", "agy-pre-tool-use"):
        print(
            "usage: mmo-guard session-start | pre-tool-use | agy-pre-tool-use  (reads the hook's JSON from stdin)",
            file=sys.stderr,
        )
        return 2
    raw = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    event = json.loads(raw) if raw.strip() else {}
    out = sys.stdout
    if hasattr(out, "reconfigure"):
        out.reconfigure(encoding="utf-8")
    if argv[0] == "agy-pre-tool-use":
        workspace = (event.get("workspacePaths") or [None])[0]
        root = Path(workspace or event.get("cwd") or os.getcwd()).resolve()
        model_id = os.environ.get("MMO_ANALYST") or None
        out.write(
            json.dumps(agy_pre_tool_use(event, root, model_id, os.environ.get("MMO_CRITIC_ROUND")), ensure_ascii=False)
        )
        return 0
    root = project_root(cwd=event.get("cwd"))
    if argv[0] == "session-start":
        context = session_start(event, root)
        out.write(
            json.dumps(
                {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}},
                ensure_ascii=False,
            )
        )
        return 0
    if result := pre_tool_use(event, root):
        out.write(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
