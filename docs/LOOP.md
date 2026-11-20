# Agent loop runbook

A scheduled task starts a fresh cloud session every 4 hours. That session is the **planner**: it runs on the expensive model, reads this file, and follows it exactly. Code is written by **coder** subagents on cheaper models. The planner reviews, tests, commits and pushes.

The loop keeps no memory between runs. Everything it knows is in this repo: `tasks/BOARD.md`, the chunk specs, `docs/LOG.md`, `docs/QUESTIONS.md` and git history.

## Roles

| Role | Model | Does | Never does |
|---|---|---|---|
| Planner | session model (expensive) | Picks chunks, writes and splits specs, reviews diffs, diagnoses failures, commits, pushes, re-plans | Writes feature code itself, except a fix of 10 lines or fewer after a failed review |
| Coder | `sonnet` by default, `haiku` where the spec says so | Implements exactly one chunk spec, with tests, inside the files the spec lists | Commits, pushes, edits the board, touches files outside the spec |

## Each run, step by step

### 1. Set up (stop the run if any step fails, and log why)

```bash
cd <repo>
git fetch origin main && git checkout main && git reset --hard origin/main
git config user.name "JustinTjitra"
git config user.email "122730410+JustinTjitra@users.noreply.github.com"
test -d .venv || python3 -m venv .venv
.venv/bin/pip install -q -e ".[test]"
.venv/bin/pytest -q
```

If the baseline tests fail, this run is a **repair run**. Find the breaking commit (`git log`, `git bisect` between the last green commit in `docs/LOG.md` and HEAD). Fix it, or revert it with `git revert`. Commit as `fix: ...`, push, log it, and end the run.

### 2. Check for the owner

Read `docs/QUESTIONS.md`. If the owner has answered a question (text under `Answer:`), act on the answer: update the board or specs, then move the question to the `Resolved` section.

### 3. Pick work

From `tasks/BOARD.md`, pick the first chunk whose status is `todo` and whose `deps` are all `done`. Do at most **3 chunks per run**. Stop early if the run has spent about 90 minutes.

If no chunk is ready and some are still `todo`, they are blocked. Make sure each blocked chunk has an entry in `docs/QUESTIONS.md`, then go to step 7.

If every chunk in the current phase is `done`, go to step 7 to plan the next phase.

### 4. Dispatch to a coder

Set the chunk's status to `doing` (no commit yet). Spawn one coder with the Agent tool:
- `model`: the chunk's `model` field (`sonnet` or `haiku`)
- `subagent_type`: `general-purpose`
- `run_in_background`: false

The prompt is the template below, with the chunk spec pasted in full:

```
You are implementing one small, well-specified chunk of the saham-gorengan repo at <repo path>.
Read CLAUDE.md first and follow it. Then implement this spec exactly:

<paste tasks/<id>.md>

Rules:
- Only create or modify the files listed under "Files". If you think another file must change, stop and say so instead.
- Write the tests listed under "Acceptance" first, watch them fail, then implement.
- Unit tests must not use the network; use fixtures under tests/fixtures/.
- Run `.venv/bin/pytest -q` and make the whole suite pass.
- Do NOT commit, push, or edit tasks/ or docs/.
- Finish with: the files you changed, the test output summary, and anything in the spec that was ambiguous or that you could not do.
```

### 5. Review (planner, expensive model)

Do this yourself; don't delegate it.
1. `git status` and `git diff`: every changed file must be on the spec's `Files` list.
2. Read the diff against the spec's `Interface` and `Acceptance` sections. Check for look-ahead, network access in tests, silent `except: pass`, hard-coded dates or paths, and secrets.
3. Run `.venv/bin/pytest -q` yourself. Don't trust the coder's summary.
4. Decide:
   - **Pass**: go to step 6.
   - **Fail, fixable**: send the coder the specific findings and let it try again. Use SendMessage to the same agent if possible; otherwise spawn a new coder with the findings appended. Allow **2 retries**.
   - **Still failing after 2 retries**: discard the changes (`git checkout -- . && git clean -fd` limited to the spec's files). Then diagnose. If the spec was too big or unclear, split or rewrite it into smaller chunks and record that in the board. If the cause is a blocker (network host, credential, decision), set status `blocked` and add it to `docs/QUESTIONS.md`.

### 6. Commit and push

```bash
git add <files from spec> tasks/BOARD.md docs/LOG.md
git commit -m "<id>: <summary>"
git fetch origin main && git rebase origin/main && .venv/bin/pytest -q
git push origin main
```

Before committing, set the chunk to `done` on the board, add the short commit hash, and append a line to `docs/LOG.md`. If the push is rejected, fetch, rebase, re-run the tests and push again; retry up to 3 times. Never force-push `main`.

**Data refresh chunks:** when a chunk's job is to run the data pipeline rather than write code, the data goes to the data store described in `docs/PLAN.md`. It never goes to this repo.

### 7. Plan ahead (planner)

Keep at least 3 ready `todo` chunks on the board. When the board runs low, write the next chunks for the current phase of `docs/PLAN.md`. Each spec must follow `tasks/TEMPLATE.md` and the sizing rules below. Commit them as `plan: add <ids>`. If the plan itself needs to change, edit `docs/PLAN.md` and log the reason.

### 8. Log and end

Append a run entry to `docs/LOG.md`: date and time, chunks done, chunks failed or blocked, questions raised, and the last green commit. Commit as `log: run <date>` if anything changed since the last commit, then push.

## Sizing rules for chunk specs

- One purpose per chunk, and one module with its test module where possible. Aim for about 150 lines of new code; never exceed 300.
- The spec gives exact file paths, function signatures with types, input and output examples, and acceptance tests specific enough that two coders would write the same thing.
- Use `haiku` only for mechanical work: data entry from a given source, renames, docs, adding fixtures. Use `sonnet` for anything with logic.
- A chunk must be testable offline.
- A chunk that needs a network host the environment doesn't allow is `blocked` until the owner allows it.

## Safety rails

- Only `main` and the data store are ever written. No new branches or tags, and no releases unless the plan says so.
- Never edit `data/*.csv` labels without a source URL for each row. Never delete label rows; mark them as superseded in `notes` instead.
- Never weaken or delete a test to make a chunk pass, unless the spec says the test is wrong. If so, the planner explains why in the commit body.
- If something looks wrong and the runbook doesn't cover it, write it in `docs/QUESTIONS.md` and skip it. Don't improvise destructive fixes.
