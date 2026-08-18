# Economic Warning Board

A 20-indicator recession watchlist, evaluated daily against free government
data (mostly FRED), published as a static JSON file, and shown in an iOS app.
No server, no database, no accounts, no push infrastructure. Running cost: **$0**.

```
GitHub Action (daily, ~06:00 ET)
  └─ evaluate.py — fetches 20 FRED series, applies spec_v03.json's rules
       └─ writes board.json
            └─ committed to the gh-pages branch
                 └─ served free at https://cobraconsumer.github.io/economic-warning-board/board.json
                      └─ SwiftUI app fetches on launch + background refresh
                           └─ local notification on tier change
```

**Live board:** https://cobraconsumer.github.io/economic-warning-board/board.json

## What this is not

Not a prediction. Not a probability. Not financial advice. Not a
recommendation to buy or sell anything. The app's own Methodology screen
carries the full disclaimer, the tiers, the honest out-of-sample lead times,
and the three named blind spots — stated in the app itself, not just here.

## Repo layout

- **`spec_v03.json`** — the frozen, hash-pinned rule spec (v0.3). Never edited
  in place; changes land as a new spec file plus a `CHANGELOG.md` entry.
- **`CHANGELOG.md`** — what changed at each spec revision and why.
- **`backtest.py`** — the point-in-time (ALFRED-vintage) research harness that
  validated the rules against 1988–present. See [`docs/BACKTEST.md`](docs/BACKTEST.md)
  for how to run it. Frozen; not used in production.
- **`evaluate.py`** — the live evaluator. Imports `evaluate()` / `is_stale()` /
  `score_board()` from `backtest.py` unmodified and swaps the ALFRED
  point-in-time lookup for a plain "latest observations" fetch, since a daily
  live board only ever needs today's reading. Verified to reproduce the
  backtest's most recent recorded reading exactly before this was trusted.
- **`scripts/seed_history.py`** — turns `results_v03/scored_v03.csv` (the
  frozen v0.3 backtest) into `history_seed.json`, the static monthly history
  `board.json` ships with. The live evaluator appends to it daily.
- **`results/`, `results_v021/`, `results_v03/`** — backtest output for each
  spec revision: lead-time reports, sensitivity sweeps, coverage tables.
- **`.github/workflows/daily-board.yml`** — the daily cron + manual-dispatch
  Action. Refuses to publish a partial board on failure; the previous
  `board.json` stays live.
- **`ios/EconomicWarningBoard/`** — the SwiftUI app (iOS 17+, no third-party
  dependencies). Open `EconomicWarningBoard.xcodeproj` in Xcode to build. The
  project is generated with [XcodeGen](https://github.com/yonaskolb/XcodeGen)
  from `project.yml` — run `xcodegen generate` there after changing it.

## `board.json` schema

See `spec_v03.json`'s `indicators` array for the rules themselves, and
`evaluate.py`'s `WHAT_IS_THIS` / `threshold_text` / `why_text` for how each
reading is turned into plain English. Every indicator's `why_text` explains
*why* it's green as much as why it would be red — that's the
anti-confirmation-bias feature the whole app is built around.

## Local development

```bash
python3 -m venv venv && source venv/bin/activate
pip install requests pandas numpy
export FRED_API_KEY=your_key_here   # free: https://fred.stlouisfed.org/docs/api/api_key.html
python3 evaluate.py --spec spec_v03.json --out board.json --history-seed history_seed.json
```
