@AGENTS.md

## Claude Code

* `.claude/skills/` and `.claude/agents/` are generated from `.agents/` by `python3 tools/agents_sync.py`; CI fails
  when they drift. Edit `.agents/`, then run the script.
* Subagents (`.claude/agents/`): `planner`, `coder`, `reviewer`, `advisor` – the same roles the lab uses.
