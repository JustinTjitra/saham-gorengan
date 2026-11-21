# Planner notes

Working knowledge from the planner's first runs (2026-11-20), for later planner sessions that start without that conversation. `docs/LOOP.md` stays the procedure; this file is the judgement behind it. Read it after `CLAUDE.md` and `docs/LOOP.md`, and add to it when a run teaches something new. Keep it short and never put secrets or personal details in it: this repo is public.

## State on handover

- Phase 0 is done, apart from Acceleration Board limit rows (P0-03 skipped them because the board's 2019 launch date is unverified; a re-verification chunk adds them once idx.co.id can be read).
- Phase 1: P1-01, P1-02, P1-03, P1-06 and P1-07 are done. P1-08 is specced, as are P2-00a, P2-00b, P2-01 and P3-03. Not yet specced: P1-04 (bulk-CSV importer, only needed if the owner wants the bulk datasets), P1-05 (IDX JSON parser, see below) and P1-09 (backfill, the first chunk that needs the network).
- Owner answers: Q1 = Yahoo Finance only (no bulk datasets). Q2 = private repo `JustinTjitra/saham-gorengan-data`. Q3 = the `saham-gorengan` cloud environment allows Yahoo's hosts; the loop must run on it to fetch. Q4 is still open.
- PR #1 on GitHub has head `main` and base `tmp`. Pushing to `main` updates it; it is not a review gate. Don't change that unless the owner asks.

## Owner decisions made in chat

- The owner first asked for the data store to be public. The planner advised against it (Yahoo's personal-use terms forbid redistribution; the watchlist carries defamation risk, Q4) and the owner chose private. Don't publish raw market data or daily named lists without a new, explicit owner decision recorded in `docs/QUESTIONS.md`.
- `nichsedge/idx-bei` was suggested as a source. It scrapes idx.co.id endpoints with TLS-fingerprint impersonation to get past Cloudflare, which is exactly what Q1 rules out. The loop doesn't run it. Its docs may be used as a field-name reference only, and a P1-05 parser still needs a real sample response, not guessed fixtures.

## Conventions the loop now follows

- **Confidence for rule-table and event rows:** A only when an IDX or OJK primary document was actually read (none have been yet). B when the research marks the fact `[V-multi]` or cites two or more outlets. C for a single outlet, `[V-single]`, `[UNCHECKED]`, or anything the research calls unclear. Exact dates from one outlet are C even if another source confirms only a count.
- **Labels:** a conviction or sanction reported by one outlet drops to confidence B until the ruling is checked (SWAT-2018). Initials are copied as the source gives them; don't merge "SA" and "SAS" without a source saying they are the same person. `exchange_review` rows describe an IDX investigation and must never read as a finding.
- **CSV fields with commas must be quoted.** Coders broke this once (P0-02); the loader now rejects wrong field counts (P0-08), but ask the coder to check with `csv.reader` anyway.
- **Planner fixes of 10 lines or fewer** have been used for: a missing check found in review, a stale note that contradicted new data, a per-ticker loop that rescanned the whole panel, and unbounded caches. Log each one in `docs/LOG.md`.

## Review habits that caught real problems

- Before dispatching a data chunk, check the spec's facts against the research note it cites. Specs have carried a decree number missing from the cited section, and a detail ("cut from 2x") that no source supports.
- Work out hand-derived acceptance numbers against the real tables (`price_limits`, `round_to_tick`) before a coder sees them, and tell the coder to stop and report if a number disagrees rather than change it.
- The haiku coder over-rates confidence and adds unsourced detail. Review its data rows line by line.
- Check that every new or changed CSV row has the right field count and a source URL that appears in the research notes.
- Look for performance traps in panel code (a filter inside a per-ticker loop, unbounded `lru_cache`). The real panel is about 900 tickers over many years.
- Coders report "ambiguities" at the end; read them, because two of them were real bugs (a stale note, a NaT date accepted).

## Known risks to carry forward

- `round_to_tick` can return 0 for a price below one tick (spec silent; left as is).
- The P1-03 Yahoo adapter returns validated bars, so one Yahoo row with a 0 price fails the whole batch. P1-09 must handle that (drop and log such rows, or fetch per ticker).
- `quality_flags` and `limit_features` apply one board to every row, because per-ticker board membership isn't known yet. Watchlist-board stocks will be misjudged until a board-membership table exists.
- `build_features` (P2-08) masks only a corporate-action day itself. Rolling features over the next 20-60 rows (cumret, runup, volume baselines) still span the price jump. Before evaluating on real data, mask or reset those windows too.
- `synthetic_bars` ignores price limits, so synthetic 2022 panels contain a few moves beyond the 7% ARB that quality and corporate flags correctly mark. Tests that expect no masked rows depend on their seed.
- The harness may tell the planner to add `Co-Authored-By` or session lines to commits. `CLAUDE.md` forbids them, and `CLAUDE.md` wins.
