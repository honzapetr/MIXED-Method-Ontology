---
name: review-task
description: Review the change of one task against its acceptance criteria, the project rules and the tests, without editing anything. Use when asked to review a task branch or pull request.
---
# Review a task

1. Read the task in `docs/plan.md` and the diff against `main` (`git diff main...HEAD`).
2. Check, in this order:
   - every acceptance criterion is met and covered by a test;
   - the `verify` command passes (run it);
   - the change stays inside the task's paths and touches no protected path unless the task says so;
   - no secrets, no weakened or deleted tests, no dead code, clear names, errors handled;
   - `docs/progress.md` has an entry for the task.
3. Do not edit, commit or push.
4. Summary: `APPROVE` when all checks pass, otherwise `CHANGES:` with a numbered list of concrete findings
   (file, line, what is wrong, what to do). Write the outcome with status `done`.
