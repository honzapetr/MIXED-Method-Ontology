"""The critic of another maker, started through the Antigravity CLI `agy` (T46, ADR 0014).

* The critic's model is set per study (`analysis.critic` of `topic.yaml`: `analyst`, the id of its profile, and
  `model`, the `agy` model). `mmo` refuses a critic of the same maker as a model that leads the study (the makers
  are read from the profiles, `| name, maker | <name>, <maker> |`).
* The critic's instructions are the **brief** `topics/<slug>/critic/brief.md`: the method's critic template (`roles:
  critic:` of `method.yaml`), copied by `mmo critic brief` and filled in by the researcher, who sets `status: ready`.
  A model does not write it (the guard).
* `mmo critic run --round 1|2` checks the critic's profile and position (confirmed, from the current profile, with
  the role `critic`) and the brief, starts a run of the role `critic`, and runs `agy -p <prompt> --model <model>
  --output-format stream-json` in the environment, with the environment's guard as an `agy` hook
  (`.agents/hooks.json`) told by `MMO_ANALYST`, `MMO_CRITIC_RUN` and `MMO_CRITIC_ROUND` who runs and in which round.
* The whole run is kept in `topics/<slug>/critic/runs/<run>/` (`prompt.md`, `stream.jsonl`, `response.md`,
  `check.yaml`) and in the history (`op: critic-run`). After the run `mmo` compares the environment's files with
  their state before: a critic may add memos and codings through `mmo`, nothing else; a run that changed more is
  reported (`status: violations`) and is not accepted.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from mmo.analysis.method import study_methods, study_settings
from mmo.analysis.roles import environment, front_matter, position_roles
from mmo.analysis.roles import role as role_of
from mmo.analysis.store import Author, Store, StoreError, is_model
from mmo.core.topic import Topic
from mmo.guard import study_open

ROLE = "critic"
MAKER_ROW = re.compile(r"(?im)^\|\s*name,\s*maker\s*\|\s*([^|]+)\|")
KNOWN_MAKERS = {"claude": "Anthropic", "gemini": "Google", "gpt": "OpenAI"}
STORE_FILES = ("codings.jsonl", "history.jsonl", "codebook.yaml", "relations.yaml")
SKIP_DIRS = {".git", ".venv", "__pycache__", "node_modules", "files", "ingest", ".pytest_cache", ".ruff_cache"}
PLACEHOLDER = re.compile(r"<fill:[^>]*>")
Runner = Callable[[list[str], Path, dict[str, str], int], tuple[int, str, str]]


# ---------------------------------------------------------------- who the critic is


def maker_of(topic: Topic, analyst: str) -> str:
    """The maker of a model, from the row `| name, maker | <name>, <maker> |` of its profile."""
    profile = environment(topic) / "analysts" / f"{analyst}.md"
    if profile.is_file() and (match := MAKER_ROW.search(profile.read_text(encoding="utf-8"))):
        return match.group(1).rsplit(",", 1)[-1].strip()
    for prefix, maker in KNOWN_MAKERS.items():
        if analyst.lower().startswith(prefix):
            return maker
    raise StoreError(f"the maker of {analyst} is not known: its profile has no row '| name, maker | ... |'")


def same_maker(a: str, b: str) -> bool:
    first = lambda m: m.lower().split()[0]  # noqa: E731 - "Google DeepMind" and "Google" are one maker
    return first(a) == first(b)


def critic_settings(topic: Topic) -> dict[str, Any]:
    return dict(study_settings(topic)["critic"])


def leads(topic: Topic, critic: str) -> list[str]:
    """The other models with a position in the study."""
    folder = topic.root / "positions"
    if not folder.is_dir():
        return []
    return [p.stem for p in sorted(folder.glob("*.md")) if p.stem != critic and is_model(topic, p.stem)]


def check_critic(topic: Topic) -> list[str]:
    """What stops the critic's run, in plain words; empty when it may run."""
    settings = critic_settings(topic)
    analyst = str(settings["analyst"])
    problems: list[str] = []
    ok, missing = study_open(environment(topic), topic.slug, analyst)
    if not ok:
        problems.append(f"the critic's profile and position: {missing} (written once per study, then confirmed)")
    elif ROLE not in position_roles(topic, analyst):
        problems.append(f"the position of {analyst} does not list the role critic under roles:")
    try:
        critic_maker = maker_of(topic, analyst)
        for lead in leads(topic, analyst):
            if same_maker(maker_of(topic, lead), critic_maker):
                problems.append(
                    f"{analyst} ({critic_maker}) is of the same maker as {lead}: the critic is a model of another "
                    "maker (analysis.critic in topic.yaml)"
                )
    except StoreError as err:
        problems.append(str(err))
    return problems


# ---------------------------------------------------------------- the brief


def brief_file(topic: Topic) -> Path:
    return topic.root / "critic" / "brief.md"


def template_of(topic: Topic) -> tuple[Path, str]:
    for method in study_methods(topic):
        prompt = (method.data.get("roles") or {}).get(ROLE)
        if prompt:
            path = method.folder / str(prompt)
            version = str(front_matter(path.read_text(encoding="utf-8")).get("version", ""))
            return path, f"{method.id}/{ROLE}@{version}"
    raise StoreError("no method of the study has a critic template (roles: critic: in method.yaml)")


def write_brief(topic: Topic, author: Author) -> Path:
    """Copy the method's critic template for the researcher to fill in."""
    if author.kind == "model":
        raise StoreError("the researcher writes the critic's brief, not the analyst it criticises")
    path = brief_file(topic)
    if path.exists():
        raise StoreError(f"{path.relative_to(topic.root).as_posix()} exists already; edit it")
    template, version = template_of(topic)
    body = template.read_text(encoding="utf-8").split("\n---", 1)[1].lstrip("-\n")
    header = {
        "template": version,
        "study": topic.slug,
        "written_by": author.id,
        "created": datetime.now(UTC).date().isoformat(),
        "status": "draft",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    text = f"---\n{yaml.safe_dump(header, allow_unicode=True, sort_keys=False)}---\n\n{body}"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def read_brief(topic: Topic) -> tuple[dict[str, Any], str]:
    path = brief_file(topic)
    if not path.is_file():
        raise StoreError(f"no brief for the critic: mmo critic brief {topic.slug} --by <researcher>, then fill it in")
    text = path.read_text(encoding="utf-8")
    meta = front_matter(text)
    if meta.get("status") != "ready":
        raise StoreError("the critic's brief is not ready: the researcher fills it in and sets status: ready")
    if left := PLACEHOLDER.findall(text):
        raise StoreError(f"the critic's brief still has {len(left)} places to fill in ({left[0]} ...)")
    return meta, text.split("\n---", 1)[1].lstrip("-\n")


def round_section(body: str, round_no: int) -> str:
    """The brief without the section of the other round (`## Round 1`, `## Round 2`)."""
    other = 2 if round_no == 1 else 1
    parts = re.split(r"(?m)^(## Round [12]\b.*)$", body)
    out, skip = [parts[0]], False
    for i in range(1, len(parts), 2):
        skip = parts[i].startswith(f"## Round {other}")
        if not skip:
            out += [parts[i], parts[i + 1]]
    return "".join(out).strip()


# ---------------------------------------------------------------- the run


def snapshot(root: Path) -> dict[str, tuple[int, int]]:
    """Size and modification time of the environment's files (not git, environments, originals, ingest)."""
    state = {}
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = Path(folder) / name
            try:
                stat = path.stat()
            except OSError:
                continue
            state[path.relative_to(root).as_posix()] = (stat.st_size, stat.st_mtime_ns)
    return state


def changes(before: dict[str, tuple[int, int]], after: dict[str, tuple[int, int]]) -> list[str]:
    return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))


def allowed_change(path: str, slug: str, run_dir: str) -> bool:
    base = f"topics/{slug}/"
    return (
        (path.startswith(base + "memos/") and path.endswith(".md"))
        or path in {base + f"analysis/{n}" for n in STORE_FILES}
        or path.startswith(run_dir + "/")
    )


def prompt_text(topic: Topic, event: dict[str, Any], round_no: int, brief: str, template: str) -> str:
    role = role_of(environment(topic), ROLE)
    role_body = role.path.read_text(encoding="utf-8").split("\n---", 1)[1].lstrip("-\n")
    analyst, run = event["analyst"], event["run"]
    return f"""# The critic of the study {topic.slug} - round {round_no}

You are `{analyst}`, the critic of this study, in run `{run}`. Work only inside this repository (the research
environment). Read `AGENTS.md` first. Write every finding through `mmo` under your own id and this run:
`uv run mmo memo add {topic.slug} --by {analyst} --run {run} ...` and, for counter-evidence on an existing code,
`uv run mmo code apply {topic.slug} <code id> <source> "<exact words>" --by {analyst} --run {run}
--note "counter-evidence: ..."`.
Never edit files by hand. The environment's guard runs on your tools.

## Your role ({role.prompt_version})

{role_body.strip()}

## The brief of the researcher ({template}), for round {round_no}

{brief}
"""


def default_runner(cmd: list[str], cwd: Path, env: dict[str, str], timeout: int) -> tuple[int, str, str]:
    done = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, timeout=timeout)
    return done.returncode, done.stdout.decode("utf-8", "replace"), done.stderr.decode("utf-8", "replace")


def critic_runs(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [e for e in history if e.get("op") == "critic-run"]


def run_critic(
    topic: Topic,
    author: Author,
    round_no: int,
    timeout_minutes: int | None = None,
    runner: Runner | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Start the critic through `agy`, keep the whole run, check what it changed (T46)."""
    if round_no not in (1, 2):
        raise StoreError("--round 1 (own reading first) or 2 (comparison with the lead)")
    if problems := check_critic(topic):
        raise StoreError("; ".join(problems))
    meta, body = read_brief(topic)
    store = Store(topic)
    if round_no == 2 and not any(e.get("round") == 1 and e.get("status") == "ok" for e in critic_runs(store.history())):
        raise StoreError("round 2 compares the critic's own reading with the lead's: run round 1 first (status ok)")
    settings = critic_settings(topic)
    analyst, model = str(settings["analyst"]), str(settings["model"])
    agy = shutil.which("agy")
    if not agy and runner is None and not dry_run:
        raise StoreError("agy (the Antigravity CLI) is not on PATH")
    event = store.start_run(author, analyst, ROLE, [f"critic/brief.md (round {round_no})"], note=f"model {model}")
    run = event["run"]
    root = environment(topic)
    run_dir = topic.root / "critic" / "runs" / run
    run_dir.mkdir(parents=True, exist_ok=True)
    rel_run_dir = run_dir.relative_to(root).as_posix()
    prompt = prompt_text(topic, event, round_no, round_section(body, round_no), str(meta.get("template")))
    (run_dir / "prompt.md").write_text(prompt, encoding="utf-8", newline="\n")
    cmd = [agy or "agy", "-p", prompt, "--model", model, "--output-format", "stream-json", "--sandbox"]
    record: dict[str, Any] = {
        "run": run,
        "round": round_no,
        "analyst": analyst,
        "model": model,
        "prompt_version": event["prompt_version"],
        "brief": {"template": meta.get("template"), "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest()},
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "record": rel_run_dir,
    }
    if dry_run:
        record.update(status="dry-run", command=[Path(cmd[0]).name, "-p", "<prompt.md>", *cmd[3:]])
        Store(topic).save(author, "critic-run", **record)
        return record
    env = {
        **os.environ,
        "MMO_ANALYST": analyst,
        "MMO_CRITIC_RUN": run,
        "MMO_CRITIC_ROUND": str(round_no),
        "MMO_STUDY": topic.slug,
    }
    timeout = 60 * int(timeout_minutes or settings.get("timeout_minutes") or 60)
    before = snapshot(root)
    started = datetime.now(UTC)
    try:
        code, out, err = (runner or default_runner)(cmd, root, env, timeout)
    except subprocess.TimeoutExpired as exc:
        code, out, err = -1, (exc.stdout or b"").decode("utf-8", "replace"), f"timeout after {timeout} s"
    (run_dir / "stream.jsonl").write_text(out, encoding="utf-8", newline="\n")
    response, steps, denied = parse_stream(out)
    (run_dir / "response.md").write_text(response, encoding="utf-8", newline="\n")
    changed = changes(before, snapshot(root))
    violations = [p for p in changed if not allowed_change(p, topic.slug, rel_run_dir)]
    written = Store(topic).run_records(run)
    status = "violations" if violations else ("ok" if code == 0 else "failed")
    record.update(
        status=status,
        exit_code=code,
        started=started.isoformat(timespec="seconds"),
        minutes=round((datetime.now(UTC) - started).total_seconds() / 60, 1),
        steps=steps,
        denied_by_guard=denied,
        wrote=written,
        changed=changed,
        violations=violations,
    )
    if err.strip():
        record["stderr"] = err.strip()[-2000:]
    (run_dir / "check.yaml").write_text(
        yaml.safe_dump(record, allow_unicode=True, sort_keys=False), encoding="utf-8", newline="\n"
    )
    Store(topic).save(author, "critic-run", **record)
    return record


def parse_stream(out: str) -> tuple[str, int, int]:
    """The final response, the number of tool steps and of calls the guard denied, from `agy` stream-json."""
    response, steps, denied = "", 0, 0
    for line in out.splitlines():
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("event") == "result":
            response = str((row.get("result") or {}).get("response") or "")
        step = row.get("step_update") or {}
        if step.get("state") == "DONE" and step.get("step_type") not in (None, "user_input", "agent_response"):
            steps += 1
        if "denied by pre-tool hook" in json.dumps(row, ensure_ascii=False):
            denied += 1
    return response, steps, denied
