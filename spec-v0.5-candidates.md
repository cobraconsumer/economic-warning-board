# Spec v0.5 — pre-registered candidate round

**Status:** PRE-REGISTRATION. Written 2026-08-20, **before** any backtest was run.
**Author of this round:** external review (Claude), handed to the repo maintainer.
**Nothing in this document has been tested yet.** Every expectation below is a prediction, recorded so that a later result cannot be retrofitted into a success.

**Spec v0.3 remains frozen.** Nothing here modifies `spec_v03.json`, `evaluate.py`, or the live board until a candidate passes and is explicitly promoted in a v0.5 amendment. The board keeps publishing v0.3 readings throughout.

---

## 0. Why this round exists

The board read 0/20 red, QUIET, on 2026-08-19. Two independent reviews concluded the same three things:

1. The pipeline is correct. 20/20 available, values match FRED vintages, no silent failures. QUIET is what the frozen rules genuinely produce, and it is defensible: layoffs are at a two-year low, public spreads are at historic tights, delinquency transition rates are steady.
2. The board is a **transmission detector**, not an ignition detector. It fires when stress has begun propagating financial → business → household. That is the correct design and should not change.
3. But in the 2026 regime, several indicators have lost *resolution* rather than merely reading green — and a percentage-of-reds framework cannot distinguish "this instrument says conditions are fine" from "this instrument has no range left."

The specific losses of resolution, each of which motivates a candidate below:

- **Bucket C measures separations in an economy that stopped hiring rather than started firing.** July payrolls −23k with 103k of downward revisions, yet the unemployment rate *fell* to 4.1% because the labor force shrank 264,000 in the same month. Participation is down a full point since December; the labor force has been flat ~21 months. Breakeven payroll growth is at or below zero, so the Sahm rule — a first-difference on the unemployment rate — cannot fire even if employment is falling. Continuing claims and initial claims are equally impaired: nobody is being fired.
- **Bucket A measures banks and public bond indices; leverage moved to neither.** Bank credit commitments to PE, BDCs and private-credit vehicles reached $2.6tn as of Q4 2025 (Fed FSR, May 2026), growing 17% y/y. Private credit default rates are reported around 5.8%, "bad PIK" at 6.4% of borrowers versus 2.5% at end-2021. Public IG at ~75bp and HY at ~267bp are partly tight *because* the marginal risky borrower no longer issues into those indices.
- **Indicator #1's 365-day post-inversion memory expired around 22 March 2026** (`days_in_state` = 149 on the 2026-08-19 board). It went green when the clock ran out, not when the curve changed character. Recessions historically arrive 12–24 months after un-inversion.
- **Indicator #12 is a y/y rule on a nominal series**, reading +12.9%, in a year with a ~50% real oil spike and tariff pass-through. This is the same objection that killed candidate C2.
- **No energy channel exists in the spec**, in a year with an actual oil shock (28 Feb 2026 conflict; Chicago Fed scenarios of −81bp to −166bp on 2026 output growth).

---

## 1. Two tiers, and the rule that separates them

The project's standing bar is: **a scoring indicator must be backtestable on ALFRED point-in-time vintages across ≥3 pre-2020 recessions (1990, 2001, 2007–09).** That bar is why C1–C3 failed and why the three named blind spots persist. **It is not lowered in this round.**

Candidates are therefore split:

| Tier | Meaning | Effect on tier calculation |
|---|---|---|
| **SCOREABLE** | Clears the ≥3-recession bar. Eligible for promotion into the scored 20 if it passes acceptance criteria. | Would change `fraction` denominator if promoted. |
| **WATCHLIST** | Fails the bar on history, but is public, free, timely and informative. | **Zero.** Display-only, labelled "not out-of-sample validated," never enters `reds`, `available`, or `fraction`. |

A WATCHLIST item can never be promoted by accumulating more calendar time under the current rules; it becomes scoreable only when it has covered three recessions, which for most of these means a wait of decades. That is the honest cost of the standard and should be stated in-app rather than worked around.

---

## 2. SCOREABLE candidates

### C4 — Prime-age employment-population ratio

| | |
|---|---|
| **FRED** | `LNS12300060` (Employment-Population Ratio, 25–54 yrs) |
| **History** | Jan 1948 – present. Covers 1990, 2001, 2007–09 plus 1970/73/80/81 |
| **Frequency** | Monthly, ~1 week publication lag |
| **Bucket** | C (Household & Labor) |
| **Role** | leading |
| **Rule** | `drop_from_peak_abs` (new; see §6) |
| **Params** | `{"ma": 1, "peak_window": 12, "drop_pp": 0.5, "streak": 2}` |
| **Scalable** | `drop_pp` |
| **Plain English** | Red when the prime-age employment rate is 0.5 percentage points or more below its highest level in the past 12 months, for 2 consecutive months. |
| **Current reading (uncalibrated, for context only)** | 80.4% in July 2026, roughly 0.4pp off its trailing high — i.e. **close but not red** |

**What it detects that the existing 20 do not.** A *level* on a fixed demographic denominator. If firms stop hiring while attrition continues, prime-age employment falls with zero layoffs, zero claims, and no move in the unemployment rate. It is structurally immune to the labor-force-shrinkage arithmetic that has disabled the Sahm rule, to immigration-driven participation swings, and to retirement demographics. It is the same economic content as the JOLTS hiring rate but with 52 more years of history.

**Why not JOLTS hires (`JTSHIR`) instead.** `JTSHIR` begins December 2000; the 2001 recession began that March, so there is no pre-recession baseline for it. That is ~1.5 usable recessions, not three. `JTSHIR` is assigned to WATCHLIST below as a corroborator, not a scorer.

**Known integrity risk — read this before trusting the result.** CPS series are not revised backward in level, but annual population-control and seasonal-factor updates create discontinuities that are *not* backfilled. ALFRED vintage coverage for `LNS12300060` may not extend to 1988. **The harness must report C4's integrity-class breakdown (V / B / M) by era before any lead time is quoted.** If pre-1997 evaluation dates are all class B (earliest-vintage approximation), the 1990 test is contaminated by exactly the lookback bias this project exists to avoid, and C4 must be reported as *2 clean recessions + 1 approximate* — which would put it below the bar and demote it to WATCHLIST. Do not quietly average across integrity classes.

**Pre-registered expectation.** Red before onset in all three of 1990, 2001, 2007–09. Amber-but-not-red today. Highest risk of failure: a false Warning in the 2015–16 control window, when prime-age EPOP was still climbing out of the GFC and made choppy new highs.

---

### C6 — Index of aggregate weekly hours, total private

| | |
|---|---|
| **FRED** | `AWHI` |
| **History** | 1964 – present. Covers 1970/73/80/81/1990/2001/2007–09 |
| **Frequency** | Monthly, ~1 week publication lag |
| **Bucket** | C |
| **Role** | leading |
| **Rule** | `yoy_below` (existing) |
| **Params** | `{"pct": -0.5, "streak": 2}` |
| **Scalable** | `pct` |
| **Plain English** | Red when total hours worked across the private economy are down 0.5% or more year-over-year for 2 consecutive months. |

**What it detects.** The margin employers adjust *before* headcount. In a labor-hoarding regime — which is what "low-fire" actually is — hours are cut first, and hours × employment is the true labor input. Also immune to labor-force size. C4 catches the level; C6 catches the flow. They are deliberately paired.

**Redundancy check required.** Run `bt.redundancy()` for C6 against #13 (temp help), #15 (initial claims) and C4. If C6 and C4 disagree on fewer than 20% of either-red months, promote only one — preferring C4 for its longer history and cleaner immunity to revision.

**Pre-registered expectation.** Red before onset in 1990, 2001 and 2007–09. Meaningful false-positive risk in the 2015–16 industrial recession, when manufacturing hours fell hard without a general recession. If C6 raises 2015–16 above the baseline's worst tier, it fails criterion 1 and is rejected outright — no threshold search to rescue it.

---

### C8 — Baa − Aaa corporate quality spread

| | |
|---|---|
| **FRED** | `BAA` minus `AAA` (derived: `DIFF:BAA-AAA`) |
| **History** | 1919 – present. Unrevised market yields (integrity class M) |
| **Frequency** | Monthly (daily variants exist; monthly matches the existing spread indicators) |
| **Bucket** | A |
| **Role** | leading |
| **Rule** | `level_above` (existing) |
| **Params** | `{"level": 1.20, "streak": 2}` |
| **Scalable** | `level` |
| **Plain English** | Red when the yield gap between medium-grade and high-grade corporate bonds exceeds 1.20 points for 2 straight months. |

**What it detects, and the Bucket A problem it addresses.** Four of Bucket A's seven slots (#2 HY OAS, #3 Baa−10Y, #4 NFCI, #5 STLFSI4) are near-duplicates of a single public-credit-spread factor. `fraction = reds / 20` implies twenty independent votes; Bucket A supplies roughly three independent factors across seven slots. When the spread factor is compressed, four slots go green together and the bucket-distribution gate — which exists to require breadth — is satisfied by correlated silence.

Baa−Aaa is a genuinely different measurement from #3. Indicator #3 is Baa minus the 10-year Treasury, which is contaminated by flight-to-quality: in a stress episode the Treasury leg falls, widening #3 for reasons unrelated to corporate credit quality. Baa−Aaa is a pure within-corporate quality-migration signal with no duration or safe-asset leg.

**This is not a private-credit indicator and must not be described as one in the app.** It measures public-market quality migration. It narrows the redundancy problem; it does not close the private-credit blind spot, which is closed by nothing currently available (§4).

**Mandatory redundancy check.** Run `bt.redundancy(board, 3, C8_id)`. If disagreement on either-red months is under 25%, C8 is redundant with #3 and should be **rejected**, not added. Adding a correlated indicator makes the concentration problem worse, not better — that is precisely how C3 failed.

**Pre-registered expectation.** Red before onset in 2001 and 2007–09 with high confidence; 1990 is the uncertain one. Current reading is expected to be well below 1.20 and green.

---

### C9 — Hamilton net oil price increase

| | |
|---|---|
| **FRED** | `WTISPLC` (spot crude, monthly, 1946–). Unrevised, integrity class M |
| **History** | 1946 – present. Covers every post-war recession |
| **Frequency** | Monthly |
| **Bucket** | B (Business — the transmission is via business costs and investment) |
| **Role** | leading |
| **Rule** | `hamilton_nopi` (new; see §6) |
| **Params** | `{"max_window": 36, "pct": 40.0, "streak": 2}` |
| **Scalable** | `pct` |
| **Plain English** | Red when the oil price is more than 40% above its highest level of the previous three years, for 2 consecutive months. |

**Rule correction, made before any run.** The first draft computed the reference max as `v.shift(1).rolling(36).max()`. Unit tests caught that this makes the 2-month streak near-unsatisfiable: the first month of a shock sets a new high, which then becomes the *second* month's own reference, so NOPI collapses to ~0 exactly when the rule asks for persistence. A sustained jump from $60 to $90–95 evaluated as green. The reference max is therefore lagged by the full streak length — `v.shift(streak).rolling(36).max()` — so every month of the streak is compared against the same pre-shock baseline, which is what "above its 3-year high for 2 straight months" actually means. Eight unit cases now pass, including the pre-registered 2026 case. This correction was made on unit tests against synthetic data, with no backtest run and no historical result visible; correcting a rule at that stage is legitimate, correcting it after seeing a lead time is not.

**What it detects.** The one recession trigger with no representation whatsoever in the current 20. Oil shocks preceded 1973, 1980, 1990 and 2007–09. The board would currently see an oil shock only second-hand, through industrial production and retail sales, with a lag — a lagging read on a leading shock.

**Why this specific formulation.** This is not an invented rule. Hamilton's net oil price increase (1996, 3-year variant 2003) is a published specification with decades of out-of-sample academic scrutiny, and its defining property is that it fires only on *new* highs — deliberately, so that a recovery from a price dip is not mistaken for a shock. Computed on **nominal** WTI, which keeps it in integrity class M and avoids importing CPI revisions. A CPI-deflated variant should be run as a labelled secondary sensitivity only.

**Pre-registered expectation — record this before running.** **C9 is expected to read GREEN throughout the 2026 oil shock.** WTI's trailing 36-month maximum as of February 2026 includes the 2022 highs near $120; a move from ~$60 to $90–110 does not exceed that, so NOPI should be zero. If C9 reads *red* in 2026, that is evidence the 40% threshold is miscalibrated, **not** a success. The 2022 control window is the other place to watch: if C9 raises 2022 above the baseline's worst tier, it fails criterion 1.

C9 therefore would **not** have helped in 2026. It closes a structural gap for future shocks. Adding it on the strength of a shock it correctly ignores would be exactly the retrofitting this process exists to prevent.

---

## 3. Spec corrections — not additions

These change existing indicators rather than adding new ones. They do not alter the denominator, so they are cheaper to test and cheaper to adopt.

### C5 — Deflate indicator #12 (core capital goods orders)

Replace the `NEWORDER` y/y rule with the same rule on **`RATIO:NEWORDER/WPSFD41312`** (PPI, capital equipment, 1947–).

`NEWORDER` is undeflated dollars, and the y/y threshold (−1.9%, ×0.95) was calibrated on 1990/2001 inflation regimes. In 2026 it reads **+12.9% y/y** while, per Pantheon's decomposition, computer and communications equipment ran +61% and *all other equipment fell 17%*, described as "worryingly broad-based." A nominal composite dominated by one credit-financed sector is not measuring business investment breadth.

This is the identical objection that killed candidate C2 — where a nominal series was rejected because "nominal spending never showed sustained contraction even through the dot-com bust." That reasoning applies with equal force to #12, which is a *live scoring indicator*, not a rejected candidate. Leaving it nominal is an internal inconsistency in the methodology.

PPI is barely revised, so the deflator adds negligible vintage risk. **Test both the ×1.00 and ×0.95 threshold scales, and report whether any of the three honest out-of-sample lead times (12 / 4 / 5 months) change.** If nothing changes, the inconsistency has been closed at zero cost, which is still a win.

### C7 — Yield curve lookback variant "1c"

Indicator #1's `params.lookback_days` is 365. Add a third variant alongside the existing 1a/1b adjudication and sweep **365 / 540 / 730**.

The historical signal is not the inversion, it is the inversion *followed by steepening*, with recessions typically arriving 12–24 months after un-inversion. A 365-day window switches the indicator off at roughly the moment the historical hazard peaks — which is what happened on ~22 March 2026.

Zero data cost, same series, full history. **The 1998 and 2015–16 control windows are where a 730-day window would be punished**; those are the tests that matter. Report lead times and control-window outcomes for all three windows in one table so the choice is visible rather than argued.

---

## 4. WATCHLIST — display only, never scored

Each fails the ≥3-recession bar. Each is public, free and timely. In the app these must render in a visually distinct section, labelled **"Context — not part of the scored board, not out-of-sample validated,"** and must not contribute to `reds`, `available`, `fraction`, or any tier.

| ID | Series | Source | History | Recessions | What it adds |
|---|---|---|---|---|---|
| **W1** | `LNFACBW027SBOG` — Loans to Nondepository Financial Institutions, All Commercial Banks | FRED (H.8), weekly, SA, ~$2.00tn | Jan 2015– | 1 | **The best available bridge to private credit.** When private-credit funds draw on bank facilities under stress it appears here, weekly, free, in the same pipeline. Directly complements #6 and #14, which see only banks lending to *operating companies*. |
| **W2** | `JTSHIR` — JOLTS hires rate | FRED, monthly, 3.4% (Jun 2026) | Dec 2000– | ~1.5 | Direct measure of the low-hire regime. 3.4% vs ~3.9–4.0% in 2019 and ~3.1% at the 2010 trough. Corroborates C4/C6 without scoring. |
| **W3** | Census private construction spending, data-center category | Census C30 | ~2014– | 0 | Leads equipment installation by 12–18 months. The least-lagging AI-capex measure that is public and free. |
| **W4** | `BABATOTALSAUS` — business applications | FRED, monthly, 578,926 (Jul 2026) | Jul 2004– | 2 | Timely SMB formation. Note it currently reads *healthy*, which is evidence against the SMB-collapse thesis and should be displayed as such. |
| **W5** | BDC price-to-NAV discount | Computed from prices + quarterly NAVs | ~2004 (thin) | 2 (one thin) | The market's live mark on private credit. See rejection note below. |

### Rejected for the watchlist: BDC non-accrual composite

A composite of non-accrual loans / portfolio-at-cost across 8–15 large public BDCs was proposed and is **rejected as a scored candidate and de-prioritised even as a watchlist item**, for reasons that mirror the failure of C1:

- **It is C1's data-assembly blocker again.** Quarterly scraping of 8–15 SEC filings, non-standardized definitions (BDCs report non-accruals at cost *and* at fair value, inconsistently), no standard machine-readable field.
- **Survivorship bias runs the wrong way.** BDCs that blow up stop filing, biasing the composite *green* exactly when it should go red.
- **The history isn't there.** ARCC IPO'd 2004, MAIN 2007, GBDC 2010, FSK 2014, OBDC 2019, BXSL 2021. At the 2008 trough the composite would have roughly three constituents, in a direct-lending market a small fraction of today's size. That is not one recession of history; it is one recession of a materially different asset class.
- **It breaks the architecture.** The project's durability comes from being a single FRED-fed GitHub Action with no manual step. A quarterly filing scrape adds a permanent maintenance obligation and a permanent failure mode.

W5 (price-to-NAV) captures much of the same information daily, from prices, with no assembly burden, and is the better of the two if any BDC-derived measure is carried at all.

---

## 5. Acceptance criteria — fixed before running

Reuse `verdict()` in `run_candidates.py` unchanged. A candidate **passes** only if all of the following hold:

1. **No new false positive.** The candidate must not raise any of the four control windows (1998 LTCM, 2011 debt ceiling, 2015–16 industrial, 2022 rate shock) to WARNING or above when the baseline did not reach that tier.
2. **No degraded lead.** Watch-tier lead times for 2001 and 2007–09 must not fall below baseline.
3. **Individual signal.** The indicator itself must be red at some point in the 24 months before onset in **≥2 of the 3** pre-2020 recessions.
4. **Not redundant.** Disagreement rate versus its nearest existing indicator must exceed 25% of either-red months. (C8 vs #3; C6 vs #13 and C4; C4 vs #17.)
5. **Integrity honesty.** Vintage-class breakdown reported by era. Any era that is predominantly class B is reported as approximate and does not count toward the three-recession bar.

Additional standing rules for this round:

- **No threshold search.** Each candidate has exactly one pre-registered threshold, plus the standard ±20% sensitivity band for reporting only. A candidate that fails at its pre-registered threshold is recorded as FAIL. It is not re-run at a threshold that makes it pass. (v0.3 already spent one global degree of freedom on the ×0.95 scale; that budget is not reopened here.)
- **Failures get written up.** C4–C9 each get a paragraph in `CHANGELOG.md` whether they pass or fail, in the same style as the C1/C2/C3 write-ups. The C2 retry write-up is the model: a clean, well-diagnosed failure is a result.
- **Adding indicators changes the denominator.** Promoting *k* candidates moves `fraction` from `reds/20` to `reds/(20+k)`, mechanically raising the reds needed for every tier. The harness handles this, but the report must show baseline-vs-candidate tier histories side by side so the effect is visible.

---

## 6. Implementation notes

`run_candidates_v05.py` (delivered alongside this document) imports `backtest.py` unmodified, exactly as `run_candidates.py` does, and adds only:

**Two new rule types:**

- `drop_from_peak_abs` — `{ma, peak_window, drop_pp, streak}`. Red when `ma(v) < rolling_max(ma(v), peak_window) - drop_pp`. Absolute percentage points, not the multiplicative form used by the existing `drop_from_peak_ma`, because 0.5pp on an 80.4 base is the interpretable unit for an employment ratio.
- `hamilton_nopi` — `{max_window, pct, streak}`. Red when `v / rolling_max(v.shift(streak), max_window) - 1 > pct/100` holds for `streak` consecutive months. Zero-floored by construction. See the rule-correction note under C9 for why the shift is `streak` and not `1`.

Both new rules ship with unit tests against synthetic series (run them with `python -m pytest` or the inline block at the bottom of the harness). `drop_from_peak_abs`: 4 cases. `hamilton_nopi`: 8 cases, including the pre-registered 2026 case (oil at 100–105 against a 36-month max of 120 → green) and the ×0.95 / ×1.20 sensitivity band. All pass as of delivery.

**One new store class,** `DerivedStore(ExtStore)`, supporting two synthetic series prefixes, both resolved by calling `super().asof()` on each leg at the same evaluation date and merging on date, with the integrity flag taken as the worse of the two legs:

- `RATIO:NUM/DEN` — for C5
- `DIFF:LEFT-RIGHT` — for C8

**Run order:**

```bash
export FRED_API_KEY=...
python run_candidates_v05.py --spec spec_v03.json --sp500-csv spx_daily.csv \
    --out results_v05/ --vintage-report-first
```

`--vintage-report-first` prints the integrity-class coverage table for every new series and **exits before running any board** if `LNS12300060` or `AWHI` vintages do not reach 1988. Fix or reclassify before spending the full run.

The C7 curve sweep is a separate, much cheaper invocation:

```bash
python run_candidates_v05.py --spec spec_v03.json --sp500-csv spx_daily.csv \
    --curve-sweep 365,540,730 --out results_v05/curve/
```

**Expect the first full run to take 30–90 minutes** on a cold FRED cache, per `backtest.py`'s own docstring. The cache is shared, so a prior full backtest run makes this much faster.

---

## 7. Repo hygiene, separate from the candidate round

Small, independent of everything above.

1. **`days_in_state` is a run counter, not a day counter.** `evaluate.py:359` does `days_in_state = prev_days + 1` per execution. A skipped or double GitHub Action run makes it drift silently, and it is displayed to users as days. Derive it from a stored `state_since` date instead.
2. **Data age is invisible in the app.** Indicators #14, #18 and #19 are quarterly with a ~7-month effective lag (Q1-2026 data, released 19 May 2026, still latest in August). They render identically to a Treasury spread from yesterday. Add an age indicator.
3. **Indicator #18 is at its threshold.** 2.92% against a level of 2.85, green only on the "rising" leg, and the spec already carries `integrity_note: "Baseline shifted post-2021; threshold flagged for recalibration review"`. Worth understanding *why* `DRCCLACBS` is falling (3.06 → 2.92 over five quarters) while the NY Fed's flow measure is flat-to-worse: banks have tightened new card issuance and charged off or sold delinquent balances, so the surviving book looks cleaner. A stock ratio on a cleaned, shrinking denominator is a weaker instrument than a transition rate. Note also that NY Fed Q2 2026 shows **mortgage** serious-delinquency transitions rising 1.29% → 1.52% y/y, with cards flat at 6.97% and autos slightly up — mixed, not improving.
4. **Ship a distance-to-threshold bar per indicator.** The single most informative artifact of this review was the gap table, and the app currently discards that information. It also makes the honest case *for* QUIET: with the exception of #18, nothing is within one bad print of red. "0/20 and nothing is close" is a much stronger statement than "0/20."

---

## 8. Summary table

| ID | Candidate | Tier | History | Recessions | Expected verdict |
|---|---|---|---|---|---|
| C4 | Prime-age EPOP (`LNS12300060`) | SCOREABLE | 1948– | 3+ (vintage risk) | Pass — highest-value candidate |
| C5 | Deflate #12 by PPI cap. equipment | CORRECTION | 1947– | 3 | Pass; may change nothing, still worth doing |
| C6 | Aggregate weekly hours (`AWHI`) | SCOREABLE | 1964– | 3+ | Uncertain — 2015–16 is the risk |
| C7 | Curve lookback 365→730 (variant 1c) | CORRECTION | full | 3 | Uncertain — 1998 / 2015–16 are the risk |
| C8 | Baa − Aaa quality spread | SCOREABLE | 1919– | 3+ | Likely rejected as redundant with #3 |
| C9 | Hamilton net oil price increase | SCOREABLE | 1946– | 3+ | Pass on history; **green through 2026 by design** |
| W1–W5 | Watchlist | DISPLAY ONLY | varies | 0–2 | Never scored |
| — | BDC non-accrual composite | REJECTED | ~2004 thin | 1 thin | C1's blocker again |

**If exactly one thing gets done from this document, make it C7.** It is a one-parameter change to an existing indicator, costs no new data, uses the full history, and addresses a gap that opened five months ago and is open right now.
