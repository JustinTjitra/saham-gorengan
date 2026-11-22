# Task board

Single source of truth for chunk status. The loop picks the first `todo` row whose deps are all `done`, top to bottom. Every row has a spec in `tasks/<id>.md`.

Statuses: `todo`, `doing`, `done`, `blocked`. Models: `haiku`, `sonnet`.

| id | title | phase | model | deps | status | commit |
|---|---|---|---|---|---|---|
| P0-07 | Task-board consistency test | P0 | sonnet | none | done | 7ef68d2 |
| P0-01 | Regime schema v2: boards and fixed-rupiah limits | P0 | sonnet | none | done | 5f4155a |
| P0-02 | Regular-board regimes Sep-Nov 2026 | P0 | sonnet | P0-01 | done | 81559d2 |
| P0-03 | Watchlist-board (full call auction) regime | P0 | sonnet | P0-02 | done | 74936c5 |
| P0-04 | Tick-size table and helpers | P0 | sonnet | none | done | 5153fe9 |
| P0-05 | Market events table | P0 | haiku | none | done | 02c4df5 |
| P0-06 | Label update: convicted and exchange_review classes | P0 | sonnet | P0-02 | done | 0906d56 |
| P0-08 | Loader rejects malformed CSV rows | P0 | sonnet | none | done | a2cab0a |
| P1-01 | Canonical bar schema and validate_bars | P1 | sonnet | none | done | b1ff86d |
| P1-02 | Month-partitioned Parquet store | P1 | sonnet | P1-01 | done | 1cfa44f |
| P1-03 | Source protocol and Yahoo adapter (mocked) | P1 | sonnet | P1-01 | done | b565729 |
| P1-06 | Trading calendar and missing-day flags | P1 | sonnet | P1-01 | done | 832ba7b |
| P1-07 | Data-quality flags | P1 | sonnet | P1-01, P0-04 | done | 7168a8e |
| P1-08 | Corporate-action suspect flags | P1 | sonnet | P1-07 | done | edd251a |
| P1-09 | Backfill command (offline-tested) | P1 | sonnet | P1-02, P1-03 | done | 5959910 |
| P1-10 | Ticker-universe file loader and fetch plan | P1 | sonnet | P1-09 | done | 1c1a9d1 |
| P2-00a | Synthetic panel generator with pump injection | P2 | sonnet | P1-01 | done | 74fa641 |
| P2-00b | assert_no_lookahead test helper | P2 | sonnet | P2-00a | done | b22a6b5 |
| P2-01 | Limit-normalised returns, limit hits, ARA run | P2 | sonnet | P1-01 | done | 76ad918 |
| P2-03 | Robust volume, turnover and value z-scores | P2 | sonnet | P2-00b | done | f408533 |
| P2-02 | Market-adjusted abnormal returns | P2 | sonnet | P2-00b | done | 3458774 |
| P2-04 | Run-up and drawdown features | P2 | sonnet | P2-00b | done | 6e10a0d |
| P2-05 | Liquidity measures and liquidity buckets | P2 | sonnet | P2-00b | done | 67d06d5 |
| P2-06 | Range volatility with limit-day censoring | P2 | sonnet | P2-01 | done | 8a9c1e4 |
| P2-07 | Trade-size and foreign-flow features (null-safe) | P2 | sonnet | P2-03 | done | f863855 |
| P2-08 | Feature assembler | P2 | sonnet | P1-08, P2-01, P2-02, P2-03, P2-04, P2-05, P2-06, P2-07 | done | 26e72e8 |
| P2-09 | Mask rolling-window features after a corporate-action day | P2 | sonnet | P2-08 | done | 55d157f |
| P3-01 | Ticker-day label panel | P3 | sonnet | P1-01 | done | 27f9d5c |
| P3-02 | ARA-run weak label | P3 | sonnet | P2-01 | done | 67e649b |
| P3-03 | Surveillance events schema and reason classifier | P3 | sonnet | none | done | 46a550c |
| P4-01 | Baseline rankers | P4 | sonnet | P2-01, P2-03 | done | 7ef32e3 |
| P4-02 | Robust z-score composite per liquidity bucket | P4 | sonnet | P2-05 | done | 407b3ed |
| P5-01 | Event-level recall, share-in-top-k, lead time | P5 | sonnet | P3-01, P4-01 | done | cfc0a60 |
| P4-05 | Episode builder | P4 | sonnet | P4-01 | done | 228cf5e |
| P5-01b | Placebo windows and random-ranker baseline | P5 | sonnet | P5-01 | done | edd5f7a |
| P5-02 | Leave-one-case-out splits with embargo | P5 | sonnet | P5-01 | done | |
| P5-03 | Synthetic-injection recovery test | P5 | sonnet | P2-08, P4-01, P4-02, P5-01 | done | 1e27df2 |
| P5-03b | Recovery difficulty sweep with random baseline | P5 | sonnet | P5-03, P5-01b | done | e5ebbd3 |
| P5-04 | Alert-burden and weak-label overlap metrics | P5 | sonnet | P5-01 | done | 3018c8e |
| P4-03 | Isolation forest per bucket, walk-forward | P4 | sonnet | P4-02 | done | b68ce35 |
| P4-04 | PU ranker, leave-one-case-out | P4 | sonnet | P5-02, P4-02 | todo | |
| P4-06 | Rank ensemble | P4 | sonnet | P4-01, P4-02, P4-03 | done | 207c96d |
| P4-07 | Price-only trend-persistence detector | P4 | sonnet | P4-01, P5-03b | done | de6cd5d |
| P5-05 | Evaluation report generator | P5 | sonnet | P5-01, P5-01b, P5-04 | done | a92e182 |
| P5-06 | Evaluation pipeline from features and windows to report inputs | P5 | sonnet | P5-05, P4-06 | done | 34a611d |
| P5-07 | Report recall by price-limit regime | P5 | sonnet | P5-05 | done | 204ec2d |
| P6-01 | `saham-gorengan score --date` command | P6 | sonnet | P1-02, P2-09, P4-02 | done | e0807e3 |
| P6-02 | Watchlist writer with explanations and wording rules | P6 | sonnet | P6-01 | done | 4d197ea |
| P6-03 | Scheduled daily refresh and score (needs Q3, Q4, Q5) | P6 | sonnet | P6-02, P1-10 | blocked | |
