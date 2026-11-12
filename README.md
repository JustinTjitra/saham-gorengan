# WIP - saham-gorengan

Labelled stock-manipulation cases on the Indonesia Stock Exchange (IDX), taken from OJK enforcement actions from 2016 to November 2026. Also includes the history of the exchange's auto-rejection (ARA/ARB) price limits. The CSVs are plain files you can read directly, and a small Python package (no dependencies) loads them and answers two questions:

- Was ticker X inside a known manipulation window on day D?
- What were the ARA/ARB limits on day D at price P?

## Read this before using it as training data

There are **8 sanctioned cases, 13 windows and 9 distinct tickers**. That works as an evaluation set or for case studies. It is far too small to train a supervised detector. Build your detector unsupervised or rule-based, and use these labels to score it.

One more limitation. Absence from this list does **not** mean a stock was clean. OJK reported 29 manipulation cases between 2022 and February 2026, but only a handful can be named from public sources. The rest were published only as aggregate totals. Treat unlabelled ticker-days as unknown, not as negatives.

## Quick start

```bash
pip install "git+https://github.com/JustinTjitra/saham-gorengan.git"
```

```python
from datetime import date
from saham_gorengan import labels_on, price_limits, load_windows

labels_on("DSSA", date(2025, 1, 2))
# [Window(window_id='DSSA-2024-3', case_id='DSSA-2024', ticker='DSSA', ...)]

labels_on("SWAT", date(2018, 6, 20))                          # [] : alleged cases are off by default
labels_on("SWAT", date(2018, 6, 20), classes={"alleged"})     # [Window(...)]
labels_on("KIOS", date(2021, 6, 1), precisions={"day"})       # [] : KIOS is month-granularity
labels_on("SUPR", date(2022, 3, 1), min_confidence="B")       # [] : SUPR is confidence C

price_limits(date(2021, 1, 4), 150)
# PriceLimits(ara_pct=35, arb_pct=7, regime_id='R2020-ARB7')
```

pandas users can skip the package entirely: `pd.read_csv("data/windows.csv", parse_dates=["start", "end"])`.

## Files

| File | One row per | Use |
|---|---|---|
| `data/windows.csv` | ticker manipulation window | **The labels.** Join to price data on ticker and date. |
| `data/cases.csv` | enforcement case | Scheme, parties, fines, release numbers, sources. |
| `data/court_named.csv` | ticker named in the Jiwasraya or Asabri cases | Context only. No windows, so don't use it for window-based evaluation. |
| `data/excluded.csv` | sanctioned case that is *not* trading manipulation | So you don't mislabel BREN, CUAN, REAL, PIPA, BOGA and the rest. |
| `data/price_limit_regimes.csv` | (regime, price tier) | ARA/ARB limits by date and price. |
| `docs/research/` | | The original research report, unchanged, as the provenance record. |

### `windows.csv`

| Column | Meaning |
|---|---|
| `window_id` | Unique id, e.g. `DSSA-2024-2`. |
| `case_id` | Foreign key into `cases.csv`. One case can cover several tickers (BVN covers AYLS, FILM, BSML), and one ticker can appear in several cases (FILM is in BVN-2021 and FILM-2023). |
| `start`, `end` | Calendar dates, **both inclusive**. Windows can start or end on non-trading days. |
| `precision` | `day`: OJK gave exact dates. `month`: only months were stated, stored as first to last day of the month. `year`: only years were stated. |
| `label_class` | `sanctioned`: administrative sanction issued. `alleged`: criminal track with no verdict yet (SWAT, BEBS). |
| `confidence` | See below. |

### Confidence tiers

- **A**: confirmed in an OJK primary source (press release or RDK statement).
- **B**: consistent across several news outlets quoting an OJK document that could not be opened directly.
- **C**: a single outlet or a low-tier aggregator.

DSSA's case is A, but its three windows are B, because the exact dates come from news coverage of OJK's 31 October 2026 sanction list.

### `price_limit_regimes.csv`

A tier applies when `price_gt < reference_price <= price_lte`. A blank `price_lte` means no upper bound. `effective_from` and `effective_to` are inclusive. The reference price is the one the limit is measured from, normally the previous close.

| Regime | In force | ARA (Rp50-200 / >200-5,000 / >5,000) | ARB |
|---|---|---|---|
| R2015-ASYM | 2015-08-24 to 2017-01-02 | 35 / 25 / 20 | 10 |
| R2017-SYM | 2017-01-03 to 2020-03-09 | 35 / 25 / 20 | same as ARA |
| R2020-ARB10 | 2020-03-10 to 2020-03-12 | 35 / 25 / 20 | 10 |
| R2020-ARB7 | 2020-03-13 to 2023-06-04 | 35 / 25 / 20 | 7 |
| R2023-ARB15 | 2023-06-05 to 2023-09-03 | 35 / 25 / 20 | 15 |
| R2023-SYM | 2023-09-04 to 2025-04-07 | 35 / 25 / 20 | same as ARA |
| R2025-ARB15 | 2025-04-08 onward | 35 / 25 / 20 | 15 |

Why this matters for a detector: return-based features aren't comparable across regimes. With a 7% ARB (2020 to 2023), a crash that would have been one -25% day shows up as several -7% days. Condition on `regime_id`, or normalise each return by the limit in force that day.

**Limitations of the regime table:**
- **Main and development boards only.** The Acceleration Board and full-call-auction watchlist stocks have different limits. They aren't in the source, so `price_limits()` gives the wrong answer for those stocks.
- **The last regime is open-ended because nothing in the source shows it ending.** The research did not confirm that the April 2025 limits are still in force today.
- **IPO-day limits and trading-halt thresholds aren't modelled.** They appear only in `notes`.

## Where this dataset deviates from the report

The report in `docs/research/` contradicts itself in a few places. The CSVs follow the reading below:

1. **Label count.** The report's intro says "10 manipulation labels", but its table has 12 rows. The dataset has 10 cases: 8 sanctioned and 2 alleged. Those 10 cases expand to 15 windows, because some tickers and cases have more than one window.
2. **Recommendations section.** The report says to "use rows 1, 2 and 6-10 as positive labels with exact dates" and to treat KIOS and IMPC as month-granularity. But IMPC is row 6, and KIOS is row 4. The dataset uses the `precision` column instead: KIOS and IMPC are `month`, BEBS is `year`, and everything else is `day`.
3. **Number of regime changes.** The report says the ARA/ARB regime changed "five times between 2016 and April 2025", but its own table shows six changes after the 2015 baseline. The dataset has seven regimes.
4. **BEBS window.** The stated window is 2020 to 2022, but BEBS listed on 2021-03-10. The window starts at the IPO date, because there was no regular-market trading before it.
5. **DSSA period.** OJK's SP 193 text says 2024 to 2026, and some press coverage says 2023 to 2026. The dataset uses the three exact windows from the sanction list.
6. **Jiwasraya tickers.** The source the report cites for the AGO's list of 13 stocks has a headline about 13 *corporate suspects* (investment managers). Those tickers are confidence C until the attribution is checked.

## Known gaps

- Ticker identities for roughly 24 to 26 of OJK's 29 cases from 2022 to February 2026. The best route to them is an e-PPID information request to OJK.
- Release numbers for SHID, KIOS, FILM-2023 and SUPR.
- The violation type in the IPPE and TDPM sanctions.
- The full Asabri stock list.
- The mapping of KIOS, FILM-2023 and SUPR onto the Rp15.9bn figure in the 2026-04-06 RDK release. It was inferred by matching totals, not stated by OJK.

## Names

Individuals appear only by initials or party type, following OJK's own practice. Companies appear by name because OJK's releases name them.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e ".[test]"
```

```bash
.venv/bin/pytest
```

The tests cover the data as well as the code: unique ids, valid tickers, every window joining to its case, ordered dates, whole-month spans for month-precision windows, no overlap between excluded tickers and labels, contiguous regimes, and full price-tier coverage. When you add a case, add its windows too and run the tests.

## Licence

Code: MIT (`LICENSE`). Data in `data/`: CC BY 4.0 (`LICENSE-DATA`). The underlying facts come from public OJK releases, court rulings and news reports, which are cited row by row.
