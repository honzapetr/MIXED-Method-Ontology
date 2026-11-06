---
name: write-plan
description: Write or update docs/spec.md and docs/plan.md from the brief and the owner's answers - small tasks with acceptance criteria, a verify command and touched paths. Use when planning or re-planning the project.
---
# Write the plan

1. Read `docs/brief.md`, `docs/answers.md`, `docs/progress.md` and the code.
2. List what is unclear. Anything that changes behaviour, data, scope, cost or security goes to the owner as a
   question (options + recommendation); do not continue on a guess. Technical choices you can make yourself go to
   an ADR in `docs/adr/` (`NNNN-title.md`: context, decision, consequences).
3. Write `docs/spec.md`: behaviour from the user's view, data model, interfaces, non-functional constraints,
   what is explicitly out of scope.
4. Write `docs/plan.md` as tasks. Each task:

   ```markdown
   ### T3 – Short name
   - Goal: one sentence.
   - Acceptance criteria: observable, testable bullet points.
   - Verify: one command that proves the criteria (usually the test command with a filter).
   - Paths: files or directories the task may touch.
   - Depends on: T1, T2
   ```

   Keep tasks small (one session, a reviewable diff). The first task sets up the stack, the commands in
   `.agents/lab.yaml` (a protected path – say so in the task) and CI when they are not there yet.
5. Commit on the planning branch with `docs: plan ...` and write the outcome.
