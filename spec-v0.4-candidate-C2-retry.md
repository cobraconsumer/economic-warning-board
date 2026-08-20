# Candidate retry: C2 "Tech Investment Reversal" — real series

**Pre-registered before running.** Written and committed before the backtest below
is executed, so the acceptance criteria can't be adjusted after seeing the result.

## Why

v0.3's CHANGELOG recorded C2 (Technology Investment Reversal) as **FAIL**, but with
a specific, fixable diagnosis: it used `A679RC1Q027SBEA`, a **nominal**-dollar series.
A zero-growth YoY rule on nominal spending proved unreachable — nominal
information-processing investment kept rising through the dot-com bust because
inflation offset the real slowdown. The CHANGELOG's own words: *"A real
(inflation-adjusted) series or a deceleration rule may work, but that requires
fresh pre-registration as a future candidate. It was not retuned and re-run."*

This is that retry — one change only (nominal → real series), same rule
structure, so the test isolates the one variable the original failure diagnosis
pointed at. Not a chance to also loosen the rule shape at the same time.

## What's changing

| | v0.3 C2 (rejected) | This retry |
|---|---|---|
| Series | `A679RC1Q027SBEA` (nominal $, SAAR) | `B679RA3Q086SBEA` (real chained-quantity index, 2017=100, same BEA category) |
| Rule | `yoy_below_periods`, pct=0.0, periods=4, streak=2 | unchanged |
| Sensitivity | additive ±1.5pp (zero threshold can't scale multiplicatively) | unchanged |
| Bucket / role | B, leading | unchanged |

## Acceptance criteria (identical to the original C2/C3 candidates, pre-registered in v0.3)

1. No new false BROAD (or worse) in the four control windows (1998 LTCM, 2011
   debt ceiling/Europe, 2015–16 industrial recession, 2022 rate shock),
   relative to the 20-indicator baseline.
2. The indicator itself reads red before or at onset in at least 2 of the 3
   pre-2020 recessions (1990-91, 2001, 2007-09).
3. Adding it does not shorten the baseline board's Watch-tier lead for 2001 or 2007-09.
4. Survives the ±1.5pp sensitivity sweep without flipping a control window to BROAD.

**If it fails, it is recorded as tested-and-rejected, same as C1–C3.** No
retuning after seeing the result, and no informal use outside these documented
criteria.
