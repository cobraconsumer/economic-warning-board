#!/usr/bin/env python3
"""
Warning Board -- v0.3 threshold review.

Sweeps a single global scale factor across all scalable thresholds and applies
the decision rule pre-registered in spec-v0.3-threshold-review.md. The rule is
applied mechanically: this script has no discretion and no tunable knobs.

Does not modify backtest.py. Reports, for every scale:
    - Watch / Warning lead months for 1990, 2001, 2007
    - worst tier reached in each of the four control windows
    - quiet fraction over the full history
    - full tier distribution

Usage:
    export FRED_API_KEY=...
    python threshold_review.py --sp500-csv spx_daily.csv --out results_v03/
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

import backtest as bt

SCALES = [0.70, 0.80, 0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.20, 1.30]

# Pre-registered constraints
MIN_QUIET = 0.70
MAX_CONTROL_TIER = "WATCH"      # Warning or Broad in a control window disqualifies
TIER_ORDER = {"-": 0, "WATCH": 1, "WARNING": 2, "BROAD": 3}


def memoize_store(store):
    """In-process memo for vintage fetches. The data pulled is identical at
    every scale, so this avoids re-reading the disk cache ~9k times per scale."""
    inner = store.fred.observations
    cache = {}

    def wrapped(series_id, realtime=None):
        key = (series_id, realtime)
        if key not in cache:
            cache[key] = inner(series_id, realtime=realtime)
        return cache[key]

    store.fred.observations = wrapped
    return store


def evaluate_scale(spec, store, dates, scale, curve_variant="b"):
    board = bt.run_board(spec, store, dates, scale=scale,
                         curve_variant=curve_variant, quiet=True)
    scored = bt.score_board(board, spec)
    s = scored.set_index("date")

    leads = {}
    for rec in spec["nber_recessions"]:
        if rec.get("external_shock"):
            continue
        start = datetime.strptime(rec["start"], "%Y-%m-%d").date()
        w = s[(s.index >= start - timedelta(days=760)) & (s.index <= start)]
        entry = {}
        for tier in ("WATCH", "WARNING"):
            hits = w[w["tier"].map(TIER_ORDER) >= TIER_ORDER[tier]]
            entry[tier] = bt.months_between(hits.index[0], start) if not hits.empty else None
        leads[rec["name"]] = entry

    controls = {}
    for wdef in spec["false_positive_windows"]:
        ws = datetime.strptime(wdef["start"], "%Y-%m-%d").date()
        we = datetime.strptime(wdef["end"], "%Y-%m-%d").date()
        w = s[(s.index >= ws) & (s.index <= we)]
        controls[wdef["name"]] = (max(w["tier"], key=lambda t: TIER_ORDER[t])
                                  if not w.empty else None)

    dist = scored["tier"].value_counts().to_dict()
    quiet = dist.get("-", 0) / len(scored)
    current = scored.iloc[-1]

    return {
        "scale": scale,
        "leads": leads,
        "controls": controls,
        "quiet": quiet,
        "dist": dist,
        "current": f"{int(current['reds'])}/{int(current['available'])} {current['tier']}",
        "scored": scored,
    }


def eligible(r):
    """Applies the three pre-registered hard constraints. Returns (bool, reasons)."""
    fails = []
    for name, tier in r["controls"].items():
        if tier is not None and TIER_ORDER[tier] > TIER_ORDER[MAX_CONTROL_TIER]:
            fails.append(f"{name}={tier}")
    if r["quiet"] < MIN_QUIET:
        fails.append(f"quiet={r['quiet']:.0%}")
    for era, v in r["leads"].items():
        if v["WATCH"] is None:
            fails.append(f"{era} no Watch")
    return (len(fails) == 0), fails


def median_watch(r):
    vals = [v["WATCH"] for v in r["leads"].values() if v["WATCH"] is not None]
    if len(vals) < 3:
        return -1
    return float(pd.Series(vals).median())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="spec_v021.json")
    ap.add_argument("--start", default="1988-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default="results_v03")
    ap.add_argument("--cache", default=".fred_cache")
    ap.add_argument("--sp500-csv", default=None)
    ap.add_argument("--curve-variant", default="b")
    args = ap.parse_args()

    key = os.environ.get("FRED_API_KEY")
    if not key:
        sys.exit("Set FRED_API_KEY")

    spec = json.loads(Path(args.spec).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    store = memoize_store(bt.SeriesStore(bt.Fred(key, Path(args.cache)),
                                         sp500_csv=args.sp500_csv))
    dates = bt.month_grid(args.start, args.end)

    results = []
    for sc in SCALES:
        print(f"  scale {sc:.2f} ...", file=sys.stderr)
        results.append(evaluate_scale(spec, store, dates, sc, args.curve_variant))

    # ---- report --------------------------------------------------------
    lines = ["=" * 92, "THRESHOLD REVIEW -- v0.3 (decision rule pre-registered)", "=" * 92, ""]
    lines.append(f"{'scale':>6}  {'1990W':>6} {'2001W':>6} {'2007W':>6}  "
                 f"{'medW':>5}  {'quiet':>6}  {'worst control window':<34} elig")
    lines.append("-" * 92)

    for r in results:
        ok, fails = eligible(r)
        def w(e):
            v = r["leads"].get(e, {}).get("WATCH")
            return "-" if v is None else str(v)
        worst = max((t for t in r["controls"].values() if t), key=lambda t: TIER_ORDER[t],
                    default="-")
        worst_where = [k for k, v in r["controls"].items() if v == worst]
        mw = median_watch(r)
        lines.append(
            f"{r['scale']:>6.2f}  {w('1990-91'):>6} {w('2001'):>6} {w('2007-09'):>6}  "
            f"{mw if mw >= 0 else '-':>5}  {r['quiet']:>6.0%}  "
            f"{worst + ' (' + (worst_where[0][:22] if worst_where else '') + ')':<34} "
            f"{'YES' if ok else 'no: ' + ', '.join(fails[:2])}")

    lines.append("")

    # ---- decision ------------------------------------------------------
    elig = [r for r in results if eligible(r)[0]]
    baseline = next(r for r in results if abs(r["scale"] - 1.00) < 1e-9)
    base_mw = median_watch(baseline)

    lines += ["-" * 92, "DECISION", "-" * 92,
              f"  baseline (x1.00) median Watch lead: {base_mw} months, "
              f"quiet {baseline['quiet']:.0%}",
              f"  eligible scales: {[r['scale'] for r in elig] or 'none'}"]

    better = [r for r in elig if median_watch(r) > base_mw]
    if not better:
        chosen = None
        lines += ["", "  RESULT: NO CHANGE.",
                  "  No eligible scale improves on the validated specification.",
                  "  v0.2.1 stands as shipped."]
    else:
        best_mw = max(median_watch(r) for r in better)
        tied = [r for r in better if median_watch(r) == best_mw]
        chosen = min(tied, key=lambda r: abs(r["scale"] - 1.00))
        lines += ["", f"  RESULT: adopt scale x{chosen['scale']:.2f}",
                  f"  median Watch lead {base_mw} -> {best_mw} months",
                  f"  quiet fraction {baseline['quiet']:.0%} -> {chosen['quiet']:.0%}",
                  f"  Watch leads: " + ", ".join(
                      f"{e}={v['WATCH']}mo" for e, v in chosen["leads"].items()),
                  f"  current reading: {chosen['current']}"]
        if len(tied) > 1:
            lines.append(f"  (tie among {[r['scale'] for r in tied]}, "
                         f"resolved toward 1.00 per pre-registered rule)")

    # ---- write spec if changed -----------------------------------------
    if chosen is not None:
        new = json.loads(json.dumps(spec))
        new["spec_version"] = "0.3"
        new["threshold_scale_applied"] = chosen["scale"]
        new["amendment_note"] = (
            f"v0.3: single global threshold scale x{chosen['scale']:.2f} applied to all "
            "scalable thresholds, selected by the decision rule pre-registered in "
            "spec-v0.3-threshold-review.md. One degree of freedom, calibrated against "
            "three recessions. Board is CALIBRATED, not out-of-sample validated, at "
            "this scale; the v0.2.1 (x1.00) leads remain the honest out-of-sample "
            "figures. Indicator membership, persistence rules, tier fractions and "
            "curve variant unchanged. Candidates C1-C3 tested and rejected.")
        for ind in new["indicators"]:
            for k in ind.get("scalable", []):
                ind["params"][k] = round(ind["params"][k] * chosen["scale"], 6)
        p = Path("spec_v03.json")
        p.write_text(json.dumps(new, indent=2))
        h = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
        lines += ["", f"  wrote spec_v03.json  sha256:{h}  (record this hash)"]
        chosen["scored"].to_csv(out / "scored_v03.csv", index=False)

    lines += ["", "-" * 92,
              "Full sweep recorded above, including rejected scales, per the",
              "pre-registration's disclosure requirement."]

    report = "\n".join(lines)
    (out / "threshold_review.txt").write_text(report)
    print("\n" + report)
    print(f"\nWritten to {out}/")


if __name__ == "__main__":
    main()
