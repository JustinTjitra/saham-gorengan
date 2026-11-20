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
| 2026-11-20 | P0-05 | done (coder: haiku; planner corrected confidence in review) | see board | Planner downgraded the March 2020 halts and the 2020-03-13 rule change to C (single-outlet dates / [V-single]) and removed an unsourced 'from 2x'. Confidence rule used: A = primary IDX/OJK document read (none yet), B = multi-outlet, C = single outlet or unclear |
| 2026-11-20 | P0-06 | done (coder: sonnet; planner fixed 2 lines in review) | see board | SWAT now convicted at confidence B (single outlet, per research). Note says defendant 'SA (initials as reported)'; parties field still says SAS, not reconciled. Planner replaced the stale 'no verdict yet' note and the 'manipulation windows' docstring |
| 2026-11-20 12:14 | run (scheduled) | 3 chunks done (P0-04, P0-05, P0-06), 0 failed, 0 blocked; planned P1-06, P1-07, P3-03 | 7d45f38 | No owner answers; no new questions. P0-03's Acceleration Board rows still missing (launch date unverified), to be picked up by the re-verification chunk. Last green commit: 7d45f38 |
| 2026-11-20 | P0-08 | done (coder: sonnet, passed review first try) | see board | _rows now raises on wrong field counts; all shipped CSVs already well formed |
| 2026-11-20 | P1-01 | done (coder: sonnet; planner added 2 checks + 1 test in review) | see board | Adds pandas, numpy, pyarrow. Planner added 'missing date' and 'missing source' checks: a NaT date passed validation |
| 2026-11-20 | P1-02 | done (coder: sonnet, passed review first try) | see board | Store root from argument or SAHAM_DATA_DIR; refuses paths inside the repo except gitignored store/ |
| 2026-11-20 15:54 | run (manual, owner-started) | 3 chunks done (P0-08, P1-01, P1-02), 0 failed, 0 blocked | 1cfa44f | Owner answered Q1 in chat: Yahoo Finance only (no bulk datasets), recorded in QUESTIONS.md. Q2 reply was a question; asked the owner to clarify. Ready chunks: P1-03, P1-06, P1-07, P2-00a, P3-03. Last green commit: 1cfa44f |
| 2026-11-20 | P1-03 | done (coder: sonnet, passed review first try) | see board | Offline only; yfinance is an optional extra. Risk for the backfill chunk: a Yahoo row with a 0 price fails validate_bars for the whole batch |
| 2026-11-20 | P1-06 | done (coder: sonnet; planner made a 3-line performance fix) | see board | Loop filtered the whole panel once per ticker; now groups once. 900 tickers x 750 days runs in about 2 s |
