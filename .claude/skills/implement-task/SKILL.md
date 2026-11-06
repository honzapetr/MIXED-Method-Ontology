---
name: implement-task
description: Implement one task T<n> from docs/plan.md on its own branch - tests first where practical, verify, record progress. Use when asked to work on a planned task.
---
# Implement a task

1. Read the task in `docs/plan.md`, the related part of `docs/spec.md`, `docs/answers.md` and the last entries of
   `docs/progress.md`.
2. Make sure you are on `task/T<n>-<short-name>` (create it from `main` if it does not exist).
3. Write or extend tests for the acceptance criteria, then the code. Stay inside the task's paths.
4. Run the lint command and the task's `verify` command; fix until both pass. Never weaken a test.
5. Append to `docs/progress.md`:

   ```markdown
   ## T<n> – <date>
   - Done: what changed.
   - Verified: the command and its result.
   - Next: what the next session must know.
   ```

6. Commit with a Conventional Commit message and write the outcome. When something needs the owner's decision,
   stop and use the outcome status `question`.
