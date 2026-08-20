# Warning Board — Changelog

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
