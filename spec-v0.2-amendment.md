# Economic Warning Board — Spec v0.2 (Pre-Registered Amendment)

**Status:** FROZEN upon adoption. This document amends v0.1 in response to review. All changes below are declared *before* any backtest results have been observed. After freezing, no threshold, rule, or tier may change until the v0.2 backtest has been run exactly as written and its results documented. Subsequent changes go in a v0.3 changelog with stated reasons.

---

## Amendment 1 — Indicator #14 renamed

**Was:** "Business loan delinquency rate (private credit proxy)"
**Now:** **"Business Loan Delinquencies"** — no private-credit claim. In-app description: "Delinquency rate on commercial & industrial loans at U.S. banks. Related to, but not a measurement of, non-bank private credit, which has no free public data source."

## Amendment 2 — Yield curve: two pre-registered variants

The v0.1 rule (red while currently inverted) can turn green precisely when risk is rising, because recessions historically begin after re-steepening. Both variants below are registered now; the backtest adjudicates. Neither may be modified after seeing results.

- **Variant 1a (current inversion):** red when T10Y3M < 0 for 15 consecutive trading days.
- **Variant 1b (12-month lookback):** red if the Variant 1a condition was satisfied at any point in the trailing 365 days.

**Adjudication rule, declared in advance:** the shipped variant is whichever produces longer median lead time across the 1990, 2001, and 2007 recessions *without* adding a false Broad-tier episode in 1998, 2011, 2015–16, or 2022. If they tie, 1b ships (it strictly dominates on the re-steepening failure mode).

## Amendment 3 — Indicator #7 reclassified as confirmation

Equity drawdown remains on the board in Bucket A (users expect it; it contributes to counts) but is tagged `role: confirmation`. It is **excluded** from Bucket A's count when testing A→B→C sequencing and Bucket-C ignition (Amendment 5). Rationale: drawdowns confirm repricing; they rarely lead it.

## Amendment 4 — Alert tiers become fractions of available indicators

Data coverage varies by era (see Coverage section). Fixed counts (5/8/12) would make 1990 incomparable to 2007. Tiers are therefore defined as fractions of *available* indicators:

| Tier | v0.1 (counts) | v0.2 (frozen) |
|------|---------------|----------------|
| 🟡 Watch | 5+ of 20 | **≥ 25%** of available indicators red |
| 🟠 Warning | 8+ across ≥2 buckets | **≥ 40%** red, spanning ≥ 2 buckets |
| 🔴 Broad | 12+ with ≥2 per bucket | **≥ 60%** red, AND every bucket with ≥3 available indicators has ≥ 25% of them red |

An indicator is "available" at date D if (a) its series existed with enough history for its rule (e.g., YoY rules need 13 months), and (b) its latest observation is not stale: within 21 days for daily/weekly series, 60 days for monthly, 135 days for quarterly.

## Amendment 5 — Bucket-C ignition: demoted to registered hypothesis

The claim that household-bucket ignition is "the most meaningful event" is a **hypothesis (H1)**, not a feature commitment. Frozen definition for testing:

> **C-ignition event:** the first month in an episode where Bucket C has ≥ 2 reds while Bucket A (excluding #7) has ≥ 3 reds and Bucket B has ≥ 3 reds. An episode resets after the overall red fraction stays below 25% for 6 consecutive months.

H1 is supported if C-ignition occurred before or within the first 3 months of the 1990, 2001, and 2007 recessions, and never occurred in 1998, 2011, 2015–16, or 2022. Partial support (2 of 3 recessions, 0 false positives) keeps it as a secondary display; any false positive at Broad-severity kills it as an alert.

## Amendment 6 — Data-integrity classes (declared, shown in output)

Every indicator-date evaluation carries one of three integrity flags, reported in all backtest output:

- **Class M (market):** unrevised market data (T10Y3M, HY, BBB, SP500). Point-in-time by nature.
- **Class V (vintage):** reconstructed from true ALFRED vintages — data exactly as published at the time.
- **Class B (backfilled approximation):** the series' modern values extend before the index existed or before ALFRED vintages begin. Known members: **NFCI** (index launched ~2011, values backfilled to 1971), **STLFSI4** (created 2010, revised four times, values backfilled to 1993), **CFNAIMA3** (index created 2001, backfilled to 1967). For these, pre-vintage evaluations are honest approximations, not true point-in-time — and any era conclusion resting mainly on Class B lights must be labeled as such.

The harness determines V-vs-B automatically per date from actual ALFRED vintage metadata; the table below is the expected picture, finalized by the harness.

## Approximate Coverage by Test Era

*(Series-start dates approximate; the harness generates the authoritative table from API metadata.)*

| Era | Expected available | Notable gaps |
|-----|--------------------|--------------|
| 1990–91 recession | ~13 of 20 | HY & BBB spreads (begin Dec 1996), STLFSI (1993), core capex orders (1992), retail sales (1992), card & mortgage delinquency rates (1991); NFCI/CFNAI only as Class B |
| 1998 (LTCM) | ~19–20 | CFNAI is Class B (pre-2001); STLFSI/NFCI Class B |
| 2001 recession | 20 | NFCI/STLFSI still Class B (pre-launch) |
| 2007–09 recession | 20 | STLFSI Class B until 2010, NFCI until ~2011 |
| 2011, 2015–16, 2020, 2022 | 20 | Full Class V/M coverage |

Consequence, stated in advance: **the 1990 reconstruction is the weakest test** and is treated as corroborating, not decisive. The primary falsification tests are 2001 and 2007 (leads) versus 1998, 2011, 2015–16, and 2022 (false-positive control). 2020 is expected to show little or no advance warning; that outcome does not count against the board.

## Unchanged from v0.1

All 20 indicators, series IDs, individual thresholds, and persistence rules are unchanged except as amended above. The ±20% threshold-sensitivity test remains mandatory before any threshold is revised.

## SP500 source note

FRED's SP500 license limits history to ~10 years. For backtesting, indicator #7 uses a user-supplied daily close CSV (e.g., Stooq ^SPX export). If absent, #7 is marked unavailable and fractions adjust automatically — pre-registered as acceptable, since #7 is confirmation-role.
