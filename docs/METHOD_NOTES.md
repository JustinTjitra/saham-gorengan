# Method notes, in plain language

Five questions about how this project works, answered without jargon where possible. Written for anyone who has to explain the project out loud, the owner first.

**What has and has not been done.** The label set and the price-limit history are finished. The features, detectors and evaluation are built and tested, but only on synthetic price panels. No detector has been scored against the real labelled cases yet, because no real market data has been loaded. There is no result to quote.

## 1. Why are unlabelled ticker-days "unknown" and not negatives?

The labels come from cases the regulator (OJK) published with enough detail to name a stock and a period: 13 cases, 18 windows. OJK itself reported about 29 to 32 manipulation cases between 2022 and February 2026, and most of those were published only as totals. Manipulation that was never caught is not in any list at all. So a stock-day with no label means "nobody has told us", not "this was clean".

What that does to the numbers:
- **Precision cannot be measured.** If the detector flags a stock with no label, that may be a false alarm or a real case nobody named. Counting it as wrong would understate precision by an unknown amount.
- **Recall on the known cases can be measured**: of the labelled windows, how many did the detector flag?
- This is why the project reports recall on labelled windows, plus the alert burden (how many flags a day), and never an accuracy or precision figure. It is also why the supervised detector is a positive-unlabelled (PU) ranker: it treats labels as "known positives" against "everything else, mixed", not as positives against negatives.

## 2. Why must returns be divided by the price limit in force?

IDX caps how far a stock may move in a day (auto-rejection: ARA up, ARB down). The cap has changed many times and depends on the price tier. The same percentage move therefore means different things on different dates.

Worked example, a stock with a previous close of Rp1,000 that falls 7% in a day:
- **1 June 2021** (regime R2020-ARB7): the lower limit was 7%. A 7% fall is the largest fall the exchange allowed. Normalised return = -7% / 7% = **-1.0**, a limit-down day.
- **3 June 2024** (regime R2023-SYM): the lower limit at that price was 25%. The same 7% fall is an ordinary bad day. Normalised return = -7% / 25% = **-0.28**.

A detector that looks at raw returns would treat those two days as equal. It would also see almost no "large falls" in 2020 to 2023 simply because large falls were not allowed, and would read a quiet period where there was a queue of sellers stuck at the limit. Dividing by the limit puts every day on the same scale: 1.0 always means "hit the cap". The cap also depends on price tier: on the same day in 2024 the upper limit was 35% for a Rp100 stock and 20% for a Rp6,000 stock.

## 3. What does leave-one-case-out with an embargo protect against?

It only matters for a model that learns from the labels (the PU ranker). With 14 usable windows, there is no room for a normal train/test split.

- **Leave-one-case-out:** train on all labelled cases except one, then ask whether the model flags the one it never saw. Repeat for each case. This protects against the model simply memorising the cases it is then scored on.
- **Embargo:** the features on any day are built from the previous 20 to 60 trading days, so days just before and after the held-out window carry information about it. The embargo removes every day within 60 trading days of the held-out window from training. Without it, the model would be trained on days whose features already contain the held-out pump.

What it does not protect against: the model is trained on cases from later years to score a case from an earlier year. That is acceptable for asking "do known cases share a pattern?", and it is not a claim that the model would have worked in real time.

## 4. What is a placebo window, and what does the random ranker tell you?

The main score is: did the stock appear in the daily top-k list at least once during its labelled window? That is easy to hit by luck when the window is long. A random list of 20 stocks out of about 900 hits a 20-day window about 36% of the time, and a 175-day window about 98% of the time.

Two checks put a floor under the score:
- **Placebo windows:** for each real window, draw fake windows of the same length, placed at random dates in other stocks of similar liquidity. Score them the same way. If the detector "finds" placebo windows as often as real ones, it is not detecting anything about manipulation.
- **Random ranker:** shuffle the detector's ranks every day and score that. It gives the hit rate that the window lengths alone produce.

A detector is only worth keeping where it clearly beats both. The report prints the three numbers side by side for that reason.

## 5. What does the synthetic injection test show, and what does it not?

Fake pump-and-dump patterns are planted in simulated price series (a run of up days with raised volume, then a fall), and the detectors are asked to find them.

What it shows:
- The pipeline works end to end: features, detectors, ranking and scoring all connect, and a detector can find a pattern that is definitely there.
- Where detection runs out. With an 8-fold volume spike the detectors find 95 to 100% of planted pumps, even at +0.5% a day. At normal volume, pumps of 0.5 to 1% a day are found no more often than by the random ranker (about 0.55 against 0.60). At +2% a day they are found again (0.95). So the detectors depend on volume, and a slow, quiet price ramp is invisible to them. A price-only trend detector was added to close that gap and did not: a 1% daily drift inside 2% daily noise is too weak to stand out among 150 stocks over ten days.

What it does not show:
- That real manipulation looks like the planted pattern. The fake pumps are the author's guess at the shape.
- Anything about performance on real cases. The simulated prices have no price limits, no suspensions and no news. Passing this test is a precondition for trusting a real result, not a result.

## Numbers worth knowing

- 13 cases, 18 windows, 14 tickers, 2016 to 2026. Default evaluation set (sanctioned and convicted only): 14 windows over 10 tickers.
- With 14 windows, one window is 7 percentage points of recall. Recall of 9/14 against 6/14 is not a reliable difference. The sample can show that a detector does no better than chance, or that it finds most cases; it cannot rank two similar detectors.
- 10 regular-board price-limit regimes since 2015, plus the watchlist (full call auction) board from 2024.
