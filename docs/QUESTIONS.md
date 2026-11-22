# Questions for the owner

The agent loop writes here when it needs a decision, a credential or a network host that only the owner can provide. To answer, write under `Answer:` and push (editing on GitHub is fine). The next run picks it up.

## Open

### Q3. Allow the data hosts in the loop's environment
Once Q1 is decided, the environment needs the source's hosts allowed. For Yahoo: `query1.finance.yahoo.com`, `query2.finance.yahoo.com`, `fc.yahoo.com`, `guce.yahoo.com`. For Kaggle: `www.kaggle.com`, plus its download host and an API key. For re-verifying rule tables: `www.idx.co.id`, `www.ojk.go.id` (reading pages only, no scraping of data endpoints). This is a settings change you approve.

Status (planner, 2026-11-20): the owner approved a personal cloud environment `saham-gorengan` that allows the four Yahoo hosts, for both repos. The current planner session could not be moved onto it (a session started by another session can't switch environments), so Yahoo is still unreachable from the loop. Remaining decision: run the scheduled loop in fresh sessions on the `saham-gorengan` environment (this matches LOOP.md's "fresh cloud session every 4 hours"). No current chunk needs the network; P1-09 (backfill) will be the first.

Update (planner, 2026-11-20 17:35): a fresh-session scheduled task created from the planner session failed its test run. It started with no repositories attached and could not attach one, so its push was refused (403). A scheduled task created by a session cannot name repositories. The owner needs to create the scheduled task from the claude.ai scheduled-tasks UI, on the `saham-gorengan` environment, with both repos selected (push access). Until then the original task, which wakes the planner session (no Yahoo access), stays in use.

Answer:

### Q4. Should the daily watchlist ever be public?
Publishing named "suspicious" stocks every day has defamation risk in Indonesia. Recommended: keep it in the private data store, and publish only the aggregate evaluation report.

Answer:

### Q5. Where should the ticker universe come from?
The backfill (P1-09) needs the list of IDX tickers to fetch, including stocks that have since delisted. Without the delisted ones, the history is survivorship-biased, and pumped stocks are over-represented among delistings. Yahoo has no listing endpoint. Options:
- (a) **Recommended:** you supply a CSV of tickers with listing and delisting dates (for example, exported from your broker app, or from IDX's public company list, downloaded by hand in a browser). The loop only reads it.
- (b) Current listings only, from a hand-made list. Simple, but biased; delisted pumps are missed.
- (c) Ask IDX in writing for research-use permission (as in Q1), then fetch their list programmatically.
The loop will not scrape idx.co.id (see Q1).

Update (planner, 2026-11-22): P1-10 defines the file format. It is a UTF-8 CSV with header `ticker,listed,delisted,source`: ISO dates, `delisted` empty if the ticker is still listed, and a non-empty `source` (a URL or a note such as `broker export 2026-11`). An Excel "CSV UTF-8" export works. Put it in the private data repo, for example `universe.csv` at its root. Backfill (P1-09 code, already built) and the daily job (P6-03, blocked) are waiting on it.

Answer:

## Resolved

### Q2. Where is the private data store?
Market data can't go in this public repo. Recommended: create a **private** repo, `JustinTjitra/saham-gorengan-data`, and attach it to the loop's environment. The loop writes month-partitioned Parquet there and keeps its history squashable. Alternative: an existing cloud bucket.

Answer: Private repo `JustinTjitra/saham-gorengan-data`, created by the owner and attached to the loop's environment on 2026-11-20 (confirmed private via the GitHub API). The owner first asked for it to be public; the planner advised against that (Yahoo personal-use terms, Q4 risk) and the owner chose private. Recorded by the planner.

### Q1. Which market-data source(s) may the pipeline use?
IDX's own `GetStockSummary` endpoint is the best free source: one request covers the whole market for a day, and it includes trade frequency and foreign flows. But **IDX's terms of use prohibit scraping**. It also blocks cloud IPs, and the scrapers that still work do so by impersonating a browser to get past Cloudflare. The loop will not build bot-protection evasion. Options:
- (a) **Recommended:** Yahoo Finance (via yfinance), plus public bulk datasets for history (the Kaggle IDX EOD dataset and `wildangunawan/Dataset-Saham-IDX`, CC BY-NC) for now. Separately, ask IDX in writing for research-use permission, or price an IDX data product. Cost: no trade-frequency or foreign-flow features until then, and weaker coverage of delisted stocks.
- (b) Owner downloads IDX data from their own machine and drops files into the data store. The loop only parses them.
- (c) Buy a feed (IDX data products, EODHD, others) now.

Answer: Yahoo Finance. (Owner, in chat with the planner, 2026-11-20; recorded by the planner.)

