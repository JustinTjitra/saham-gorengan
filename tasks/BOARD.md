# Task board

Single source of truth for chunk status. The loop picks the first `todo` row whose deps are all `done`, top to bottom. Every row has a spec in `tasks/<id>.md`.

Statuses: `todo`, `doing`, `done`, `blocked`. Models: `haiku`, `sonnet`.

| id | title | phase | model | deps | status | commit |
|---|---|---|---|---|---|---|
| P0-07 | Task-board consistency test | P0 | sonnet | none | done | 7ef68d2 |
| P0-01 | Regime schema v2: boards and fixed-rupiah limits | P0 | sonnet | none | done | 5f4155a |
| P0-02 | Regular-board regimes Sep-Nov 2026 | P0 | sonnet | P0-01 | done | 81559d2 |
| P0-03 | Watchlist-board (full call auction) regime | P0 | sonnet | P0-02 | done | 74936c5 |
| P0-04 | Tick-size table and helpers | P0 | sonnet | none | todo | |
| P0-05 | Market events table | P0 | haiku | none | todo | |
| P0-06 | Label update: convicted and exchange_review classes | P0 | sonnet | P0-02 | todo | |
| P0-08 | Loader rejects malformed CSV rows | P0 | sonnet | none | todo | |
| P1-01 | Canonical bar schema and validate_bars | P1 | sonnet | none | todo | |
| P1-02 | Month-partitioned Parquet store | P1 | sonnet | P1-01 | todo | |
| P1-03 | Source protocol and Yahoo adapter (mocked) | P1 | sonnet | P1-01 | todo | |
| P2-00a | Synthetic panel generator with pump injection | P2 | sonnet | P1-01 | todo | |
| P2-00b | assert_no_lookahead test helper | P2 | sonnet | P2-00a | todo | |
