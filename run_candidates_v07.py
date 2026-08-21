#!/usr/bin/env python3
"""
Warning Board -- candidate indicator test harness (v0.7 candidate C10).

Does NOT modify backtest.py or run_candidates.py. Imports the frozen,
validated harness and reuses it unchanged, since C10's rule (level_above)
is already a native rule type -- no new evaluation logic needed, unlike
the v0.5 round.

Runs the board three ways, as spec-v0.7-candidates.md section 4 requires
for C10 specifically ("Run baseline, C10-replaces-17, and C10-added, and
report all three side by side"):

    baseline        (spec_v05.json, 20 indicators, #17 = Sahm Rule)
    C10-replaces-17 (#17 removed, C10 takes its slot; denominator stays 20)
    C10-added       (#17 kept; C10 becomes a 21st indicator)

PRE-REGISTRATION NOTE
----------------------
Params below are the ones recorded in spec-v0.7-candidates.md section 1
BEFORE any run. Do not edit them to make the candidate pass. C10's
revised:false treatment is not this file's decision -- it is the
pre-registered case written up in CHANGELOG.md ("Pre-flight note -- 21
August 2026: C10 vintage and comparability case") BEFORE this script was
run. If that case is wrong, the fix belongs there, not here.

Pre-registered expectations, recorded so they cannot be retrofitted
(spec-v0.7-candidates.md section 1):
- Red before onset in all three of 1990-91, 2001, 2007-09.
- NOT red on the current board (25.5% against a 26.0% threshold, falling
  from 27.3%). A red current reading is evidence of a mis-set threshold,
  not evidence of a recession.
- Highest failure risk: the 2011 control window, where long-term
  unemployment was extraordinarily elevated for years post-GFC. A false
  Warning there is a criterion-1 FAIL, full stop -- it does not get
  rescued by switching to a change-based rule after the fact.

Usage:
    export FRED_API_KEY=...
    python run_candidates_v07.py --spec spec_v05.json --sp500-csv spx_daily.csv \
        --out results_v07/
"""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import backtest as bt
import run_candidates as rc  # reuse ExtStore, verdict, redundancy, leads_and_fps

# ---------------------------------------------------------------------------
# Candidate definition (mirrors spec-v0.7-candidates.md section 1 exactly)
# ---------------------------------------------------------------------------

C10 = {
    "id": 30,
    "name": "Long-term unemployed share (27+ weeks)",
    "bucket": "C",
    "role": "leading",
    "fred": "LNS13025703",
    "freq": "m",
    "revised": False,
    "rule": "level_above",
    "params": {"level": 26.0, "streak": 2},
    "scalable": ["level"],
    "integrity_note": (
        "ALFRED vintage archive starts 2011-09-02 (same wall that demoted "
        "C4). Treated revised:false per the pre-flight case in CHANGELOG.md "
        "(2026-08-21 'C10 vintage and comparability case'): BLS CPS "
        "seasonally-adjusted series revise only via annual seasonal-factor "
        "reestimation, the same mechanism already relied on for "
        "SAHMREALTIME; the 1994 CPS redesign's documented effects are "
        "concentrated in short-term unemployment and mean duration, not "
        "the 27-week-plus share (Abraham & Shimer, NBER WP8513: 0.79% vs "
        "0.78% across their natural-experiment control)."
    ),
}

# Nearest existing indicators for the redundancy criterion (>=25% disagreement).
REDUNDANCY_PAIRS = [(15, "initial claims (4-wk avg)"), (16, "continuing claims")]

REPLACES = 17  # Sahm Rule (real-time)


# ---------------------------------------------------------------------------
# Spec construction
# ---------------------------------------------------------------------------

def spec_baseline(base_spec):
    return json.loads(json.dumps(base_spec))


def spec_replace(base_spec, cand, replaces_id):
    s = json.loads(json.dumps(base_spec))
    s["indicators"] = [i for i in s["indicators"] if i["id"] != replaces_id] + [cand]
    return s


def spec_add(base_spec, cand):
    s = json.loads(json.dumps(base_spec))
    s["indicators"] = s["indicators"] + [cand]
    return s


# ---------------------------------------------------------------------------
# Board runner (C10 needs no new rule evaluation -- level_above is native)
# ---------------------------------------------------------------------------

def run_variant(spec, store, dates):
    board = rc.run_board_ext(spec, store, dates)
    scored = bt.score_board(board, spec)
    leads, fps, ig = rc.leads_and_fps(scored, spec)
    return board, scored, leads, fps, ig


def all_recession_leads_preserved(base_leads, cand_leads):
    """The extra requirement spec-v0.7-candidates.md section 4 states for
    C10 specifically: the replacement variant must preserve every lead the
    Sahm rule contributed, not just 2001/2007-09 (which is all the shared
    verdict() function checks by default)."""
    fails = []
    for era, tiers in base_leads.items():
        for tier in ("WATCH", "WARNING", "BROAD"):
            b = tiers.get(tier)
            c = cand_leads.get(era, {}).get(tier)
            if b is not None and (c is None or c < b):
                fails.append(f"{era} {tier} lead {b}->{c} mo")
    return fails


def integrity_report(board, cand_id):
    """C10 is revised:false, so every evaluation date should carry
    integrity 'M' -- confirm that mechanically rather than assuming it."""
    col = f"i{cand_id:02d}_q"
    if col not in board:
        return "no integrity column found"
    counts = board[col].value_counts().to_dict()
    return counts


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default="spec_v05.json")
    ap.add_argument("--start", default="1988-01")
    ap.add_argument("--end", default=date.today().strftime("%Y-%m"))
    ap.add_argument("--out", default="results_v07")
    ap.add_argument("--cache", default=".fred_cache")
    ap.add_argument("--sp500-csv", default=None)
    args = ap.parse_args()

    key = os.environ.get("FRED_API_KEY")
    if not key:
        sys.exit("Set FRED_API_KEY")

    base_spec = json.loads(Path(args.spec).read_text())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fred = bt.Fred(key, Path(args.cache))
    store = rc.ExtStore(fred, sp500_csv=args.sp500_csv, csv_sources={})
    dates = bt.month_grid(args.start, args.end)

    print("== baseline (spec_v05.json, 20 indicators, #17 = Sahm Rule) ==", file=sys.stderr)
    sp_base = spec_baseline(base_spec)
    board_base, scored_base, leads_base, fps_base, ig_base = run_variant(sp_base, store, dates)
    board_base.to_csv(out / "board_baseline.csv", index=False)
    scored_base.to_csv(out / "scored_baseline.csv", index=False)

    print("== C10-replaces-17 (denominator stays 20) ==", file=sys.stderr)
    sp_replace = spec_replace(base_spec, C10, REPLACES)
    board_r, scored_r, leads_r, fps_r, ig_r = run_variant(sp_replace, store, dates)
    board_r.to_csv(out / "board_C10_replace.csv", index=False)
    scored_r.to_csv(out / "scored_C10_replace.csv", index=False)

    print("== C10-added (21 indicators) ==", file=sys.stderr)
    sp_add = spec_add(base_spec, C10)
    board_a, scored_a, leads_a, fps_a, ig_a = run_variant(sp_add, store, dates)
    board_a.to_csv(out / "board_C10_add.csv", index=False)
    scored_a.to_csv(out / "scored_C10_add.csv", index=False)

    # ---- acceptance criteria --------------------------------------------
    def evaluate_variant(tag, board, spec, leads, fps):
        notes = []
        own = rc.indicator_red_before_onset(board, C10["id"], spec)
        hits = sum(1 for v in own.values() if v)
        notes.append(f"own red pre-onset: {own} ({hits}/3)")
        if hits < 2:
            notes.append("CRITERION 2 FAIL: red in fewer than 2 of 3 pre-2020 recessions")

        for rid, rname in REDUNDANCY_PAIRS:
            r = rc.redundancy(board, C10["id"], rid)
            notes.append(f"disagreement with #{rid} ({rname}): "
                         f"{'n/a' if r is None else f'{r:.0%}'} (needs >=25%)")
            if r is not None and r < 0.25:
                notes.append(f"CRITERION 4 FAIL: redundant with #{rid} ({rname})")

        notes.append(f"integrity classes observed: {integrity_report(board, C10['id'])}")

        v, fails, notes = rc.verdict(tag, leads_base, fps_base, leads, fps, notes)
        if any("CRITERION" in n for n in notes):
            v = "FAIL"
        return v, fails, notes

    v_r, fails_r, notes_r = evaluate_variant("C10-replaces-17", board_r, sp_replace, leads_r, fps_r)
    lead_fails_r = all_recession_leads_preserved(leads_base, leads_r)
    if lead_fails_r:
        notes_r.append("CRITERION (C10-specific) FAIL: did not preserve every "
                        f"Sahm-rule lead: {lead_fails_r}")
        v_r = "FAIL"

    v_a, fails_a, notes_a = evaluate_variant("C10-added", board_a, sp_add, leads_a, fps_a)

    # ---- report -----------------------------------------------------------
    def fmt_leads(d):
        return "  ".join(
            f"{era}: W{v['WATCH'] if v['WATCH'] is not None else '-'}"
            f"/Wn{v['WARNING'] if v['WARNING'] is not None else '-'}"
            for era, v in d.items() if era != "2020")

    lines = ["=" * 74, "C10 CANDIDATE EVALUATION -- v0.7", "=" * 74, "",
             "BASELINE (spec_v05.json, 20 indicators)",
             "  Watch/Warning lead months: " + fmt_leads(leads_base),
             "  control windows: " + ", ".join(
                 f"{k} {v['peak']:.0%}/{v['worst']}" for k, v in fps_base.items()
                 if v["peak"] is not None), ""]

    for tag, v, fails, notes in (("C10-replaces-17", v_r, fails_r, notes_r),
                                  ("C10-added", v_a, fails_a, notes_a)):
        leads = leads_r if tag == "C10-replaces-17" else leads_a
        fps = fps_r if tag == "C10-replaces-17" else fps_a
        lines += [f"{tag}: {v}",
                  "  Watch/Warning lead months: " + fmt_leads(leads),
                  "  control windows: " + ", ".join(
                      f"{k} {vv['peak']:.0%}/{vv['worst']}" for k, vv in fps.items()
                      if vv["peak"] is not None)]
        for n in notes:
            lines.append(f"  note: {n}")
        for f in fails:
            lines.append(f"  FAIL: {f}")
        lines.append("")

    last_r = scored_r.iloc[-1]
    last_a = scored_a.iloc[-1]
    lines += ["CURRENT READING",
              f"  baseline:         {int(scored_base.iloc[-1]['reds'])}/{int(scored_base.iloc[-1]['available'])} {scored_base.iloc[-1]['tier']}",
              f"  C10-replaces-17:  {int(last_r['reds'])}/{int(last_r['available'])} {last_r['tier']}",
              f"  C10-added:        {int(last_a['reds'])}/{int(last_a['available'])} {last_a['tier']}", ""]

    lines += ["DECISION",
              "  C10-replaces-17 passes only if it meets every criterion 1-5 AND",
              "  preserves every Sahm-rule lead across all three recessions. If it",
              "  fails that extra bar but C10-added still passes on its own, the",
              "  addition variant is the fallback per spec-v0.7-candidates.md.",
              "  A FAIL on both is recorded as a rejected candidate, written up",
              "  in CHANGELOG.md, and the Sahm rule stays."]

    report = "\n".join(lines)
    (out / "candidate_report.txt").write_text(report)
    print("\n" + report)
    print(f"\nWritten to {out}/")


if __name__ == "__main__":
    main()
