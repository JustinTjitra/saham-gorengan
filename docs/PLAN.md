# saham-gorengan project plan

Status: v1, 2026-11-20. Owner: JustinTjitra. Only the planner role changes this file (see `docs/LOOP.md`), and every change is logged in `docs/LOG.md`.

## 1. Goal

Score every stock on the Indonesia Stock Exchange (IDX) every trading day for patterns typical of trade-based manipulation ("saham gorengan": pump-and-dump, ramping, wash trading). Then measure how well that score would have found the cases OJK and IDX later acted on.

The project has two final outputs:
1. **A backtested detector with an honest evaluation report.** It compares the detector to simple baselines on every known case from 2016 to 2026.
2. **A daily watchlist.** It ranks the stocks whose trading that day looks most anomalous, with the reasons.

**Non-goals:**
- Proving anyone manipulated anything.
- Producing trading signals.
- Doing real-time or intraday detection. That would need data we don't have.

## 2. Why the method is shaped this way

The research behind these points is in `research_notes/IDX manipulation detector sources/` and `reports/`.

- **Labels are scarce.** There are 8 OJK-sanctioned cases (13 windows), 2 cases on the criminal track, and a few IDX investigations from November 2026. Supervised learning on that is not viable. The detector is **unsupervised or rule-based**, and the known cases are used **only for evaluation**, plus at most a lightly regularised positive-unlabelled (PU) ranker evaluated with leave-one-case-out.
- **Unlabelled does not mean clean.** OJK handled about 29 cases between 2022 and early 2026, but almost none are named by ticker. The literature estimates that only a small fraction of manipulation is ever prosecuted. So precision measured against labels is a lower bound, and a false positive in this data may be a real case that was never caught.
- **Weak labels have a severity ladder.** From weakest to strongest:
  1. repeated upper-limit (ARA) runs, computed from prices;
  2. IDX Unusual Market Activity (UMA) notices;
  3. suspensions for price reasons;
  4. repeat suspension or move to the full-call-auction watchlist;
  5. a public IDX investigation;
  6. an OJK sanction or court conviction.

  UMA notices and suspensions are themselves outputs of IDX's surveillance rules. If the detector is tuned on them, evaluating against them becomes circular. They are reported separately and never used for tuning.
- **The rules changed under the data.** IDX's daily price limits (ARA/ARB) changed at least ten times between 2015 and 2026, and several other things changed too:
  - ARB was 7% from 2020 to 2023 and has been 7% again since 19 Oct 2026.
  - The minimum price fell from Rp50 to Rp1 on 28 Sep 2026, and limits are fixed in rupiah for the lowest price band.
  - The watchlist board has traded by full call auction since 25 Mar 2024.

  A -7% day in 2021 can be a limit-down crash, while in 2018 it is an ordinary move. Every return-based feature is therefore normalised by the limit in force that day, and limit hits are explicit features.
- **The literature agrees on the daily pattern.** Manipulated stocks are small and illiquid. During the scheme they show abnormal return, volume and turnover, often with streaks of limit-up days, and the price reverses afterwards. On IDX, volume predicts abnormal returns over the following days.

## 3. Methodology

### 3.1 Data
- **Canonical daily panel:** one row per (date, ticker). It holds OHLC, volume, value and trade frequency, plus foreign buy and sell, listed shares and tradeable shares, a `source` column and quality flags. A field the source doesn't provide is null, never zero.
- **Survivorship:** the universe includes delisted and suspended stocks. A stock that is missing on a trading day is recorded as missing, which serves as a suspension proxy. It is never forward-filled into a fake price.
- **Corporate actions:** a move larger than the limit in force is flagged as a probable corporate action. Those days are excluded from features; they are not silently adjusted.
- **Rule tables in `data/`:**
  - price-limit regimes for each board, with percentage or fixed-rupiah limits;
  - tick sizes;
  - market-wide halts and structural breaks.

### 3.2 Features (each computed for day D using only data up to the close of D)
1. **Limit-normalised return:** return divided by the limit in force. Plus ARA and ARB hit flags and the length of the current ARA run.
2. **Market-adjusted abnormal return:** compared with the equal-weighted panel or IHSG, over 1, 5 and 20 days.
3. **Abnormal volume, turnover and value:** robust z-scores using median and MAD over the trailing 60 days.
4. **Run-up and reversal:** cumulative return over 5 and 20 days, and the drawdown from the 20-day peak.
5. **Liquidity and size:** Amihud illiquidity, share of zero-volume days, value traded, and a size bucket.
6. **Volatility:** range-based (Parkinson), with limit days marked as censored.
7. **Trade size:** value per trade and frequency z-scores. These need IDX fields and are null when the source lacks them.
8. **Foreign flow:** net foreign buy as a share of value. Optional.

### 3.3 Detectors, in build order. Each must beat the ones before it to stay.
1. **Baselines:** daily rank by limit-normalised return, rank by abnormal volume, and a simple rule that approximates UMA.
2. **Robust z-score composite:** the rule score, calculated within liquidity and size buckets.
3. **Isolation forest:** fitted per bucket on a trailing window, then refitted walk-forward.
4. **PU ranker:** positives are the sanctioned windows; UMA counts as a low-weight positive in a separate experiment. Evaluated leave-one-case-out with an embargo.
5. **Episode builder:** change-point detection merges flagged days into episodes, so the output reads "stock X, episode from date A to date B" instead of 30 separate alerts.
6. **Ensemble:** the average rank of the detectors that survive.

### 3.4 Evaluation
- **Event-level recall@k.** A case window counts as found if the stock enters the daily top-k at least once between `start - lead` and `end`. Use k = 10, 25 and 50. For month- or year-precision windows, the whole month or year range is used.
- **Placebo baseline, which is mandatory.** "Any day in the top-k" is easy to hit by chance on long windows. A random top-20 list out of about 900 stocks hits a 20-day window about 36% of the time, and a 175-day window like PANR's about 98% of the time. Every recall figure must be reported against (a) the same metric on randomly placed placebo windows of matching length, in random stocks of the same liquidity bucket, and (b) a random ranker. Long windows are also scored by the **share of window days in the top-k** and by the **days from window start to the first flag**.
- **Lead time:** days from the first flag to the window start and to the first UMA notice or suspension.
- **Alert burden:** flags per day, and the share of flags on stocks with any weak label.
- **No look-ahead:**
  - a walk-forward protocol;
  - a generic test that recomputes each feature on data truncated at D and checks it matches;
  - an embargo of ±60 days around held-out windows for anything trained.
- **Sanity check:** synthetic pump-and-dump patterns are injected into real or synthetic panels. Detectors must recover them before their results on real cases mean anything.
- **Stratified reporting:** results are shown separately by price-limit regime (2020-2023 ARB 7% versus others) and by board.
- **Success criterion:** a detector is worth keeping only if it beats the best baseline on event recall@25 and on median lead time without a worse alert burden. Results are reported per case, so readers can see which cases are found and which are missed. No accuracy target is set in advance; with this few labels it would be meaningless.

### 3.5 Daily watchlist
After each trading day: refresh the data, compute features, score, and write the top 25 with the features that drove each score. The wording describes statistical anomalies only (see `CLAUDE.md`). The watchlist goes to the private data store, not this public repo, until the owner decides otherwise (Question Q4).

## 4. Data sources and constraints

| Source | Gives | Constraint | Status |
|---|---|---|---|
| IDX `GetStockSummary` (one request = whole market for one day) | Full fields including frequency, foreign flows, non-regular market, listed and tradeable shares | **IDX's terms of use prohibit scraping.** It is behind Cloudflare, blocks cloud IPs, and the scrapers that work impersonate browsers. | **Not used** unless the owner gets permission or picks another route (Q1) |
| Yahoo Finance via `yfinance` (`.JK`) | OHLCV, adjusted close | No frequency or foreign flow; delisted tickers mostly missing; rate limits; personal-use terms | Allowed as a source once its hosts are allowed (Q3) |
| Public bulk datasets (Kaggle "EOD Data Indonesia Stock Exchange"; GitHub `wildangunawan/Dataset-Saham-IDX`, CC BY-NC, about 958 stocks, 2019-2025) | History backfill | Non-commercial licences; coverage to be verified | Candidate (Q1) |
| KSEI / IDX monthly holders above 1% (since Mar 2026) | Ownership concentration | Only from 2026 | Later |
| Paid: IDX data products, ICE, EODHD, Stockbit (broker summary) | Broker-level data, tick history | Cost | Designed as a plug-in, not planned |

**Data storage:** market data is never committed to this public repo, because the source licences forbid redistributing it. It goes to a **private** data store, Parquet files partitioned by month. Until the owner creates one (Q2), every chunk works offline on fixtures and synthetic panels.

**Network:** this environment currently allows only package registries. Fetching data needs specific hosts allowed (Q3). Chunks that need the network are marked `blocked` until then.

## 5. Deliverables

| ID | Deliverable | Done when |
|---|---|---|
| D1 | Label dataset v0.1 | Done (`data/`, `tests/`) |
| D2 | Rule tables v2 (regimes per board with fixed-rupiah limits, tick sizes, halts and breaks) plus label update | Phase 0 done |
| D3 | Data layer: bar schema, Parquet store, source adapters, quality checks | Phase 1 done; at least one real source backfilled 2016-2026 |
| D4 | Feature library with a look-ahead guard | Phase 2 done |
| D5 | Detectors and episode builder | Phase 4 done |
| D6 | Evaluation report: per-case results, baselines, lead time, stratified tables | Phase 5 done, `reports/evaluation.md` |
| D7 | Daily watchlist job | Phase 6 done, running on a schedule |

## 6. Phases and chunks

Chunk specs live in `tasks/<id>.md` and their status in `tasks/BOARD.md`. Phases 0 to 2 can run fully offline. The planner writes specs for later phases when the board runs low (`docs/LOOP.md` step 7). The titles below are the intended breakdown, and the planner may split them further.

**Phase 0: rule tables and labels (offline)**
- P0-01 Regime schema v2: board column, fixed-rupiah limits, `price_limits()` support
- P0-02 Regular-board regimes for Sep to Nov 2026; close the April 2025 regime
- P0-03 Watchlist-board (full call auction) and Acceleration Board regimes
- P0-04 Tick-size table and `tick_size()` / `round_to_tick()`
- P0-05 Market events table: halts, structural breaks, shocks
- P0-06 Label update: `convicted` and `exchange_review` classes; SWAT verdict; NSSS, FUJI and CASA reviews
- P0-07 Task-board consistency test

**Phase 1: data layer**
- P1-01 Canonical bar schema and `validate_bars()` (adds pandas and pyarrow)
- P1-02 Month-partitioned Parquet store: `write_bars()` / `read_bars()`
- P1-03 Source adapter protocol and Yahoo adapter, tested with mocked responses
- P1-04 Generic bulk-CSV importer with column mappings (Kaggle and GitHub dataset formats)
- P1-05 IDX stock-summary JSON parser, from fixtures only. No fetcher until Q1 is answered.
- P1-06 Trading calendar from the panel, and missing-day (suspension proxy) flags
- P1-07 Data-quality report: zero volume, stale prices, gaps, moves beyond the limit
- P1-08 Corporate-action suspect flags
- P1-09 Backfill command: source to store, resumable, rate-limited (needs the network)

**Phase 2: features (offline on synthetic data)**
- P2-00a Synthetic panel generator with injectable pump-and-dump episodes
- P2-00b `assert_no_lookahead()` test helper
- P2-01 Limit-normalised returns, limit-hit flags, ARA run length
- P2-02 Market-adjusted abnormal returns
- P2-03 Robust volume, turnover and value z-scores
- P2-04 Run-up and reversal features
- P2-05 Liquidity and size buckets
- P2-06 Range volatility with censoring flags
- P2-07 Trade-size and foreign-flow features (null-safe)
- P2-08 Feature pipeline assembler, writing a feature table to the store

**Phase 3: labels on the panel**
- P3-01 Ticker-day label panel from windows, with class, precision and confidence filters
- P3-02 ARA-run weak label
- P3-03 Surveillance events schema (UMA, suspension, notation, investigation) and loader
- P3-04 IDX announcement and suspension JSON parsers, from fixtures (fetching depends on Q1)

**Phase 4: detectors**
- P4-01 Baseline rankers
- P4-02 Robust z-score composite per bucket
- P4-03 Isolation forest per bucket, walk-forward (adds scikit-learn)
- P4-04 PU ranker with leave-one-case-out
- P4-05 Episode builder (change point and merging)
- P4-06 Ensemble

**Phase 5: evaluation**
- P5-01 Event-level recall@k, share-of-window-in-top-k and lead-time metrics
- P5-01b Placebo-window and random-ranker baselines
- P5-02 Walk-forward runner with embargo
- P5-03 Synthetic-injection recovery test
- P5-04 Weak-label precision and alert-burden metrics
- P5-05 Evaluation report generator (`reports/evaluation.md`)

**Phase 6: daily watchlist**
- P6-01 `saham-gorengan score --date` CLI
- P6-02 Watchlist writer with explanation and wording rules
- P6-03 Scheduled daily refresh and score (separate scheduled task, after Q2, Q3 and Q4)

## 7. Risks

| Risk | Mitigation |
|---|---|
| No legal, reliable free source with full IDX fields | Source adapters are pluggable and features are null-safe. Evaluate on Yahoo plus bulk datasets, and add IDX or paid data later. |
| Look-ahead leakage inflates results | Generic truncation test on every feature, walk-forward only, and an embargo |
| Weak labels make evaluation circular | UMA and suspensions are never used for tuning, and they're reported separately |
| Defamation risk of naming stocks | The watchlist stays private and its wording is statistical. Only OJK or court findings are called manipulation. |
| The loop pushes broken code | Tests gate every push, one chunk per commit, repair runs, at most 3 chunks per run |
| Research facts are wrong (most came from search snippets, not primary documents) | Rule-table rows carry source URLs and notes. A re-verification chunk runs once idx.co.id and ojk.go.id can be reached. |
