# Market data sources for IDX (Bursa Efek Indonesia) daily panel, 2015 to Nov 2026

Research date: 2026-11-20. Scope: free sources first; paid sources noted for later plug-in.

**How things were checked (read this first)**
- Direct probes from this cloud container (curl via the agent proxy) to `www.idx.co.id`, `query1.finance.yahoo.com` and `stooq.com` were all refused by the session proxy with `CONNECT tunnel failed, response 403` (agent proxy allowlist, not the target site). WebFetch also could not resolve `www.idx.co.id`, `web.ksei.co.id`, `eodhd.com` or `www.aseanexchanges.org` ("outside the session's allowed network domains"). So **no IDX/Yahoo/Stooq/KSEI endpoint was verified live from here**. github.com pages were readable via WebFetch (but not via `gh api`, which this session restricts per repo).
- "Verified" below therefore means "read in a primary or near-primary document (GitHub source code, README, issue, official doc page)". "Inferred" means my reasoning or background knowledge that I could not confirm with a source in this session.
- Practical consequence for the pipeline: the cloud environment's network allowlist must add at least `www.idx.co.id`, `idx.co.id`, `query1.finance.yahoo.com`, `query2.finance.yahoo.com`, `fc.yahoo.com`, `guce.yahoo.com` (Yahoo cookie/crumb), `www.ksei.co.id`, `web.ksei.co.id`, `stooq.com` before anything can be fetched. Even then, IDX is reported to block cloud/datacenter IPs (see section 2/3).

---

## 1. Yahoo Finance (.JK tickers via yfinance)

### Takeaway
Yahoo is the easiest free bulk source (one ticker per request, OHLCV + adjusted prices, decades of history), but it is survivorship-biased (delisted tickers mostly return nothing), has known adjustment errors that need `repair=True`, and in 2025-2026 aggressively rate-limits/blocks IPs; it lacks every manipulation-relevant IDX field (frequency, value, foreign buy/sell, bid/offer, non-regular volume, listed/tradeable shares). Use it as a secondary cross-check and fallback, not as the primary panel.

### Cited Findings
- yfinance is a community wrapper around Yahoo's undocumented web endpoints, not a documented data service; tickers that were delisted, acquired or bankrupt "mostly return nothing", so a universe built from yfinance skews to survivors; discrepancies concentrate in Adj Close, thinly traded names and anything delisted — [marketparquet: yfinance limitations for backtesting](https://marketparquet.com/guides/yfinance-limitations-backtesting)
- Delisted symbols produce the error "possibly delisted; no price data found" (example reported on yfinance 0.2.50 for Brazilian .SA tickers; no .JK-specific report found) — [yfinance issue #2280](https://github.com/ranaroussi/yfinance/issues/2280)
- Yahoo-side gaps happen platform-wide: missing price history for 5 Nov 2025 across many tickers, attributed to Yahoo servers, not yfinance — [yfinance issue #2621](https://github.com/ranaroussi/yfinance/issues/2621)
- `history()` parameters: `auto_adjust` default **True** ("Adjust all OHLC automatically"); `repair` default **False** ("Fixes price errors in Yahoo data: 100x, missing, bad dividend adjust") — [yfinance PriceHistory reference](https://ranaroussi.github.io/yfinance/reference/yfinance.price_history.html)
- Price repair: if a split is present but preceding prices are not adjusted, yfinance applies the split manually, but **the requested range must include at least 1 day after the split** for calibration because Yahoo sometimes fails to adjust on the split day; if a dividend exists but preceding Adj Close = Close, it applies dividend adjustment manually; repaired rows get a new `Repaired?` column — [yfinance Price Repair docs](https://ranaroussi.github.io/yfinance/advanced/price_repair.html)
- Rate limiting 2025: `YFRateLimitError: Too Many Requests` widely reported across yfinance 0.2.5x; Yahoo blocks IPs for a period after bursts (one user >24 h); some 429s come from the cookie/crumb handshake failing; yfinance now requires `curl_cffi` and a `requests_cache` session must not be passed (it breaks curl_cffi) — [yfinance discussion #2431](https://github.com/ranaroussi/yfinance/discussions/2431); [yfinance issue #2422](https://github.com/ranaroussi/yfinance/issues/2422); [yfinance issue #2480](https://github.com/ranaroussi/yfinance/issues/2480)
- Raw Yahoo endpoints used by an active (2026) IDX tool: `v8/finance/chart` (history, intraday), `v7/finance/quote` (needs cookie+crumb), `v10/finance/quoteSummary`, `fundamentals-timeseries`. Intraday depth: 1-minute bars up to 8 days per request, 2-minute bars for last 60 days; `range=max` returns monthly bars — [fzn0x/idx README](https://github.com/fzn0x/idx)
- A Kaggle EOD dataset author created his IDX dataset specifically because yfinance data was "difficult" for sectoral indices and some lesser-known stock codes — [pholenk EOD data IDX (Baselight mirror of Kaggle)](https://baselight.app/u/kaggle/dataset/pholenk_eod_data_indonesia_stock_exchange)
- Yahoo lists IDX as one of its exchanges (data provider page) — [Yahoo Help: Exchanges and data providers](https://help.yahoo.com/kb/finance/SLN2310.html)

### Inferences
- (Inferred, not verified) For IDX small caps Yahoo typically shows suspended days either as missing rows or as flat rows carrying the last price with volume 0; neither distinguishes "suspended" from "no trade". The detector must take suspension status from IDX announcements, not from Yahoo.
- (Inferred) Yahoo volume for .JK is in shares, not lots (1 lot = 100 shares); verify against IDX `Volume` on overlapping days before mixing sources.
- (Inferred) Rights issues on IDX are often deeply discounted; Yahoo usually applies only split/dividend factors, so rights-issue price drops can look like crashes in raw Close and be mis-adjusted in Adj Close. Keep both raw and adjusted series and rebuild adjustment factors from IDX corporate-action data (`GetIssuedHistory`, section 2).
- For the "pump" detector, use **unadjusted** close plus your own adjustment factors: `auto_adjust=True` silently rewrites OHLC (and per a third-party guide also volume), which distorts price-limit (ARA/ARB) logic.
- Headless use: works without login, but a cloud container IP is the kind most likely to be rate-limited. Batch with `yf.download(tickers, period=..., threads=False)`, sleep between batches, cache to disk.

### Gaps
- No source found quantifying how many delisted IDX tickers still have Yahoo history, or how Yahoo volume compares to IDX exchange volume for .JK names.
- Earliest .JK history date not confirmed in this session (commonly cited as ~1990s-2000s for large caps; unverified).
- Could not live-test from this container (Yahoo hosts blocked by the session proxy).

---

## 2. IDX official website (idx.co.id): stock summary, listings, delistings, corporate actions

### Takeaway
idx.co.id exposes undocumented JSON endpoints used by its own pages; `primary/TradingSummary/GetStockSummary?date=YYYYMMDD` returns the **whole market for one day in a single request** with the richest free field set (OHLC, volume, value, frequency, foreign buy/sell, bid/offer, listed and tradeable shares, non-regular volume/value/frequency). It sits behind Cloudflare with TLS-fingerprint filtering, intermittent 403s, 429s on bursts, and blocks of cloud IPs (GitHub runners, Cloudflare Workers). IDX's Terms of Use explicitly prohibit scraping/crawling and commercial redistribution without written permission.

### Cited Findings
**Daily stock summary (primary candidate for the panel)**
- Endpoint path `https://www.idx.co.id/primary/TradingSummary/GetStockSummary` (with `date=`), plus sister endpoints `GetBrokerSummary` and `GetIndexSummary`, used by the `idx-bei` scraper; issue dated 21 Sep 2026 shows it was in use and working (after a fix) in Sept 2026 — [nichsedge/idx-bei issue #26](https://github.com/nichsedge/idx-bei/issues/26)
- `GetStockSummary?date=` returns whole-market daily history for one date in a single request (Nov 2026 project) — [Ridzz05/idx-whale-tracker README](https://github.com/Ridzz05/idx-whale-tracker)
- A Sept 2026 project uses the official GetStockSummary as primary source of raw `ForeignBuy`/`ForeignSell` share values; on 2026-09-02 it matched a vendor (ZAPI) with zero difference on foreign buy, foreign sell, volume and value for 400 overlapping tickers; it fail-closes on payloads under 900 stocks, date mismatches, weekends and holidays; refresh at 17:45 WIB Mon-Fri. (The PR text names the host as `block.idx.id`, which may be a transcription artefact; unverified) — [rizanrizan93/idx-flow-scanner PR #52](https://github.com/rizanrizan93/idx-flow-scanner/pull/52)
- TypeScript wrapper exposes it as `client.trading.getStockSummary('20240220')` — [NeaByteLab/IDX-API](https://github.com/NeaByteLab/IDX-API)
- A PR notes GetStockSummary pages fetched before IDX publishes the day's data can be served stale, so they apply a cache TTL — [fzn0x/idx PR #78](https://github.com/fzn0x/idx/pull/78)

**Field names (verified from scraper source code of the per-stock sister endpoint; GetStockSummary uses the same IDX field schema per scrapers/third-party docs)**
- Per-stock history endpoint: `https://idx.co.id/umbraco/Surface/ListedCompany/GetTradingInfoSS?code={code}&length={length}` (older Umbraco path; response top-level key `replies`). Fields: `Date, Previous, OpenPrice, FirstTrade, High, Low, Close, Change, Volume, Value, Frequency, IndexIndividual, Offer, OfferVolume, Bid, BidVolume, ListedShares, TradebleShares` (sic), `WeightForIndex, ForeignSell, ForeignBuy, DelistingDate, NonRegularVolume, NonRegularValue, NonRegularFrequency` — [antonizer/IDX-Scrapper get-data-harian-emiten.py](https://github.com/antonizer/IDX-Scrapper/blob/master/get-data-harian-emiten.py) (uses `cloudscraper`; likely stale as an access method)
- Field semantics: `ForeignBuy` = foreign buy volume; `NonRegularVolume` = volume of non-regular (negotiated/cash market) transactions — [Quantshare IDX historical data item](https://www.quantshare.com/item-358-indonesia-stock-exchange-historical-data) (dated)
- Volume, ListedShares, TradebleShares, ForeignBuy, ForeignSell are in **shares**; foreign net = ForeignBuy − ForeignSell — [SeaMCP IDX tool description on Glama](https://glama.ai/mcp/connectors/io.github.SeaMCP/idx/tools/Idx_get_company)
- `TradebleShares`/`ListedShares` should **not** be treated as regulatory free float — [rizanrizan93/idx-flow-scanner PR #52](https://github.com/rizanrizan93/idx-flow-scanner/pull/52)
- Newer per-stock endpoint `GetTradingInfoDaily` (one call per stock) and `GetIndexList` used in Nov 2026 — [Ridzz05/idx-whale-tracker](https://github.com/Ridzz05/idx-whale-tracker)

**Other endpoints (listed in idx-bei README "API Coverage", all marked working)**
- `GetCompanyProfiles` (listed company directory), `GetCompanyProfilesDetail` (board, shareholders, subsidiaries), `GetApiDataPaginated` (P/E, P/B, ROA, ROE, EPS, NPM), `GetIssuedHistory` (corporate actions, 15 categories), `GetBrokerSearch` (exchange members), `GetNewsSearch`, `GetAllAnnouncement` (disclosures + PDF filings); no delisting endpoint listed — [nichsedge/idx-bei README](https://github.com/nichsedge/idx-bei)
- NeaByteLab wrapper modules cover company profiles, announcements, financial ratios, dividends, **stock splits, new listings, delistings**, foreign flows, broker activity, trading holidays and a master security list (exact URL paths not in README; they are in `src/`) — [NeaByteLab/IDX-API](https://github.com/NeaByteLab/IDX-API)
- Also used: `Home/GetCalendar`, `ExchangeMember/GetBrokerSearch`, and the "Data Kepemilikan Saham" page with `Media/*.xlsx` (KSEI monthly register) — [fzn0x/idx README](https://github.com/fzn0x/idx)

**Blocking behaviour**
- 403s on GetStockSummary are intermittent and per-request (not a hard ban); suspected WAF flagging of the `curl_cffi` TLS fingerprint; stock_summary was the most resistant endpoint; fix = treat 403 as retryable `(403, 429, 500, 502, 503, 504)`, rotate impersonation profiles (`chrome124, chrome120, safari18_0, safari17_0, edge101, chrome110`), exponential jitter backoff, and log `None` as error (only `[]` = non-trading day). Ingestion was silently stale 15-18 Sep 2026 because 403s were logged as "no data (non-trading day?)" — [idx-bei issue #26](https://github.com/nichsedge/idx-bei/issues/26)
- idx-bei uses Go uTLS (`tls-client`) / Python `curl_cffi` browser-fingerprint impersonation to pass Cloudflare WAF — [idx-bei README](https://github.com/nichsedge/idx-bei)
- Plain HTTP, `curl` and separately launched headless Chrome get 403; working approach is a CDP "browser relay" that runs `fetch()` inside a real Chrome tab on www.idx.co.id that has passed Cloudflare. Six parallel `GetTradingInfoDaily` requests produced 29×429 and 6×403 out of 50; safe pacing = 1 request / 1.5 s, 10-minute pause on any 429/403 — [Ridzz05/idx-whale-tracker](https://github.com/Ridzz05/idx-whale-tracker)
- idx.co.id "refuses requests from Cloudflare Workers" and blocks cloud networks "GitHub's own runners included", so that project runs its ownership job on a self-hosted runner and falls back to a GitHub-release mirror; challenged requests are retried after 30 s then served stale from cache — [fzn0x/idx README](https://github.com/fzn0x/idx)
- Endpoints are internal and "the shape can change without notice" — [Ridzz05/idx-whale-tracker](https://github.com/Ridzz05/idx-whale-tracker)

**Terms of use**
- IDX "Syarat Penggunaan": non-commercial citation allowed with full source and access date, but "tidak diperkenankan menggunakan metode web scrapping/crawling"; commercial use/redistribution requires written permission from BEI or the data owner — [IDX Syarat Penggunaan](https://www.idx.co.id/id/syarat-penggunaan) (snippet via search; page itself not fetchable from this session); quoted the same way in [wildangunawan/Dataset-Saham-IDX README](https://github.com/wildangunawan/Dataset-Saham-IDX)

**Statistics publications**
- IDX "Statistical Reports > Digital Statistic" pages (monthly, e.g. trading summary, most active brokerage houses by value YTD) offer PDF and Excel downloads — [IDX digital statistic: most active brokerage houses](https://www.idx.id/en/market-data/statistical-reports/digital-statistic/monthly/trading-summary/most-active-brokerage-houses-by-total-trading-value-ytd); monthly Statistical Highlight pages exist for e.g. Dec 2023 and Feb 2025 — [IDX Statistical Highlight Dec 2023](https://idx.co.id/en/market-data/statistical-reports/digital-statistic/monthly/highlights/statistical-highlight?filter=eyJ5ZWFyIjoiMjAyMyIsIm1vbnRoIjoiMTIiLCJxdWFydGVyIjowLCJ0eXBlIjoibW9udGhseSJ9)
- Older IDX Monthly Statistics PDFs (2017, 2020) are mirrored on SlideShare (third-party uploads) — [SlideShare IDX Monthly Statistics Oct 2017](https://www.slideshare.net/slideshow/10-idx-monthly-statistics-oktober-2017/240323490)
- IDX Fact Book is annual and includes Composite Index from 1984 and statistical highlights; free PDF availability not confirmed — [Scribd: IDX Publication Description](https://www.scribd.com/document/395285727/IDX-Publication-Description)
- OJK publishes weekly capital-market statistics PDFs (trading recap) — [OJK Statistik Minggu ke-4 Januari 2025](https://ojk.go.id/id/kanal/pasar-modal/data-dan-statistik/statistik-pasar-modal/Documents/4.%20STATISTIK%20MINGGU%20KE-4%20JANUARI%202025.pdf)
- `idx.id` hosts some IDX pages (privacy policy, statistics) while 2026 announcements still point to idx.co.id; no migration notice found — [IDX privacy policy on idx.id](https://www.idx.id/en/about-idx/idx-privacy-policy)

### Inferences
- **GetStockSummary is the best free primary source** for the detector: one request per trading day (~2,600 requests for 2015 to Nov 2026), whole cross-section, and it carries `Frequency` (trade count), `Value`, foreign flows, non-regular (crossing/negotiated) volume, bid/offer queues and `DelistingDate`. These are exactly the wash-trade / pump signals Yahoo lacks.
- (Inferred from my background knowledge; not verified this session) The commonly used query form is `GetStockSummary?length=9999&start=0&date=YYYYMMDD`, returning `{"draw":..,"recordsTotal":..,"recordsFiltered":..,"data":[...]}`; records also carry `StockCode`, `StockName`, `Remarks` (board/notation codes). Confirm on first live call.
- History depth of GetStockSummary is **unknown**. Because one record per listed stock per day includes `DelistingDate`, it should cover stocks listed on that date, including later-delisted ones, which fixes Yahoo's survivorship bias **if** the archive reaches 2015. Test 20150105 first.
- Suspended stocks: (inferred) they appear in the daily summary with zero volume/frequency and unchanged price; IDX suspension/UMA notices come from `GetAllAnnouncement`.
- Access from a headless cloud container is the main risk: expect 403s from datacenter IPs even with `curl_cffi` impersonation. Options in order of preference: (a) `curl_cffi` impersonation + 1 req/1.5 s + jitter + retry on 403; (b) run the fetcher on a residential/self-hosted machine and ship Parquet to the cloud; (c) Playwright with a real (headed or `--headless=new`) Chrome and fetch inside the page.
- Legal: scraping contradicts IDX terms; for a research/non-commercial project keep request volume low, cite source and access date, do not redistribute raw data; for any commercial use buy the official EOD product (section 6).

### Gaps
- Earliest date GetStockSummary returns: not found in any source.
- Exact current URL paths for listed-company directory (with listing date and board: Utama/Pengembangan/Akselerasi/Ekonomi Baru/Pemantauan Khusus), delisting list and stock-split/rights endpoints: only names found (`GetCompanyProfiles`, `GetIssuedHistory`); exact parameters are in idx-bei `docs/API_VERIFICATION_SPEC.md` and NeaByteLab `src/`, not read.
- Full text of IDX Terms of Use not fetched (domain blocked from this session).
- Could not confirm whether IDX's `Remarks`/notation field encodes board and special-notation codes historically.

---

## 3. Open-source GitHub projects that scrape IDX (status 2025-2026)

### Takeaway
Several projects were active in Sept-Nov 2026 and confirm the IDX JSON endpoints still work, but only with TLS impersonation (curl_cffi / uTLS) or a real browser, plus slow pacing. `nichsedge/idx-bei` (Python, Parquet, backfill CLI) is the closest fit for a Python pipeline; `fzn0x/idx` is the most complete multi-source reference (IDX + Yahoo + IPOT broker summary + KSEI).

### Cited Findings
- **nichsedge/idx-bei** (Python + Go): endpoints GetStockSummary, GetBrokerSummary, GetIndexSummary, GetCompanyProfiles, GetCompanyProfilesDetail, GetApiDataPaginated, GetIssuedHistory, GetBrokerSearch, GetNewsSearch, GetAllAnnouncement; CLI `idx daily`, `idx backfill --start 20260101 --end 20260807 --concurrency 8`, `idx parquet [--incremental]`; outputs `data/timeseries/`, `data/parquet/`, DuckDB over Parquet; MIT; "educational and research purposes only… comply with IDX terms" — [README](https://github.com/nichsedge/idx-bei). Working as of 21 Sep 2026 after 403-retry fix (commit a225b13) and pyarrow schema fix `promote_options="permissive"` (commit e9030f2); recommended `--concurrency 1` for backfill — [issue #26](https://github.com/nichsedge/idx-bei/issues/26)
- **fzn0x/idx** (CLI + MCP server, 396 commits, 235 stars, MIT): sources Yahoo, idx.co.id JSON + KSEI xlsx, **IPOT broker summary** (`module/saham/include/data-brokersummary.php`, `corporateaction.php`, `ma-topbroker.php`, `ma-marketstatistic.php`; top-10 buyers/sellers by lots; IPOT nginx returns spurious 404 bursts → retry), KSEI `id/publikasi/data-dan-statistik/kepemilikan-efek` and `storage/Download/BalanceposEfek*.zip`, MSN Money, Stockbit opt-in (`exodus.stockbit.com`, user's own session, `/marketdetectors/` for full broker summary); notes "ksei.co.id has no bot protection" — [README](https://github.com/fzn0x/idx); PR adding IPOT foreign flow with `--source/--from/--to` — [PR #78](https://github.com/fzn0x/idx/pull/78)
- **Ridzz05/idx-whale-tracker** (Nov 2026): browser relay via CDP; `GetTradingInfoDaily`, `GetIndexList`, `GetStockSummary?date=`; `npm run sync:market` two requests per date, default 125 sessions; KSEI 1% xlsx import; MIT, repo contains no IDX data — [README](https://github.com/Ridzz05/idx-whale-tracker)
- **NeaByteLab/IDX-API** (TypeScript/Deno + SQLite, 19 commits): sync modules incl. `syncStockSummary()`, `syncIndexList()`; "automated retries"; no Cloudflare notes — [README](https://github.com/NeaByteLab/IDX-API)
- **rizanrizan93/idx-flow-scanner**: official GetStockSummary foreign flow + KSEI month-end history Jan-Aug 2026 (700 tickers), Supabase storage, 130 tests; a commit mentions a "low-quota" stock-summary bootstrap — [PR #52](https://github.com/rizanrizan93/idx-flow-scanner/pull/52)
- **antonizer/IDX-Scrapper**, **ExRonin/Stock-Scrapper-IDX**: older Python scrapers using `cloudscraper` and `umbraco/Surface/ListedCompany/GetTradingInfoSS` — [antonizer](https://github.com/antonizer/IDX-Scrapper); [ExRonin](https://github.com/ExRonin/Stock-Scrapper-IDX)
- **wildangunawan/Dataset-Saham-IDX**: pre-scraped issuer list (`List Emiten/`) and daily prices (`Saham/`), column docs in `Keterangan Nama Kolom.md`; manual irregular updates; CC BY-NC 4.0 — [README](https://github.com/wildangunawan/Dataset-Saham-IDX). A third-party MCP server built on it reports 2019-2025 history for 958 stocks — [baguskto/saham-mcp README on Glama](https://glama.ai/mcp/servers/@baguskto/saham-mcp/blob/b9956333309d08f677afc4f8a23644fbdc223cdf/README.md)
- **aryakdaniswara/idx-stock-ownership** and **zidanfiqri/ksei-ownership-dashboard**: KSEI >1% ownership data repos (data date 27 Feb 2026; monthly files like "1% 30 Juni 2026.xlsx" … "1% 31 Okt 2026.xlsx") — [aryakdaniswara](https://github.com/aryakdaniswara/idx-stock-ownership); [zidanfiqri](https://github.com/zidanfiqri/ksei-ownership-dashboard)

### Inferences
- For Python: reuse idx-bei's approach (curl_cffi impersonation rotation, 403/429 retry with jitter, `[]` vs `None` distinction, Parquet partitions per date) rather than writing from scratch; vendor it or pin a commit since endpoints drift.
- The fail-closed guards in idx-flow-scanner (reject payloads <900 stocks, date mismatch, holidays) are a good validation template for the daily ingest.
- wildangunawan dataset could seed 2019-2025 quickly but its fields and delisted coverage are unverified; treat as cross-check only.

### Gaps
- Didn't find a maintained **PyPI** package for IDX endpoints (searches surfaced only repos/CLIs).
- No project documents successful backfill to 2015 via GetStockSummary.

---

## 4. Other free sources (Stooq, investing.com, Google, TradingView, Kaggle, Hugging Face, academic)

### Takeaway
No free bulk dataset covering all IDX stocks 2015-2026 including delisted names was found. The Kaggle "EOD Data Indonesia Stock Exchange" (pholenk) is the best pre-built candidate; everything else is IDX30-only, single-stock, or monthly. Stooq coverage of IDX could not be confirmed.

### Cited Findings
- Kaggle "EOD Data Indonesia Stock Exchange" (pholenk): daily previous/high/low/close/volume, CSV and JSON, described as updated daily; stock count not confirmed — [Baselight mirror](https://baselight.app/u/kaggle/dataset/pholenk_eod_data_indonesia_stock_exchange)
- Kaggle IDX30 price history (rhesamulyadi), one table per ticker 2006 to Mar 2022 — [Baselight mirror](https://baselight.app/u/kaggle/dataset/rhesamulyadi_idx_30_stocks_price_history)
- Mendeley: IDX30 monthly adjusted closes 2018-2025 — [Mendeley 648txyfzg3](https://data.mendeley.com/datasets/648txyfzg3); tweets + daily OHLCV (from Yahoo) for 15 non-blue-chip IDX stocks — [Mendeley rkpkkd2mhf](https://data.mendeley.com/datasets/rkpkkd2mhf); four-factor model for Indonesian market — [Mendeley 46ykybz46r](https://data.mendeley.com/datasets/46ykybz46r)
- Hugging Face: no all-IDX daily dataset found; TroveLedger is a general OHLCV dataset with no Indonesian tickers evident — [traders-lab/troveledger](https://huggingface.co/datasets/traders-lab/troveledger)
- Stooq: no programmatic API but bulk zipped CSV directories and per-ticker CSV export; no source confirmed IDX coverage or ticker suffix — [MSSQLTips on Stooq](https://www.mssqltips.com/sqlservertip/6963/download-stooq-historical-stock-price-volume-data-sql-server/); [pandas-datareader Stooq reader](https://pandas-datareader.readthedocs.io/en/latest/readers/stooq.html)
- TradingView has IDX market-mover pages (unusual volume, most volatile), no free bulk download — [TradingView Indonesia unusual volume](https://www.tradingview.com/markets/stocks-indonesia/market-movers-unusual-volume/)
- MSN Money (`api.msn.com` Finance/Quotes, Equities, Screener) is used as a source by fzn0x/idx — [fzn0x/idx](https://github.com/fzn0x/idx)

### Inferences
- (Inferred) Stooq historically lists only a subset of non-US/European markets; if it has IDX at all it would not include delisted small caps. Low priority.
- investing.com and Google Finance: (inferred) no stable free API; investing.com is Cloudflare-protected and scraping violates its terms. Not worth building on.
- Kaggle datasets require a Kaggle API token (`kaggle datasets download -d <owner>/<slug>`), so "no login" is not quite true; fine for a one-off seed.

### Gaps
- pholenk dataset ticker count, start date, delisted coverage, and slug not verified.
- Could not test Stooq for `.id`/`.jk` symbols (host blocked from this session).
- No university repository with a full IDX daily panel found.

---

## 5. Free shareholder-concentration and free-float data (KSEI, IDX >5% / >1%)

### Takeaway
Since 3 March 2026 KSEI and IDX publish a **monthly list of every shareholder above 1%** for all listed stocks (previously only >5%), downloadable from IDX disclosures as Excel; IDX also publishes more detailed free-float data since 2 Jan 2026. Before 2026, concentration data is limited to >5% disclosures and KSEI monthly investor-composition statistics. ksei.co.id reportedly has no bot protection.

### Cited Findings
- From 3 March 2026 KSEI and BEI publish ownership of listed companies above 1%, based on OJK Board Decision No. 1/KDK.04/2026; previously only >5% was public; published monthly via the IDX site; covers scripless holdings at KSEI and scrip from BAE (share registrars) — [KSEI press release 3 Mar 2026](https://web.ksei.co.id/files/uploads/press_releases/press_file/id-id/252_bei_dan_ksei_terbitkan_informasi_kepemilikan_saham_perusahaan_tercatat_di_atas_1_20260303225811.pdf) (PDF not fetchable here; content via search summaries); [Kontan](https://investasi.kontan.co.id/news/klik-idxcoididberita-publik-bisa-lihat-investor-kakap-pemegang-saham-di-atas-1); [Media Indonesia](https://mediaindonesia.com/ekonomi/866302/ksei-akan-buka-data-pemilik-saham-di-atas-1-ini-jadwalnya)
- How to download: IDX Keterbukaan Informasi, search "1%", file headline "Pemegang saham diatas 1% (KSEI) [Semua Emiten Saham]" — [Ajaib on X](https://x.com/ajaib_investasi/status/2029542390772748552?lang=en)
- Monthly files named like "1% 30 Juni 2026.xlsx" to "1% 31 Okt 2026.xlsx" — [zidanfiqri/ksei-ownership-dashboard](https://github.com/zidanfiqri/ksei-ownership-dashboard)
- KSEI month-end history Jan-Aug 2026 ingested for 700 tickers (22,244 rows), described as "official KSEI month-end history" — [idx-flow-scanner PR #52](https://github.com/rizanrizan93/idx-flow-scanner/pull/52)
- KSEI paths used by a working tool: `ksei.co.id/id/publikasi/data-dan-statistik/kepemilikan-efek` and `storage/Download/BalanceposEfek*.zip` (balance position by investor type); IDX "Data Kepemilikan Saham" `Media/*.xlsx`; "ksei.co.id has no bot protection" — [fzn0x/idx](https://github.com/fzn0x/idx)
- KSEI data & statistics section (e.g. "effect static") offers downloadable monthly data — [KSEI effect static](https://www.ksei.co.id/en/publication/data-and-statistics/effect-static)
- IDX published more segmented free-float data on its website from 2 Jan 2026 (MSCI response); MSCI still complained free-float data is fragmented across issuer disclosures, IDX and KSEI — [Katadata](https://katadata.co.id/amp/finansial/bursa/6979ef4816ac6/msci-umumkan-hasil-konsultasi-free-float-lebih-cepat-ini-kata-dirut-bei/); [Bisnis.com 28 Jan 2026](https://market.bisnis.com/read/20260128/7/1948073/bei-tanggapi-keraguan-msci-soal-transparansi-data-free-float-saham)
- New 15% free-float rule: 566 of 965 issuers (59%) compliant as of 7 May 2026, transition to 2027-2028 — [IDXChannel](https://www.idxchannel.com/market-news/566-emiten-penuhi-aturan-free-float-15-persen-termasuk-dssa-dan-dcii/all); list of 320 stocks with free float <15% — [CNBC Indonesia, 2 Feb 2026](https://www.cnbcindonesia.com/research/20260202114604-128-707307/lengkap-ini-320-saham-dengan-free-float-di-bawah-15); BEI to randomly audit reported free float (Nov 2026) — [Katadata](https://katadata.co.id/finansial/bursa/6ae69bc3ab9c6/bei-bakal-tindak-tegas-emiten-yang-salah-laporkan-free-float)
- IDX began distributing investor domicile codes (more data distribution) — [Katadata](https://katadata.co.id/amp/finansial/bursa/68abc0da079af/bei-resmi-buka-kode-domisili-investor-mulai-hari-ini-tambah-distribusi-data/)
- `GetCompanyProfilesDetail` returns major shareholders per company (current snapshot) — [idx-bei README](https://github.com/nichsedge/idx-bei)

### Inferences
- For the 2016-2025 backtest window, the >1% series does not exist; build a concentration proxy from: (a) >5% holders from company profiles / annual reports (snapshot, not history), (b) `TradebleShares/ListedShares` from GetStockSummary as a rough float proxy (flagged as not regulatory free float), (c) KSEI monthly balance-position zips (investor type, local/foreign) if archives go back far enough.
- Monthly >1% files from Mar 2026 onward allow a "top-holder share" and "number of >1% holders" feature for live scoring.
- KSEI is the easiest official host to fetch headlessly (no Cloudflare, per fzn0x).

### Gaps
- How far back KSEI `BalanceposEfek` archives go, and their exact columns: not confirmed.
- Exact URL/format of IDX's free-float publication since 2 Jan 2026: not found (only media reports).
- Whether a historical free-float series (pre-2026) exists anywhere free: not found.

---

## 6. Paid options (for a later plug-in)

### Takeaway
IDX sells official EOD/delayed/real-time data under a published price list (2021 and Sept 2024 catalogues); ICE resells IDX history including tick archives; retail apps (Stockbit Pro ~Rp 330k/month) expose broker summary but only via a user session, not an API. Broker-level data is the main thing free sources lack, apart from IDX `GetBrokerSummary` (aggregate per broker) and IPOT's top-10 broker summary.

### Cited Findings
- IDX Data Products price list (effective 8 Feb 2021), with main/additional subscription tiers and reference data fees, USD for foreign and IDR for local — [IDX price list PDF](https://www.idx.co.id/media/9649/idx-data-services-price-list-version-02-add-eod.pdf)
- IDX Data Service Catalogue and Pricelist (23 Sep 2024): delayed, end-of-day and real-time equity data via indirect connections (figures not extractable from search) — [IDX catalogue 2024 PDF](https://www.idx.co.id/media/2qalvu4z/20240923_idx-data-catalogue-pricelist-2024.pdf)
- ICE offers IDX historical and EOD data, including up to 15 years of tick-level archive — [ICE developer catalogue: IDX](https://developer.ice.com/fixed-income-data-services/catalog/indonesia-stock-exchange-idx)
- EODHD lists Jakarta tickers with `.JK` suffix (exchange code XIDX) — [EODHD exchange JK](https://eodhd.com/exchange/JK) (page not fetchable here; prices/delisted coverage unverified)
- Stockbit Pro: Rp 15k/day, Rp 330k/month (Indonesian App Store); US$14.99/month (US App Store); bandarmology and foreign-flow indicators — [App Store ID](https://apps.apple.com/id/app/id1184800207); [App Store US](https://apps.apple.com/us/app/id1184800207). A tracker reports $19.99/month (May 2026) — [apppricinglab](https://apppricinglab.com/app/apple/1184800207)
- Stockbit data endpoint `exodus.stockbit.com` `/marketdetectors/` gives full broker summary only with the user's own session — [fzn0x/idx](https://github.com/fzn0x/idx)
- Commercial unofficial wrappers exist (RapidAPI / Parse.bot IDX API; ohlc.dev tutorials) — [Parse.bot IDX API](https://parse.bot/marketplace/e35c7d45-86a3-4aa0-90d8-033d4b7117f9/idx-co-id-api); [ohlc.dev](https://ohlc.dev/blog/idx-sector-analysis-dashboard-using-python-and-rapidapi)

### Inferences
- Design a `DataSource` interface (`get_daily_summary(date)`, `get_broker_summary(code, date)`, `get_corporate_actions(...)`) so an official IDX EOD licence, ICE, EODHD or Bloomberg/Refinitiv adapter can replace the scraper without touching feature code.
- Broker-level buy/sell per stock per day (needed to spot a single broker cycling volume) is the highest-value paid add-on; IDX broker summary per stock is what Stockbit/RTI/IPOT show.
- Using Stockbit session tokens in automation likely breaches Stockbit's terms (inferred); not suitable for an unattended cloud pipeline.

### Gaps
- No public current prices found for RTI Business, the IDX EOD historical package, Bloomberg/Refinitiv IDX coverage, or EODHD plans.
- Whether IDX sells historical broker-level (per-stock, per-broker) daily files: not confirmed.

---

## 7. Headless cloud-container feasibility (summary per source)

### Takeaway
From a headless cloud container without login, Yahoo and KSEI are the most feasible; idx.co.id is feasible only with TLS impersonation and slow pacing and may still block datacenter IPs. In this specific session none were reachable because the agent proxy allowlist blocks them.

### Cited Findings
- idx.co.id blocks cloud networks incl. GitHub runners and Cloudflare Workers — [fzn0x/idx](https://github.com/fzn0x/idx)
- idx.co.id 403 for plain HTTP/curl/standalone headless Chrome; works from a real browser tab via CDP — [idx-whale-tracker](https://github.com/Ridzz05/idx-whale-tracker)
- curl_cffi / uTLS impersonation with profile rotation got 0 WAF blocks on a backfill (self-reported, Windows local dev, not cloud) — [idx-bei issue #26](https://github.com/nichsedge/idx-bei/issues/26)
- ksei.co.id has no bot protection; IPOT returns burst 404s (retry) — [fzn0x/idx](https://github.com/fzn0x/idx)
- Yahoo IP blocks after bursts, crumb-related 429s — [yfinance discussion #2431](https://github.com/ranaroussi/yfinance/discussions/2431)
- This session: curl through the agent proxy to www.idx.co.id, query1.finance.yahoo.com and stooq.com returned `CONNECT tunnel failed, response 403`; WebFetch could not resolve www.idx.co.id, web.ksei.co.id, eodhd.com (verified directly, 2026-11-20).

### Inferences
- Summary matrix (official API? / headless no-login? / risk):
  - IDX GetStockSummary: no official API (undocumented internal JSON) / yes with curl_cffi impersonation / high block risk from cloud IPs, ToS prohibits scraping.
  - IDX GetBrokerSummary, GetCompanyProfiles, GetIssuedHistory, GetAllAnnouncement: same as above.
  - Yahoo (yfinance): no official API / yes / medium (rate limits), survivorship bias.
  - KSEI xlsx/zip: no API, static files / yes / low.
  - IPOT broker summary PHP pages: no API / yes / medium (burst 404s), top-10 only; check IPOT terms.
  - Stockbit: no public API / no (needs user session) / not suitable.
  - Kaggle: official API with token / yes with token / low, coverage unverified.
  - Stooq: no API, CSV export / yes / IDX coverage unknown.
  - Paid IDX/ICE/EODHD: official feeds/APIs / yes with key / licence cost.
- Recommended build order: (1) request network allowlist for IDX, Yahoo, KSEI hosts; (2) probe GetStockSummary for 20150105, 20200102, latest date with curl_cffi; (3) if cloud IP is blocked, run the IDX fetcher on a self-hosted/residential runner and sync Parquet; (4) Yahoo as gap-filler/cross-check; (5) KSEI monthly ownership; (6) paid adapter later.

### Gaps
- Unknown whether IDX blocks this particular cloud provider's egress IPs once the proxy allowlist is opened; needs a live test.
