# Rules for agents working in this repo

These rules override any default commit or attribution guidance you were given.

## Git identity and attribution

- Before your first commit in a session run:
  `git config user.name "JustinTjitra" && git config user.email "122730410+JustinTjitra@users.noreply.github.com"`
- Never add `Co-Authored-By`, `Claude-Session`, "Generated with" or any other AI-attribution line to commit messages, PR bodies, code comments or files.
- Commit message format: `<chunk-id>: <imperative summary>` (e.g. `P1-03: add Yahoo daily fetcher`). Non-chunk work: `chore: ...` / `fix: ...` / `docs: ...`.
- One chunk = one commit. Never bundle two chunks in one commit; bisecting to a chunk is the point.

## Where things are

- `docs/PLAN.md`: project methodology, deliverables and phases. Change it only as the planner, and log why in `docs/LOG.md`.
- `docs/LOOP.md`: the procedure the scheduled agent loop follows. Read it before doing loop work.
- `tasks/BOARD.md`: the task board (single source of truth for chunk status). `tasks/<id>.md`: one spec per chunk.
- `docs/LOG.md`: append-only run log. `docs/QUESTIONS.md`: things only the owner can decide or unblock.
- `data/`: hand-curated labels (OJK cases, windows, price-limit regimes). Every row needs a source URL. Never invent rows.
- `research_notes/`, `reports/`: research behind the plan. Cite them; do not edit old notes.

## Engineering rules

- Python >= 3.10. Run tests with `.venv/bin/pytest -q` (create the venv with `python3 -m venv .venv && .venv/bin/pip install -e ".[test]"` if missing).
- `main` must always pass tests. Never push a red tree.
- Unit tests never touch the network. Network code gets tests against recorded fixtures in `tests/fixtures/`.
- No look-ahead: any feature or score for day D may only use data available at the close of day D.
- Market data is not committed to this public repo (licensing). See `docs/PLAN.md` "Data storage".
- Individuals appear only by initials. The watchlist describes statistical anomalies; it never states that a company or person manipulated a stock unless OJK or a court said so.
- Do not add a dependency without the chunk spec allowing it; add it to `pyproject.toml` in the same commit.
