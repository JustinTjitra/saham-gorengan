# Run log

Append-only. Newest at the bottom. One entry per loop run, plus a line per chunk.

| When (UTC) | Run / chunk | Result | Commit | Notes |
|---|---|---|---|---|
| 2026-11-20 | setup | plan, runbook and task board created | | Last green commit: see git log |
| 2026-11-20 | P0-07 | done (manual dry run of the loop; coder: sonnet) | see board | Runbook fix: commit hash filled in by the log step |
| 2026-11-20 | run (manual) | 1 chunk done, 0 failed | 7ef68d2 | Last green commit: 7ef68d2 |
| 2026-11-20 | P0-01 | done (coder: sonnet, passed review first try) | see board | PriceLimits field order now follows the spec (regime_id first); no positional callers existed |
| 2026-11-20 | P0-02 | done (coder: sonnet; planner fixed 1 line in review) | see board | Coder left an unquoted comma in R2026-ARB7B notes (extra column, notes truncated, loader silent). Planner quoted it; loader hardening queued as P0-08 |
| 2026-11-20 | P0-03 | done (coder: sonnet; planner moved the FCA README row to the end of the table and fixed the stale regime count) | see board | Decree Peng-00001/BEI.PB1/03-2024 is from surveillance_weak_labels.md:120 |
| 2026-11-20 09:09 | run (scheduled) | 3 chunks done (P0-01, P0-02, P0-03), 0 failed, 0 blocked; planned P0-08 | 95abf08 | No owner answers in QUESTIONS.md; no new questions. Last green commit: 95abf08 |
| 2026-11-20 | P0-04 | done (coder: sonnet, passed review first try) | see board | Includes 2014-01-06 three-band period (start date single-source). round_to_tick can return 0 for sub-tick prices; left as is (spec silent) |
