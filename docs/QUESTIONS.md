# Questions for the owner

The agent loop writes here when it needs a decision, a credential or a network host that only the owner can provide. To answer, write under `Answer:` and push (editing on GitHub is fine). The next run picks it up.

## Open

### Q3. Allow the data hosts in the loop's environment
Once Q1 is decided, the environment needs the source's hosts allowed. For Yahoo: `query1.finance.yahoo.com`, `query2.finance.yahoo.com`, `fc.yahoo.com`, `guce.yahoo.com`. For Kaggle: `www.kaggle.com`, plus its download host and an API key. For re-verifying rule tables: `www.idx.co.id`, `www.ojk.go.id` (reading pages only, no scraping of data endpoints). This is a settings change you approve.

Answer:

### Q4. Should the daily watchlist ever be public?
Publishing named "suspicious" stocks every day has defamation risk in Indonesia. Recommended: keep it in the private data store, and publish only the aggregate evaluation report.

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

