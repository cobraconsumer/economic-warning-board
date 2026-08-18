# Warning Board — v0.3 Threshold Review (PRE-REGISTERED)

**Status:** decision rule declared BEFORE the sweep is run. Written 18 August 2026, after the v0.2.1 results and the C1–C3 candidate rejections, and before any multi-scale threshold output has been observed.

---

## What prompted this

The v0.2.1 sensitivity analysis, which was itself pre-registered, produced an asymmetric result:

| Scale | 1990 Warning lead | 2001 Warning lead | 2007 Warning lead | False Broad |
|-------|-------------------|-------------------|-------------------|-------------|
| ×0.8 (looser) | 11 mo | 3 mo | 3 mo | none |
| ×1.0 (frozen) | none | 2 mo | 0 mo | none |
| ×1.2 (tighter) | none | 0 mo | 0 mo | none |

Loosening improved every lead and broke nothing that was measured. That is evidence the frozen thresholds sit slightly tight.

**But the measured set was incomplete.** The sensitivity run reported only whether a false *Broad* occurred. It did not report:

1. whether looser thresholds create false **Warnings** in the control windows, and
2. what happens to the **quiet fraction** — the share of months the board says nothing.

Item 2 is the product's core value. A board that gives better lead times but sits at Watch a third of the time is worse than useless: users stop reading it, which is precisely the doomscrolling failure this design exists to avoid. Any threshold decision made without that number is not a real decision.

---

## What is being changed, and what is not

**One global scale factor, applied to every scalable threshold simultaneously.** Not per-indicator tuning.

This matters. Adjusting 12 thresholds individually against 3 recessions would be flagrant overfitting — 12 degrees of freedom against 3 events. A single global multiplier is **one** degree of freedom, and it tests a single coherent hypothesis: *the whole board is calibrated slightly tight.* If that hypothesis is true, one number fixes it. If it is false, no single number will look good, and the rule below returns "no change."

Persistence rules, alert tier fractions, bucket gates, indicator membership, and the curve variant are **not** under review. Only the scale factor.

---

## The decision rule (binding)

Sweep scales: **0.70, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20, 1.30**.

A scale is **eligible** only if all three hard constraints hold:

1. **No Warning or Broad tier in any of the four control windows** (1998, 2011, 2015–16, 2022). Watch is permitted — those were real stress episodes.
2. **Quiet fraction ≥ 70%** across the full 1988–2026 history. The validated board is at 75%; this permits modest loss, not a regime change.
3. **Watch reached before onset in all three pre-2020 recessions** (1990, 2001, 2007).

Among eligible scales, select the one that **maximises the median Watch-tier lead** across the three recessions.

**Tie-break:** prefer the scale closest to 1.00, i.e. the smallest change from the validated specification.

**Default:** if no eligible scale produces a strictly greater median Watch lead than 1.00, **the specification does not change** and v0.2.1 stands as shipped. No-change is a legitimate and expected outcome.

**Objective is Watch, not Warning.** The v0.2.1 results established that Watch is the tier with usable lead time (4–12 months) while Warning arrives at or near onset. Optimising Warning lead would be optimising the wrong thing.

---

## Declared limitations of whatever comes out

Recorded now so it cannot be quietly dropped later:

- **This is calibration against three events.** Even with one degree of freedom, selecting a scale using the same recessions the board was validated on means the resulting lead times are no longer clean out-of-sample estimates. If the scale changes, the results document must describe the board as *calibrated* rather than *validated*, and quote the v0.2.1 (×1.00) leads as the honest out-of-sample figures.
- **No hold-out exists.** Three usable recessions, all used. This is an unavoidable limitation of the problem, not a fixable flaw in the method.
- **The next real test is forward.** Whatever ships, its genuine out-of-sample performance is what it does over the coming years, live.
- **One revision only.** This review runs once. If the outcome is disappointing, the answer is to keep v0.2.1, not to re-open the rule and search further.

---

## Post-decision requirement

Whatever the outcome, record in the changelog: the sweep table in full, the eligible set, the selected scale, and the resulting spec hash. A reader must be able to see every scale that was considered — including the ones that were rejected — not just the winner.
