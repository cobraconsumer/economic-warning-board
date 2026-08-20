#!/usr/bin/env python3
"""
Warning Board -- candidate indicator test harness (v0.5 candidates C4-C9).

Does NOT modify backtest.py or run_candidates.py. Imports the frozen, validated
harness and extends it with the rule types, derived series and reports the v0.5
candidates need, then runs the board several ways:

    baseline (spec_v03.json, 20 indicators)
    baseline + C4   Prime-age employment-population ratio      (add,     bucket C)
    baseline + C6   Index of aggregate weekly hours            (add,     bucket C)
    baseline + C8   Baa - Aaa corporate quality spread         (add,     bucket A)
    baseline + C9   Hamilton net oil price increase            (add,     bucket B)
    baseline w/ C5  Core capital goods orders, PPI-deflated    (REPLACES #12)
    baseline + all passing candidates

and evaluates each against the acceptance criteria pre-registered in
spec-v0.5-candidates.md.

C7 (yield-curve lookback 365 -> 540 -> 730, "variant 1c") is a parameter sweep on
an existing indicator, not an added candidate. It runs via --curve-sweep.

Usage:
    export FRED_API_KEY=...

    # ALWAYS run this first. Exits before the expensive part if the vintage
    # coverage for C4/C6 does not reach the backtest start date.
    python run_candidates_v05.py --spec spec_v03.json --vintage-report-first

    # full candidate round
    python run_candidates_v05.py --spec spec_v03.json --sp500-csv spx_daily.csv \
        --out results_v05/

    # C7 curve sweep (cheap, separate)
    python run_candidates_v05.py --spec spec_v03.json --sp500-csv spx_daily.csv \
        --curve-sweep 365,540,730 --out results_v05/curve/

PRE-REGISTRATION NOTE
---------------------
Thresholds below are the ones recorded in spec-v0.5-candidates.md BEFORE any
run. Do not edit them to make a candidate pass. A candidate that fails at its
pre-registered threshold is a FAIL and gets written up as one, in the same
style as the C1/C2/C3 entries in CHANGELOG.md.

Pre-registered expectation for C9, recorded here so it cannot be retrofitted:
C9 is expected to read GREEN throughout the 2026 oil shock, because WTI's
trailing 36-month maximum in Feb 2026 still includes the 2022 highs. If C9
reads red in 2026 that is evidence of MISCALIBRATION, not of success.
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

import backtest as bt
import run_candidates as rc   # reuse ExtStore, verdict, redundancy, leads_and_fps


# ---------------------------------------------------------------------------
# Candidate definitions (mirror spec-v0.5-candidates.md exactly)
# ---------------------------------------------------------------------------

C4 = {
    "id": 24, "name": "Prime-age employment-population ratio",
    "bucket": "C", "role": "leading",
    "fred": "LNS12300060", "freq": "m", "revised": True,
    "rule": "drop_from_peak_abs",
    "params": {"ma": 1, "peak_window": 12, "drop_pp": 0.5, "streak": 2},
    "scalable": ["drop_pp"],
    "integrity_note": (
        "CPS levels are not revised backward, but annual population-control and "
        "seasonal-factor updates create unbackfilled discontinuities. Report the "
        "V/B/M integrity split by era before quoting any lead time."
    ),
}

C6 = {
    "id": 26, "name": "Aggregate weekly hours, total private",
    "bucket": "C", "role": "leading",
    "fred": "AWHI", "freq": "m", "revised": True,
    "rule": "yoy_below",
    "params": {"pct": -0.5, "streak": 2},
    "scalable": ["pct"],
    "integrity_note": "Subject to annual payroll benchmark revisions; vintage-tracked.",
}

C8 = {
    "id": 28, "name": "Baa - Aaa corporate quality spread",
    "bucket": "A", "role": "leading",
    "fred": "DIFF:BAA-AAA", "freq": "m", "revised": False,
    "rule": "level_above",
    "params": {"level": 1.20, "streak": 2},
    "scalable": ["level"],
    "integrity_note": (
        "Market yields, unrevised (class M), 1919-. Pure within-corporate quality "
        "migration -- unlike #3 (Baa - 10Y) it carries no Treasury/duration leg. "
        "NOT a private credit measure; must not be labelled as one in the app."
    ),
}

C9 = {
    "id": 29, "name": "Hamilton net oil price increase",
    "bucket": "B", "role": "leading",
    "fred": "WTISPLC", "freq": "m", "revised": False,
    "rule": "hamilton_nopi",
    "params": {"max_window": 36, "pct": 40.0, "streak": 2},
    "scalable": ["pct"],
    "integrity_note": (
        "Hamilton (1996; 3-year variant 2003) net oil price increase, computed on "
        "NOMINAL WTI to stay in integrity class M and avoid importing CPI "
        "revisions. Fires only on new 3-year highs by construction."
    ),
}

# C5 REPLACES indicator #12 rather than adding a slot.
C5_REPLACES = 12
C5 = {
    "id": 12, "name": "Core capital goods orders (real, PPI-deflated)",
    "bucket": "B", "role": "leading",
    "fred": "RATIO:NEWORDER/WPSFD41312", "freq": "m", "revised": True,
    "legs_revised": [True, True],
    "rule": "yoy_below",
    "params": {"pct": -1.9, "streak": 2},
    "scalable": ["pct"],
    "integrity_note": (
        "Same rule and threshold as nominal #12. Closes the internal inconsistency "
        "with the C2 rejection, which turned on nominal series never showing "
        "sustained contraction. PPI is barely revised, so the deflator adds "
        "negligible vintage risk."
    ),
}

ADDITIVE = [C4, C6, C8, C9]

# Nearest existing indicator for the redundancy criterion (>=25% disagreement).
REDUNDANCY_PAIRS = {
    24: [(17, "Sahm rule"), (15, "initial claims")],
    26: [(13, "temp help"), (15, "initial claims")],
    28: [(3, "Baa - 10Y"), (2, "HY OAS")],
    29: [(9, "industrial production")],
}


# ---------------------------------------------------------------------------
# Extended rule evaluation
# ---------------------------------------------------------------------------

def evaluate_ext(ind, df, D, scale=1.0):
    """Handles the v0.5 rule types; delegates everything else down the chain so
    existing indicators evaluate byte-identically to the frozen harness."""
    rule = ind["rule"]
    if rule not in ("drop_from_peak_abs", "hamilton_nopi"):
        return rc.evaluate_ext(ind, df, D, scale=scale)

    p = dict(ind["params"])
    for k in ind.get("scalable", []):
        p[k] = p[k] * scale
    v = df["value"].reset_index(drop=True)

    if rule == "drop_from_peak_abs":
        need = p["ma"] + p["peak_window"] + p["streak"]
        if len(v) < need:
            return None, {}
        ma = v.rolling(int(p["ma"])).mean()
        peak = ma.rolling(int(p["peak_window"])).max()
        cond = ma < (peak - p["drop_pp"])
        return bt._streak_at_end(cond.fillna(False), int(p["streak"])), {}

    if rule == "hamilton_nopi":
        s = int(p["streak"])
        need = int(p["max_window"]) + s + 1
        if len(v) < need:
            return None, {}
        # Reference max is lagged by the full streak length, NOT by 1. Lagging by 1
        # makes the streak near-unsatisfiable: the first month of a shock sets a new
        # high, which then becomes the second month's own reference, so NOPI collapses
        # to ~0 exactly when the rule asks for persistence. Lagging by `streak`
        # compares every month of the streak against the same pre-shock baseline,
        # which is what "above its 3-year high for 2 straight months" actually means.
        prior_max = v.shift(s).rolling(int(p["max_window"])).max()
        nopi = (v / prior_max - 1.0) * 100.0
        cond = nopi > p["pct"]
        return bt._streak_at_end(cond.fillna(False), s), {}

    raise ValueError(f"unknown rule {rule}")


# ---------------------------------------------------------------------------
# Derived series store (RATIO: and DIFF:)
# ---------------------------------------------------------------------------

_IQ = {"M": 0, "V": 1, "B": 2, "missing": 3}
_IQ_INV = {v: k for k, v in _IQ.items()}


def _worse(a, b):
    return _IQ_INV[max(_IQ.get(a, 3), _IQ.get(b, 3))]


class DerivedStore(rc.ExtStore):
    """Adds two-leg derived series, resolved leg-by-leg at the SAME evaluation
    date so the result stays point-in-time correct. Integrity is the worse of
    the two legs -- a vintage-clean numerator over a class-B denominator is a
    class-B series, not a class-V one."""

    @staticmethod
    def _split(sid):
        if sid.startswith("RATIO:"):
            left, right = sid[6:].split("/", 1)
            return "ratio", left, right
        if sid.startswith("DIFF:"):
            left, right = sid[5:].split("-", 1)
            return "diff", left, right
        return None, None, None

    def asof(self, ind, D):
        kind, left, right = self._split(ind["fred"])
        if kind is None:
            return super().asof(ind, D)

        legs_revised = ind.get("legs_revised", [ind.get("revised", True)] * 2)
        out = []
        integrity = "M"
        for sid, rev in zip((left, right), legs_revised):
            leg = dict(ind, fred=sid, revised=rev)
            leg.pop("legs_revised", None)
            df, iq = super().asof(leg, D)
            if df is None or df.empty:
                return None, "missing"
            out.append(df[["date", "value"]])
            integrity = _worse(integrity, iq)

        m = out[0].merge(out[1], on="date", how="inner", suffixes=("_l", "_r"))
        if m.empty:
            return None, "missing"
        if kind == "ratio":
            m = m[m["value_r"] != 0]
            if m.empty:
                return None, "missing"
            m["value"] = m["value_l"] / m["value_r"]
        else:
            m["value"] = m["value_l"] - m["value_r"]
        return m[["date", "value"]].sort_values("date").reset_index(drop=True), integrity


# ---------------------------------------------------------------------------
# Board runner (routes through this module's evaluate_ext)
# ---------------------------------------------------------------------------

def run_board_v05(spec, store, dates, scale=1.0, curve_variant="b",
                  curve_lookback=None, quiet=True):
    rows = []
    for i, D in enumerate(dates):
        if not quiet and i % 48 == 0:
            print(f"    {D} ({i+1}/{len(dates)})", file=sys.stderr)
        row = {"date": D}
        for ind in spec["indicators"]:
            key = f"i{ind['id']:02d}"
            if curve_lookback is not None and ind["rule"] == "curve":
                ind = dict(ind, params=dict(ind["params"], lookback_days=curve_lookback))
            df, integrity = store.asof(ind, D)
            if df is None or df.empty or bt.is_stale(ind, df, D, spec["staleness_days"]):
                row[key], row[key + "_q"] = np.nan, "missing"
                continue
            red, detail = evaluate_ext(ind, df, D, scale=scale)
            if red is None:
                row[key], row[key + "_q"] = np.nan, "short"
                continue
            if ind["rule"] == "curve" and curve_variant == "b":
                red = detail["variant_b"]
            row[key] = int(red)
            row[key + "_q"] = integrity
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Vintage coverage pre-flight
# ---------------------------------------------------------------------------

NEW_SERIES = [
    ("C4", "LNS12300060", True),
    ("C6", "AWHI", True),
    ("C5", "NEWORDER", True),
    ("C5", "WPSFD41312", True),
    ("C8", "BAA", False),
    ("C8", "AAA", False),
    ("C9", "WTISPLC", False),
]


def vintage_report(fred, start_date):
    """Prints first-vintage coverage for every new series. Returns list of
    (tag, sid) that cannot be evaluated vintage-correctly from `start_date`."""
    print("=" * 74)
    print("VINTAGE COVERAGE PRE-FLIGHT")
    print("=" * 74)
    print(f"{'cand':<5} {'series':<16} {'revised':<8} {'first vintage':<15} status")
    problems = []
    for tag, sid, revised in NEW_SERIES:
        if not revised:
            print(f"{tag:<5} {sid:<16} {'no':<8} {'n/a (class M)':<15} OK -- unrevised")
            continue
        try:
            vints = fred.vintage_dates(sid)
        except Exception as e:                                   # noqa: BLE001
            print(f"{tag:<5} {sid:<16} {'yes':<8} {'ERROR':<15} {e}")
            problems.append((tag, sid))
            continue
        if not vints:
            print(f"{tag:<5} {sid:<16} {'yes':<8} {'NONE':<15} FAIL -- no ALFRED vintages")
            problems.append((tag, sid))
            continue
        first = vints[0]
        ok = first <= start_date
        status = ("OK" if ok else
                  f"WARN -- {start_date} .. {first} would be class B (approximate)")
        print(f"{tag:<5} {sid:<16} {'yes':<8} {first.isoformat():<15} {status}")
        if not ok:
            problems.append((tag, sid))
    print()
    if problems:
        print("Series whose early evaluation dates fall back to class B "
              "(earliest-vintage approximation):")
        for tag, sid in problems:
            print(f"  {tag}: {sid}")
        print()
        print("Per spec-v0.5-candidates.md section 5, criterion 5: any era that is")
        print("predominantly class B is reported as APPROXIMATE and does not count")
        print("toward the >=3-recession bar. If C4's 1990 era is class B, C4 has")
        print("2 clean recessions and must be demoted to WATCHLIST, not promoted.")
    else:
        print("All revised series have vintage coverage back to the start date.")
    print()
    return problems


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="spec_v03.json")
    ap.add_argument("--start", default="1988-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default="results_v05")
    ap.add_argument("--cache", default=".fred_cache")
    ap.add_argument("--sp500-csv", default=None)
    ap.add_argument("--curve-variant", default="b", choices=["a", "b"])
    ap.add_argument("--curve-sweep", default=None,
                    help="comma-separated lookback_days values, e.g. 365,540,730 (C7)")
    ap.add_argument("--vintage-report-first", action="store_true",
                    help="print vintage coverage and exit before the expensive run")
    ap.add_argument("--sensitivity", action="store_true")
    ap.add_argument("--self-test", action="store_true",
                    help="unit-test the new rules against synthetic data and exit "
                         "(no network, no FRED key)")
    args = ap.parse_args()

    if args.self_test:
        sys.exit(self_test())

    key = os.environ.get("FRED_API_KEY")
    if not key:
        sys.exit("Set FRED_API_KEY")

    base_spec = json.loads(Path(args.spec).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fred = bt.Fred(key, Path(args.cache))
    start_date = pd.Timestamp(args.start + "-01").date()

    problems = vintage_report(fred, start_date)
    if args.vintage_report_first:
        (out / "vintage_preflight.json").write_text(
            json.dumps({"start": str(start_date),
                        "class_b_series": [{"cand": t, "series": s} for t, s in problems]},
                       indent=2))
        print(f"Pre-flight written to {out}/vintage_preflight.json")
        print("Re-run without --vintage-report-first to execute the candidate round.")
        return

    store = DerivedStore(fred, sp500_csv=args.sp500_csv, csv_sources={})
    dates = bt.month_grid(args.start, args.end)

    # ---- C7: curve lookback sweep (cheap path, exits after) --------------
    if args.curve_sweep:
        lookbacks = [int(x) for x in args.curve_sweep.split(",")]
        lines = ["=" * 74, "C7 -- YIELD CURVE LOOKBACK SWEEP (variant 1c)", "=" * 74, "",
                 "Indicator #1 params.lookback_days. 365 is the frozen v0.3 value.",
                 "The 1998 and 2015-16 control windows are where a longer window is",
                 "punished; those are the tests that matter.", ""]
        sweep = {}
        for lb in lookbacks:
            print(f"== curve lookback {lb}d ==", file=sys.stderr)
            board = run_board_v05(base_spec, store, dates,
                                  curve_variant=args.curve_variant, curve_lookback=lb)
            scored = bt.score_board(board, base_spec)
            leads, fps, ig = rc.leads_and_fps(scored, base_spec)
            board.to_csv(out / f"board_curve_{lb}.csv", index=False)
            scored.to_csv(out / f"scored_curve_{lb}.csv", index=False)
            sweep[lb] = {"leads": leads, "fps": fps,
                         "ignition": [str(d) for d in ig],
                         "current": {
                             "date": str(scored.iloc[-1]["date"]),
                             "reds": int(scored.iloc[-1]["reds"]),
                             "tier": scored.iloc[-1]["tier"],
                             "i01": (None if pd.isna(board.iloc[-1]["i01"])
                                     else int(board.iloc[-1]["i01"])),
                         }}
            lines += [f"lookback {lb}d",
                      "  Watch/Warning lead months: " + _fmt_leads(leads),
                      "  control windows: " + ", ".join(
                          f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in fps.items()
                          if v["peak"] is not None),
                      f"  #1 red today: {sweep[lb]['current']['i01']}"
                      f"   board today: {sweep[lb]['current']['reds']} red,"
                      f" {sweep[lb]['current']['tier']}", ""]
        lines += ["DECISION RULE (pre-registered)",
                  "  Adopt the longest lookback that does not raise 1998 or 2015-16",
                  "  above the 365d baseline's worst tier AND does not shorten the",
                  "  2001 or 2007-09 Watch lead. If 365d wins on those tests, the",
                  "  March 2026 gap is the honest cost of the frozen rule and stays."]
        report = "\n".join(lines)
        (out / "curve_sweep_report.txt").write_text(report)
        json.dump(sweep, open(out / "curve_sweep.json", "w"), indent=2, default=str)
        print("\n" + report)
        return

    # ---- baseline --------------------------------------------------------
    print("== baseline (v0.3) ==", file=sys.stderr)
    base_board = run_board_v05(base_spec, store, dates, curve_variant=args.curve_variant)
    base_scored = bt.score_board(base_board, base_spec)
    base_leads, base_fps, base_ig = rc.leads_and_fps(base_scored, base_spec)
    base_board.to_csv(out / "board_baseline.csv", index=False)

    def spec_add(cands):
        s = json.loads(json.dumps(base_spec))
        s["indicators"] = s["indicators"] + list(cands)
        return s

    def spec_replace(new_ind, old_id):
        s = json.loads(json.dumps(base_spec))
        s["indicators"] = [new_ind if i["id"] == old_id else i for i in s["indicators"]]
        return s

    results = {}

    # ---- additive candidates, one at a time ------------------------------
    for cand in ADDITIVE:
        tag = f"C{cand['id'] - 20}"
        print(f"== {tag}: {cand['name']} ==", file=sys.stderr)
        sp = spec_add([cand])
        board = run_board_v05(sp, store, dates, curve_variant=args.curve_variant)
        scored = bt.score_board(board, sp)
        cl, cf, ig = rc.leads_and_fps(scored, sp)
        board.to_csv(out / f"board_{tag}.csv", index=False)
        scored.to_csv(out / f"scored_{tag}.csv", index=False)

        notes = []

        # integrity split by era -- criterion 5
        qcol = f"i{cand['id']:02d}_q"
        if qcol in board:
            q = board[qcol].value_counts().to_dict()
            notes.append(f"integrity classes: {q}")
            early = board[board["date"] < pd.Timestamp("1998-01-01").date()]
            if len(early):
                eq = early[qcol].value_counts().to_dict()
                notes.append(f"pre-1998 integrity: {eq}")
                if eq.get("B", 0) > 0.5 * len(early):
                    notes.append("CRITERION 5 WARNING: pre-1998 predominantly class B "
                                 "-- 1990 result is APPROXIMATE and does not count "
                                 "toward the 3-recession bar")

        # criterion 3: own red pre-onset in >=2 of 3
        own = rc.indicator_red_before_onset(board, cand["id"], sp)
        hits = sum(1 for v in own.values() if v)
        notes.append(f"own red pre-onset: {own} ({hits}/3)")
        if hits < 2:
            notes.append("CRITERION 3 FAIL: red in fewer than 2 of 3 recessions")

        # criterion 4: redundancy
        for other_id, other_name in REDUNDANCY_PAIRS.get(cand["id"], []):
            r = rc.redundancy(board, other_id, cand["id"])
            shown = "n/a" if r is None else f"{r:.0%}"
            notes.append(f"disagreement with #{other_id} ({other_name}): "
                         f"{shown} (needs >=25%)")
            if r is not None and r < 0.25:
                notes.append(f"CRITERION 4 FAIL: redundant with #{other_id}")

        # C9-specific pre-registered expectation
        if cand["id"] == 29:
            recent = board[board["date"] >= pd.Timestamp("2026-01-01").date()]
            fired = bool((recent[f"i{cand['id']:02d}"] == 1).any()) if len(recent) else False
            notes.append(f"2026 reading (expected GREEN): "
                         f"{'RED -- MISCALIBRATED' if fired else 'green, as pre-registered'}")
            if fired:
                notes.append("CRITERION FAIL: C9 fired on the 2026 shock, which the "
                             "3-year-max construction should have excluded")

        v, fails, notes = rc.verdict(tag, base_leads, base_fps, cl, cf, notes)
        if any("CRITERION" in n and "FAIL" in n for n in notes):
            v = "FAIL"
        results[tag] = {"name": cand["name"], "verdict": v, "fails": fails,
                        "notes": notes, "leads": cl, "fps": cf,
                        "ignition": [str(d) for d in ig]}

    # ---- C5: replacement, not addition -----------------------------------
    print("== C5: %s (REPLACES #%d) ==" % (C5["name"], C5_REPLACES), file=sys.stderr)
    sp5 = spec_replace(C5, C5_REPLACES)
    board5 = run_board_v05(sp5, store, dates, curve_variant=args.curve_variant)
    scored5 = bt.score_board(board5, sp5)
    l5, f5, ig5 = rc.leads_and_fps(scored5, sp5)
    board5.to_csv(out / "board_C5.csv", index=False)
    scored5.to_csv(out / "scored_C5.csv", index=False)
    notes5 = ["C5 replaces #12 rather than adding a slot: denominator unchanged at 20.",
              "Pass condition is NOT 'improves leads'. It is 'closes the nominal/real "
              "inconsistency with the C2 rejection without degrading anything'."]
    # how often does deflating actually change indicator #12's colour?
    cmp12 = pd.DataFrame({"nom": base_board["i12"], "real": board5["i12"]}).dropna()
    either = cmp12[(cmp12.nom == 1) | (cmp12.real == 1)]
    if len(either):
        notes5.append(f"nominal vs real #12 disagreement: "
                      f"{(either.nom != either.real).mean():.0%} of either-red months "
                      f"({len(either)} months)")
        only_real = int(((cmp12.real == 1) & (cmp12.nom == 0)).sum())
        only_nom = int(((cmp12.nom == 1) & (cmp12.real == 0)).sum())
        notes5.append(f"red only when deflated: {only_real} months; "
                      f"red only when nominal: {only_nom} months")
    else:
        notes5.append("nominal vs real #12: never red on either measure -- "
                      "inconclusive, report as such")
    for era in ("1990-91", "2001", "2007-09"):
        b = base_leads.get(era, {}).get("WATCH")
        c = l5.get(era, {}).get("WATCH")
        notes5.append(f"{era} Watch lead: nominal {b} -> real {c} months")
    v5, fails5, notes5 = rc.verdict("C5", base_leads, base_fps, l5, f5, notes5)
    results["C5"] = {"name": C5["name"], "verdict": v5, "fails": fails5,
                     "notes": notes5, "leads": l5, "fps": f5,
                     "ignition": [str(d) for d in ig5]}

    # ---- all passing additive candidates together ------------------------
    passing = [c for c in ADDITIVE if results[f"C{c['id'] - 20}"]["verdict"] == "PASS"]
    if passing:
        print("== all passing candidates ==", file=sys.stderr)
        sp_all = spec_add(passing)
        board_all = run_board_v05(sp_all, store, dates, curve_variant=args.curve_variant)
        scored_all = bt.score_board(board_all, sp_all)
        al, af, aig = rc.leads_and_fps(scored_all, sp_all)
        board_all.to_csv(out / "board_all.csv", index=False)
        scored_all.to_csv(out / "scored_all.csv", index=False)
    else:
        sp_all, scored_all = base_spec, base_scored
        al, af, aig = base_leads, base_fps, base_ig

    # ---- sensitivity -----------------------------------------------------
    sens = {}
    if args.sensitivity and passing:
        print("== sensitivity on full candidate board ==", file=sys.stderr)
        for scale in (0.8, 1.2):
            b = run_board_v05(sp_all, store, dates, scale=scale,
                              curve_variant=args.curve_variant)
            sc = bt.score_board(b, sp_all)
            sl, sf, _ = rc.leads_and_fps(sc, sp_all)
            sens[scale] = {"leads": sl, "fps": sf}

    # ---- report ----------------------------------------------------------
    lines = ["=" * 74, "CANDIDATE EVALUATION -- v0.5 (C4-C9)", "=" * 74, "",
             "Pre-registered in spec-v0.5-candidates.md. Thresholds were fixed",
             "before this run. No threshold search is permitted on a failure.", "",
             f"BASELINE (v0.3, {len(base_spec['indicators'])} indicators)",
             "  Watch/Warning lead months: " + _fmt_leads(base_leads),
             "  control windows: " + ", ".join(
                 f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in base_fps.items()
                 if v["peak"] is not None), ""]

    for tag in ("C4", "C5", "C6", "C8", "C9"):
        if tag not in results:
            continue
        r = results[tag]
        lines += [f"{tag} -- {r['name']}: {r['verdict']}",
                  "  Watch/Warning lead months: " + _fmt_leads(r["leads"]),
                  "  control windows: " + ", ".join(
                      f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in r["fps"].items()
                      if v["peak"] is not None)]
        lines += [f"  note: {n}" for n in r["notes"]]
        lines += [f"  FAIL: {f}" for f in r["fails"]]
        lines.append("")

    lines += ["ALL PASSING CANDIDATES TOGETHER"
              f" ({len(passing)} promoted, denominator {20 + len(passing)})",
              "  Watch/Warning lead months: " + _fmt_leads(al),
              "  control windows: " + ", ".join(
                  f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in af.items()
                  if v["peak"] is not None),
              f"  C-ignition events: {[str(d) for d in aig]}", ""]

    if sens:
        lines.append("SENSITIVITY (full candidate board)")
        for scale, d in sens.items():
            bad = [k for k, v in d["fps"].items() if v["worst"] == "BROAD"]
            lines.append(f"  x{scale}: " + _fmt_leads(d["leads"])
                         + f"   false BROAD: {bad if bad else 'none'}")
        lines.append("")

    last = scored_all.iloc[-1]
    lines += ["CURRENT READING (with passing candidates)",
              f"  {last['date']}  {int(last['reds'])}/{int(last['available'])} "
              f"({last['fraction']:.0%})  {last['tier']}"
              f"  [A:{int(last['A_red'])} B:{int(last['B_red'])} C:{int(last['C_red'])}]", "",
              "DECISION",
              "  PASS candidates meet every pre-registered criterion and may be",
              "  promoted in a v0.5 amendment. FAIL candidates are recorded as",
              "  tested-and-rejected in CHANGELOG.md and must NOT be retained as",
              "  commentary. Watchlist items W1-W5 are display-only and never enter",
              "  reds / available / fraction."]

    report = "\n".join(lines)
    (out / "candidate_report.txt").write_text(report)
    json.dump(results, open(out / "candidate_results.json", "w"), indent=2, default=str)
    print("\n" + report)
    print(f"\nWritten to {out}/")


def self_test():
    """Unit tests for the two new rules, against synthetic series. No network,
    no FRED key. Run with --self-test before spending an hour on a backtest."""
    def mk(v):
        return pd.DataFrame({"date": pd.date_range("2000-01-01", periods=len(v),
                                                   freq="MS"), "value": v})

    i4 = {"rule": "drop_from_peak_abs",
          "params": {"ma": 1, "peak_window": 12, "drop_pp": 0.5, "streak": 2},
          "scalable": ["drop_pp"]}
    i9 = {"rule": "hamilton_nopi",
          "params": {"max_window": 36, "pct": 40.0, "streak": 2},
          "scalable": ["pct"]}

    cases = [
        (i4, "EPOP -0.6pp for 2 months", [80.9] * 18 + [80.3, 80.3], True, 1.0),
        (i4, "EPOP -0.3pp for 2 months", [80.9] * 18 + [80.6, 80.6], False, 1.0),
        (i4, "EPOP dips then recovers", [80.9] * 18 + [80.3, 80.9], False, 1.0),
        (i4, "EPOP -0.6pp for 1 month only", [80.9] * 18 + [80.9, 80.3], False, 1.0),
        (i9, "2026 case: 100-105 vs 36m max 120", [120] * 40 + [100, 105], False, 1.0),
        (i9, "new high sustained: 90,95 vs 60", [60] * 40 + [90, 95], True, 1.0),
        (i9, "new high flat: 90,90 vs 60", [60] * 40 + [90, 90], True, 1.0),
        (i9, "mild +33%: 80,80 vs 60", [60] * 40 + [80, 80], False, 1.0),
        (i9, "spike then fade: 90,65 vs 60", [60] * 40 + [90, 65], False, 1.0),
        (i9, "one month only: 60,95", [60] * 40 + [60, 95], False, 1.0),
        (i9, "x0.95 (pct=38): 83,83 vs 60", [60] * 40 + [83, 83], True, 0.95),
        (i9, "x1.20 (pct=48): 83,83 vs 60", [60] * 40 + [83, 83], False, 1.20),
    ]
    bad = 0
    for ind, label, vals, expect, scale in cases:
        got = evaluate_ext(ind, mk(vals), None, scale=scale)[0]
        ok = got == expect
        bad += 0 if ok else 1
        print(f"{'ok ' if ok else 'XX '}{ind['rule']:20} {label:36} "
              f"-> {got} (expect {expect})")

    for sid, expect in [("RATIO:NEWORDER/WPSFD41312", ("ratio", "NEWORDER", "WPSFD41312")),
                        ("DIFF:BAA-AAA", ("diff", "BAA", "AAA")),
                        ("T10Y3M", (None, None, None))]:
        got = DerivedStore._split(sid)
        ok = got == expect
        bad += 0 if ok else 1
        print(f"{'ok ' if ok else 'XX '}{'derived-split':20} {sid:36} -> {got}")

    for a, b, expect in [("V", "B", "B"), ("M", "V", "V"), ("M", "missing", "missing")]:
        got = _worse(a, b)
        ok = got == expect
        bad += 0 if ok else 1
        print(f"{'ok ' if ok else 'XX '}{'integrity-worse':20} "
              f"{'worse(%s,%s)' % (a, b):36} -> {got}")

    print()
    print("ALL PASS" if not bad else f"{bad} FAILURE(S)")
    return 0 if not bad else 1


def _fmt_leads(d):
    return "  ".join(
        f"{era}: W{v['WATCH'] if v['WATCH'] is not None else '-'}"
        f"/Wn{v['WARNING'] if v['WARNING'] is not None else '-'}"
        for era, v in d.items() if era != "2020")


if __name__ == "__main__":
    main()
