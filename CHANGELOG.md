# Warning Board — Changelog

---

## v0.5 candidate round — 20 August 2026

**Spec hash:** `e011e3d4b9e94e03` (`spec_v05.json`)
**Supersedes:** v0.3 (`a67f4fb8e6b2856d`)
**Board size:** unchanged at 20 indicators

`spec_v05.json` promotes exactly one change (C7), pre-registered in
`spec-v0.5-candidates.md`, written before any backtest ran.

Motivation for the round: the board read 0/20 on 2026-08-19, and it's a
correct, defensible reading — but 2026's labor market is a "low-fire" regime
(payrolls flat, unemployment rate falling only because the labor force is
shrinking) that several Bucket C indicators structurally can't see, credit
stress has migrated into private markets that Bucket A doesn't reach, and
indicator #1's post-inversion memory lapsed in March 2026 while the
historical recession hazard window was still open. Six candidates and one
parameter correction were pre-registered to address specific pieces of that.

### C7 — Yield curve lookback 365→730 days: **ADOPTED**

Indicator #1's `lookback_days` swept at 365 (frozen v0.3 value), 540, and
730. Result: **byte-identical** Watch/Warning lead times and control-window
outcomes at all three values, across the full 1988–2026 backtest. The 53
dates where 365d and 730d disagree cluster into exactly three episodes —
mid-2009, late 2020–2021, and April–August 2026 — and every one is *after*
a recession's onset, never before. Extending the memory only affects how
long the indicator stays lit during and after a stress episode; it never
changes when a fresh inversion first triggers a warning. Per the
pre-registered decision rule (adopt the longest lookback that doesn't
raise 1998/2015-16 or shorten 2001/2007-09), 730 days wins outright with
zero downside anywhere in the backtest.

This closes the gap the round was partly motivated by: indicator #1 read
green as of 2026-08-19 only because its 365-day memory of the March-2026
un-inversion had just expired, not because the curve's signal had changed
character. Under 730 days it reads red again today.

### C4 — Prime-age employment-population ratio (`LNS12300060`): tested, **demoted to WATCHLIST**

The harness's mechanical verdict printed PASS — own-red-before-onset was
2/3 (green in 1990-91, red before both 2001 and 2007-09) and no control
window degraded. **That verdict is overridden here.** ALFRED's vintage
archive for this exact series starts 2014-12-05; every evaluation date
before that falls back to the earliest-vintage approximation (class B).
Pre-1998 integrity came back **100% class B (120/120 evaluation dates)**.
The 1990-91 result -- already the one recession where it read green -- is
not just unconfirmed, it's uninformative: there is no clean vintage
reconstruction of this series before 2014, full stop. That leaves 2 clean,
confirmed recessions (2001, 2007-09) against the project's standing ≥3 bar.
Per spec-v0.5-candidates.md §5 criterion 5 (an era that is predominantly
class B does not count toward the bar) and its own worked example for
this exact shape of result, C4 is demoted to WATCHLIST: displayed,
labeled not-out-of-sample-validated, never scored.

Checked whether the vintage gap could be closed by manual historical
reconstruction (BLS's own archived press releases, back to 1966, exist
as plain text at bls.gov/news.release/history/ -- not scanned images).
Pulled the actual May 1994 release: Table A-1 breaks employment-population
ratio out by sex and by "16-19" vs. "20 and over," with no 25-54 cut
anywhere in it. The statistic wasn't published in that form yet -- there
is no historical document to transcribe from. This is a structural dead
end, not an access problem, and lines up with ALFRED's 2014 vintage start
date: that's roughly when this specific age cut started getting
standalone attention.

### C5 — Deflate #12 (core capital goods orders) by PPI: **FAIL**

Replaces `NEWORDER` (nominal) with `RATIO:NEWORDER/WPSFD41312` (PPI-
deflated), same rule and threshold, closing the same nominal-vs-real
inconsistency that sank C2. **Raised the 2022 rate-shock control window
from WATCH to WARNING** -- a new false positive, disqualifying regardless
of anything else. Deflating changed indicator #12's color on 38% of
either-red months (97 of 464): 36 months red-only-when-deflated against
just 1 red-only-when-nominal, so the real series is substantially more
trigger-happy, and 2022's inflation-driven equipment-order slump is
exactly the kind of month it newly catches. The 2007-09 Watch lead did
genuinely improve (5→7 months) under the real series, but the pre-
registered pass condition was explicitly "closes the inconsistency
without degrading anything," not "improves leads," so a new false
positive fails it outright. Also newly discovered: the PPI deflator leg
(`WPSFD41312`) has its own ALFRED vintage gap (first vintage 2015-03-13),
so even a passing result here couldn't have been vintage-validated
before 2015 -- a limitation the original proposal didn't anticipate,
having assumed "PPI is barely revised" implied negligible vintage risk.
Indicator #12 stays nominal.

### C6 — Aggregate weekly hours, total private (`AWHI`): **FAIL**

Zero red readings in the 24-month pre-onset window for any of the three
recessions (0/3, against the pre-registered ≥2/3 bar) -- CRITERION 3 FAIL,
caught by the harness automatically. It isn't silent, though: it does
fire, just late -- first red 4 months into 1990-91, 7 months into 2001,
8 months into 2007-09. A labor-hoarding regime cuts hours only once a
downturn is already visible, the same lagging-not-leading shape the C2
retry found for realized capex. (Also would have been vintage-limited to
2/3 clean recessions regardless, per the same pre-flight gap as C4's
1990-91 window -- moot given the more fundamental timing failure.)

### C8 — Baa − Aaa corporate quality spread: **FAIL**

Zero red readings in the 24-month pre-onset window for any of the three
recessions (0/3) -- CRITERION 3 FAIL. Fires 4 months into 1990-91, 10
months into 2001 (after that recession had already ended), 2 months into
2007-09. Same lagging pattern as C6: within-corporate credit-quality
migration is a realized, coincident signal, not an anticipatory one. The
pre-registration's predicted rejection reason -- redundancy with #3 --
did not materialize (66% disagreement on either-red months, well clear of
the 25% bar, so this genuinely is a different signal from Baa−10Y). It
just doesn't lead.

### C9 — Hamilton net oil price increase (`WTISPLC`): **FAIL**

Never read red once in the entire 1988–2026 backtest. Not a data problem
and not a rule bug -- the rule-correction unit tests (8/8) and the
pre-registered 2026 expectation both held exactly as designed (green
through the 2026 shock, confirmed). The reason it never fires is
mechanical and instructive: oil rose enormously in cumulative terms
across all three recession windows (+113% into 1990-91, +186% into 2001,
+226% into 2007-09), but every one of those was a gradual, multi-year
climb, not a sudden spike against a flat base. Hamilton's construction
compares today's price to the *rolling max of the trailing 3 years* --
for a steady climb, that ceiling rises right along with the price, so
the price is never 40% above its own recent high, even while being far
above where it started years earlier. The rule is built to catch sharp
discrete shocks (1973/1979-style embargoes); none of the three pre-2020
episodes in this dataset were shaped like that, not even the 1990 Gulf
War spike, which was sharp but apparently didn't hold the 2-month streak.
No energy-shock indicator is added; the gap named in §0 of the
pre-registration stays open.

### Watchlist (W1–W5): added, display-only

`LNFACBW027SBOG` (bank loans to nondepository financial institutions,
the private-credit bridge), `JTSHIR` (JOLTS hires rate), Census data-center
construction spending, `BABATOTALSAUS` (business applications), and BDC
price-to-NAV discount are added to the app as a labeled "Context -- not
part of the scored board, not out-of-sample validated" section per
spec-v0.5-candidates.md §4. None enter `reds`, `available`, or `fraction`.
The BDC non-accrual composite proposal was rejected even as a watchlist
item, for the same reasons C1 was rejected in v0.3: no standard
machine-readable field across filers, survivorship bias runs the wrong
direction, and it would require a permanent manual scraping obligation
the architecture is deliberately built without.

### Current reading (v0.5, i.e. v0.3 + C7 only)

**2026-08-01: 1 of 20 red** (indicator #1, yield curve, under the 730-day
lookback). Every other indicator unchanged from v0.3's 0/20 reading.

---

## Post-v0.3 note — 19 August 2026: C2 retry, tested and rejected again

**Board size:** unchanged at 20 indicators. Spec unchanged; no new spec file.

v0.3's C2 (Technology Investment Reversal) failed because it used a nominal-
dollar series, and the CHANGELOG left the door open: *"A real
(inflation-adjusted) series or a deceleration rule may work, but that
requires fresh pre-registration as a future candidate."* Pre-registered in
`spec-v0.4-candidate-C2-retry.md` and run via `run_c2_retry.py`, changing
exactly one thing — swapping `A679RC1Q027SBEA` (nominal) for
`B679RA3Q086SBEA` (the real, chained-quantity-index counterpart of the same
BEA category), same rule, same thresholds, same acceptance criteria as the
original candidates.

**Verdict: FAIL.** The indicator never read red in the 24 months before any
of the three pre-2020 recessions (0/3, against a pre-registered minimum of
2/3). It did eventually go red both other times it was checked — 1–7 months
into the 2001 recession (first red October 2001, recession ran March–November
2001) and 13 months into 2007-09 (first red January 2009, recession ran
December 2007–June 2009) — which makes this a clean negative result, not a
noisy one: real tech investment cuts show up as a *reaction* to a downturn
already underway, not a warning ahead of one. Fixing the inflation problem
didn't fix the underlying issue — capex is lagging by construction here, not
leading.

**Consequence.** The AI-specific capital spending blind spot named in the
app's Methodology screen remains open. This closes the specific "retry with
real data" thread the v0.3 CHANGELOG left pending; a future attempt would
need a genuinely different mechanism (e.g. financing/credit conditions for
data-center buildouts, rather than realized investment spending, which by
definition can only be measured after the money's already been spent).

---

## v0.3 — 18 August 2026

**Spec hash:** `a67f4fb8e6b2856d` (`spec_v03.json`)
**Supersedes:** v0.2.1 (`8a3d5f7b68c84d5a`)
**Board size:** unchanged at 20 indicators

### Change 1 — Candidate indicators C1–C3: tested, rejected

Three candidates were pre-registered in `spec-v0.3-candidates.md` and `spec-v0.3-candidates-C2-C3.md` and evaluated against their stated acceptance criteria. **None passed. The board is unchanged.**

| Candidate | Verdict | Reason |
|-----------|---------|--------|
| C1 — Business Bankruptcy Filings | not run | US Courts data requires manual assembly; deferred, still pre-registered |
| C2 — Technology Investment Reversal | **FAIL** | Red before onset in 0 of 3 recessions, including 2001 — its designed analog |
| C3 — Small-Firm Lending Standards | **FAIL** | Only 12% disagreement with #6 (redundant); also raised 2022 from Watch to Warning |

**C2 analysis.** A zero-growth YoY rule on nominal information-processing investment proved effectively unreachable: the series did not post two consecutive quarters of YoY contraction even through the dot-com bust, because nominal spending kept rising while unit investment collapsed. This is a threshold design error, not necessarily a failure of the concept. A real (inflation-adjusted) series or a deceleration rule may work, but that requires fresh pre-registration as a future candidate. **It was not retuned and re-run.**

**C3 analysis, and its consequence.** Small-firm and large-firm bank lending standards move together closely enough to be the same light. Adding the correlated measure also manufactured a false Warning in 2022 — the exact correlated-cluster failure predicted when the candidate was proposed.

This settles a question that motivated the candidate: **the private-credit blind spot cannot be narrowed from the borrower side.** Bank lending standards do not segment usefully by firm size. The blind spot is structural.

**Incidental finding.** In the combined run, Bucket-C ignition fired at 2020-06 — inside the pandemic recession, not before it. This further confirms ignition as a coincident confirmation signal rather than a predictor, consistent with the v0.2.1 finding that demoted hypothesis H1 to secondary display.

### Change 2 — Global threshold scale ×0.95

Decision rule pre-registered in `spec-v0.3-threshold-review.md` before the sweep. A single global scale factor was applied to all scalable thresholds — one degree of freedom, testing the single hypothesis that the board was calibrated slightly tight.

**Full sweep (disclosure required by the pre-registration):**

| Scale | 1990 Watch | 2001 Watch | 2007 Watch | Median | Quiet | Worst control | Eligible |
|-------|-----------|-----------|-----------|--------|-------|---------------|----------|
| 0.70 | 25 | 8 | 8 | 8.0 | 64% | WARNING (2022) | no — false Warning, quiet <70% |
| 0.80 | 12 | 8 | 8 | 8.0 | 69% | WARNING (2022) | no — false Warning, quiet <70% |
| 0.85 | 12 | 8 | 8 | 8.0 | 71% | WARNING (2022) | no — false Warning |
| 0.90 | 12 | 6 | 7 | 7.0 | 73% | WARNING (2022) | no — false Warning |
| **0.95** | **12** | **6** | **5** | **6.0** | **74%** | WATCH (2015–16) | **YES — adopted** |
| 1.00 | 12 | 4 | 5 | 5.0 | 75% | WATCH (2015–16) | yes (baseline) |
| 1.05 | 12 | 4 | 5 | 5.0 | 76% | WATCH (2022) | yes |
| 1.10 | 12 | 3 | 5 | 5.0 | 78% | WATCH (2022) | yes |
| 1.20 | 12 | 3 | 4 | 4.0 | 80% | WATCH (2022) | yes |
| 1.30 | 12 | 3 | 2 | 3.0 | 81% | WATCH (2022) | yes |

**Selected:** ×0.95. Median Watch lead 5.0 → 6.0 months; quiet fraction 75% → 74%.

### Limitations of the v0.3 threshold change — recorded, not to be dropped

1. **The board at ×0.95 is CALIBRATED, not out-of-sample validated.** The scale was selected using the same three recessions the board was validated against. **The honest out-of-sample lead times remain the v0.2.1 (×1.00) figures: 12 / 4 / 5 months.** Any public claim about lead time should quote those.
2. **The selected scale is adjacent to a disqualification cliff.** ×0.90 produces a false Warning in 2022. A 5% shift in the loose direction breaks the clean 35-year false-positive record. The margin is thin and should be treated as a known fragility.
3. **The improvement rests on two data points.** 1990's Watch lead is 12 months at every scale tested and therefore carries no discriminating information; 2007 is unchanged at 5 months. The entire median improvement comes from 2001 moving 4 → 6.
4. **The tradeoff curve is monotone and well-behaved** — tighter is quieter with shorter leads, looser is noisier with longer leads, with no discontinuities. This is evidence the instrument responds sensibly to its parameters rather than sitting on a fitted artifact.
5. **This review runs once.** Per the pre-registration, the threshold question is now closed. It does not reopen because a future reading is disappointing.

### Unchanged in v0.3

Indicator membership (20), bucket assignments, persistence rules, alert tier fractions (25/40/60%), bucket gates, yield-curve variant (1b), staleness windows, and the C-ignition definition.

### Current reading

**2026-08-01: 0 of 20 red.** All buckets clear at the adopted scale.

---

## v0.2.1 — 18 August 2026

Plumbing corrections declared before re-run. Staleness windows widened to match real publication lags (monthly data was being discarded at 61 days); indicator #3 substituted BBB (`BAMLC0A4CBBB`) with Baa spread (`BAA10Y`) because FRED serves only ~3 years of ICE BofA history; indicator #2 (HY spread) retained for live use but unavailable in backtest before 2023. No threshold, tier, or persistence rule changed.

**Effect:** corrected lead times were *shorter* than the pre-fix run (2007 Warning 3 → 0 months), because the earlier figures were inflated by small denominators. See `RESULTS-v0.2.1.md`.

---

## v0.2 — 18 August 2026

Pre-registered amendment responding to specification review. Indicator #14 renamed to Business Loan Delinquencies (dropping the unsupported private-credit claim); yield-curve variants 1a/1b both registered with adjudication rule declared in advance; equity drawdown reclassified as confirmation-role and excluded from sequencing tests; alert tiers converted from fixed counts to fractions of available indicators to make eras comparable; Bucket-C ignition demoted from feature commitment to testable hypothesis H1; data-integrity classes (M/V/B) introduced.

---

## v0.1 — 18 August 2026

Initial specification. 20 indicators in three buckets (Financial/Credit, Business, Household/Labor), fixed thresholds with persistence rules, three alert tiers.
