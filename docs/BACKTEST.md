# Warning Board Backtest Harness — Setup & Run

Three files: `spec_v02.json` (the frozen spec — record its hash, never edit it mid-experiment), `backtest.py` (the harness), and `spec-v0.2-amendment.md` (the pre-registration document).

## Setup (5 minutes, runs on your MacBook)

```bash
mkdir warning-board && cd warning-board   # put the three files here
python3 -m venv venv && source venv/bin/activate
pip install requests pandas numpy matplotlib
```

Get a free FRED API key at https://fred.stlouisfed.org/docs/api/api_key.html (instant), then:

```bash
export FRED_API_KEY=your_key_here
```

**S&P 500 data (optional but recommended):** FRED only licenses ~10 years of SP500. Download full daily history from Stooq — visit `https://stooq.com/q/d/l/?s=^spx&i=d` (downloads a CSV) — and save it as `spx_daily.csv`. Without it, indicator #7 is simply marked unavailable (pre-registered as acceptable).

## Run

```bash
# Full backtest, both yield-curve variants:
python backtest.py --spec spec_v02.json --sp500-csv spx_daily.csv --out results/

# Add the ±20% threshold sensitivity pass:
python backtest.py --spec spec_v02.json --sp500-csv spx_daily.csv --sensitivity --out results/
```

First run: expect 30–90 minutes — it downloads and caches thousands of vintage snapshots from ALFRED at a polite request rate. Everything caches to `.fred_cache/`, so re-runs (including sensitivity) take a couple of minutes. If it dies mid-run (network hiccup), just re-run; it resumes from cache.

## What comes out (`results/`)

- `report_variant_a.txt` / `report_variant_b.txt` — **the main event.** Lead times for each tier before each recession, false-positive window verdicts, C-ignition (H1) results, and the "what did the board show each quarter" run-up tables for 1990/2001/2007/2020.
- `scored_variant_*.csv` — month-by-month red counts, fractions, tiers, bucket breakdowns. Chartable in anything.
- `fraction_variant_*.png` — red fraction over ~35 years with recession shading. If the concept works, this one picture is your App Store screenshot and your pitch.
- `coverage_by_era.csv` — the authoritative integrity table (M/V/B/missing per indicator per era) that finalizes the amendment doc's estimates.
- `sensitivity_summary.csv` — whether lead times and false-positive verdicts survive thresholds ×0.8 and ×1.2.

## How to read the results (pre-committed, from the amendment)

- **Success:** Warning-tier lead of several months before 2001 and 2007; 1998/2011/2015-16/2022 peak at Watch or Warning but never Broad; C-ignition fires before or at recession onset and never in control windows.
- **2020 showing no warning is fine** — pre-registered as expected.
- **1990 is corroborating only** (thin coverage).
- If results are ugly: that's the experiment working. Document it, then and only then revise thresholds — in a v0.3 with a changelog.

## What I could not verify from here

This sandbox can't reach `api.stlouisfed.org`, so the harness is smoke-tested against synthetic data (all 20 rules, both curve variants, tier logic, ignition logic, availability fractions — all verified) but has **not** touched the live API. Two things may need a small first-run fix: exact ALFRED vintage behavior for the handful of Class-B series, and any FRED series whose units differ from assumed (spreads are assumed in percent, e.g. 5.0 = 500bp — that one is correct). If a series errors, the harness marks it missing rather than crashing.
